import json
import os

from ocigoat import config as config_module
from ocigoat import credential, flags, instances, oci_profile, paths, progress, scenarios, terraform, tfvars, ui
from ocigoat.errors import OcigoatError

EXTRA_VARS_FILE = "extra_vars.json"


def _parse_extra_vars(pairs):
    extra = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise OcigoatError(f"--var expects KEY=VALUE, got '{pair}'")
        key, value = pair.split("=", 1)
        extra[key] = value
    return extra


def run(args):
    manifest = scenarios.get_scenario(args.scenario_id)
    cfg = config_module.load_config()

    scenario_terraform_dir = scenarios.scenario_terraform_dir(manifest)
    required = tfvars.discover_required_variables(scenario_terraform_dir)
    known_values = dict(cfg.known_values())
    extra_vars = _parse_extra_vars(args.var)
    # test_user_api_public_key and flag_content are filled in below, after the
    # instance dir exists (keypair generation, flag generation) — not yet here.
    will_be_known = set()
    if manifest.player_credential:
        will_be_known.add("test_user_api_public_key")
    if manifest.flag:
        will_be_known.add("flag_content")
    missing = sorted(
        name for name in required
        if name not in extra_vars and known_values.get(name) is None and name not in will_be_known
    )
    if missing:
        raise OcigoatError(
            f"missing required variable(s) for {manifest.id}: {', '.join(missing)}. "
            f"Pass each with --var KEY=VALUE (e.g. --var {missing[0]}=<value>)."
        )

    instance_dir = instances.create_instance_dir(manifest.id, scenario_terraform_dir)
    terraform_dir = instance_dir / "terraform"

    ui.info(f"instance: {instance_dir.name}")

    declared = tfvars.discover_declared_variables(terraform_dir)

    if manifest.player_credential:
        ui.info("generating test-operator API keypair")
        private_key, public_key = credential.generate_keypair(instance_dir)
        known_values["test_user_api_public_key"] = public_key.read_text(encoding="utf-8")

    if manifest.flag:
        flag_value = flags.generate_flag(manifest.id)
        known_values["flag_content"] = flag_value

    admin_config = oci_profile.resolve_admin_config_file(cfg.oci_cli_profile, instance_dir)
    env = dict(os.environ)
    env["OCI_CONFIG_FILE"] = str(admin_config)

    ui.info("terraform init")
    terraform.init(terraform_dir, paths.plugin_cache_dir(), env)

    (instance_dir / EXTRA_VARS_FILE).write_text(json.dumps(extra_vars), encoding="utf-8")
    var_args = tfvars.build_var_args(declared, known_values, extra_vars)

    plan_path = instance_dir / "tfplan"
    ui.info("terraform plan")
    terraform.plan(terraform_dir, var_args, plan_path, env)

    if args.plan_only:
        ui.info(f"plan only, stopping here. Instance kept at {instance_dir}")
        return 0

    if not ui.confirm("Apply this plan?", assume_yes=args.yes):
        ui.info(f"not applied. Instance kept at {instance_dir}; re-run 'ocigoat create {manifest.id}' or clean it up by hand.")
        return 1

    try:
        ui.info("terraform apply")
        terraform.apply(terraform_dir, plan_path, env)
    except OcigoatError:
        ui.error(
            f"apply failed. Instance left in place at {instance_dir} so its state isn't lost. "
            f"Run 'ocigoat destroy {instance_dir.name}' to tear down whatever was created, then try again."
        )
        raise

    outputs = terraform.output_json(terraform_dir, env)

    if manifest.player_credential:
        user_ocid = outputs.get("test_user_ocid")
        fingerprint = outputs.get("test_user_api_key_fingerprint")
        if user_ocid and fingerprint:
            credential.write_test_operator_config(
                instance_dir, cfg.tenancy_ocid, cfg.region, user_ocid, fingerprint, private_key
            )
            ui.info(f"test-operator OCI config: {instance_dir / 'oci_config'} (profile TEST_OPERATOR)")
        else:
            ui.warn(
                "manifest declares player_credential but terraform outputs don't include "
                "test_user_ocid / test_user_api_key_fingerprint; skipping profile write"
            )

    if manifest.flag:
        try:
            progress.record_flag_hash(manifest.id, flags.hash_flag(flag_value))
            ui.info(
                f"flag generated for {manifest.id}. Find it via the real exploit, "
                f"then run 'ocigoat submit {manifest.id} <flag>'."
            )
        except OSError as exc:
            ui.warn(f"could not update local progress store: {exc}")

    readme = scenarios.scenario_readme_path(manifest)
    instances.write_start_txt(instance_dir, outputs, readme)

    ui.info(f"done. Instance: {instance_dir}")
    ui.info(f"start here: {readme}")
    return 0
