import json
import os

from ocigoat import config as config_module
from ocigoat import credential, instances, oci_profile, scenarios, terraform, tfvars, ui
from ocigoat.errors import OcigoatError
from ocigoat.commands.create_cmd import EXTRA_VARS_FILE, _parse_extra_vars


def _load_persisted_extra_vars(instance_dir):
    path = instance_dir / EXTRA_VARS_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _destroy_instance(record, cfg, assume_yes, cli_extra_vars=None):
    manifest = scenarios.get_scenario(record.scenario_id)
    terraform_dir = record.path / "terraform"

    if manifest.manual_cleanup_note:
        ui.info("")
        ui.info(f"manual cleanup required for {record.id}:")
        ui.info(manifest.manual_cleanup_note.strip())
        ui.info("")
        if not ui.confirm("Have you completed the manual cleanup above?", assume_yes=assume_yes):
            ui.error(f"skipping {record.id}: manual cleanup not confirmed")
            return False

    if not ui.confirm(f"Destroy {record.id}?", assume_yes=assume_yes):
        ui.info(f"skipping {record.id}")
        return False

    if not terraform.has_state(terraform_dir):
        ui.info(f"{record.id} has no terraform state; nothing to destroy")
        instances.move_to_trash(record.path)
        return True

    declared = tfvars.discover_declared_variables(terraform_dir)
    known_values = dict(cfg.known_values())

    public_key_path = record.path / credential.PUBLIC_KEY_NAME
    if manifest.player_credential and public_key_path.exists():
        known_values["test_user_api_public_key"] = public_key_path.read_text(encoding="utf-8")

    if manifest.flag:
        # destroy never recomputes resource content from this value, it only
        # needs something syntactically valid to satisfy the variable.
        known_values["flag_content"] = "unused-on-destroy"

    admin_config = oci_profile.resolve_admin_config_file(cfg.oci_cli_profile, record.path)
    env = dict(os.environ)
    env["OCI_CONFIG_FILE"] = str(admin_config)

    extra_vars = _load_persisted_extra_vars(record.path)
    extra_vars.update(cli_extra_vars or {})
    var_args = tfvars.build_var_args(declared, known_values, extra_vars)

    try:
        terraform.destroy(terraform_dir, var_args, env)
    except OcigoatError as exc:
        ui.error(f"destroy failed for {record.id}: {exc}")
        if manifest.manual_cleanup_note:
            ui.error("re-check the manual cleanup note above before retrying")
        ui.error(f"instance left in place at {record.path}")
        return False

    trash_path = instances.move_to_trash(record.path)
    ui.info(f"{record.id} destroyed, moved to {trash_path}")
    return True


def run(args):
    cfg = config_module.load_config()
    cli_extra_vars = _parse_extra_vars(getattr(args, "var", None))

    if args.all:
        records = instances.find_instances()
        if not records:
            ui.info("no active instances.")
            return 0
        succeeded = 0
        failed = 0
        for record in records:
            if _destroy_instance(record, cfg, args.yes, cli_extra_vars):
                succeeded += 1
            else:
                failed += 1
        ui.info(f"{succeeded} destroyed, {failed} failed or skipped")
        return 0 if failed == 0 else 1

    record = instances.find_instance(args.target)
    return 0 if _destroy_instance(record, cfg, args.yes, cli_extra_vars) else 1
