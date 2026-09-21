from ocigoat import config as config_module
from ocigoat import ui
from ocigoat.errors import ConfigError


def _prompt(label, current):
    suffix = f" [{current}]" if current else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or current


def run(args):
    try:
        existing = config_module.load_config()
    except ConfigError:
        existing = config_module.Config(
            oci_cli_profile="DEFAULT", compartment_id="", tenancy_ocid="", region=""
        )

    profile = args.profile or _prompt("OCI CLI profile to use as admin", existing.oci_cli_profile)
    compartment_id = args.compartment_id or _prompt("Compartment OCID", existing.compartment_id)
    tenancy_ocid = args.tenancy_ocid or _prompt("Tenancy OCID", existing.tenancy_ocid)
    region = args.region or _prompt("Region", existing.region)

    if not (compartment_id and tenancy_ocid and region):
        ui.error("compartment_id, tenancy_ocid, and region are all required.")
        return 1

    new_config = config_module.Config(
        oci_cli_profile=profile,
        compartment_id=compartment_id,
        tenancy_ocid=tenancy_ocid,
        region=region,
    )
    config_module.save_config(new_config)
    ui.info("config.yml written.")
    return 0
