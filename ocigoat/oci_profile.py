import configparser
from pathlib import Path

from ocigoat.errors import ConfigError

REAL_OCI_CONFIG = Path.home() / ".oci" / "config"


def _read_profile(profile_name, config_file=None):
    if config_file is None:
        config_file = REAL_OCI_CONFIG
    if not config_file.exists():
        raise ConfigError(f"no OCI config file found at {config_file}")

    parser = configparser.ConfigParser(interpolation=None, default_section="__ocigoat_unused__")
    parser.read(config_file)

    if not parser.has_section(profile_name):
        raise ConfigError(f"profile '{profile_name}' not found in {config_file}")
    items = dict(parser.items(profile_name))

    if not items:
        raise ConfigError(f"profile '{profile_name}' in {config_file} has no keys")
    return items


def resolve_admin_config_file(profile_name, instance_dir, out_name="admin_oci_config"):
    items = _read_profile(profile_name)
    out_path = instance_dir / out_name

    lines = ["[DEFAULT]"]
    for key, value in items.items():
        lines.append(f"{key}={value}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
