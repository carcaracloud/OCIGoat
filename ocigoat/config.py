from dataclasses import dataclass

import yaml

from ocigoat import paths
from ocigoat.errors import ConfigError

FIELDS = ("oci_cli_profile", "compartment_id", "tenancy_ocid", "region")


@dataclass
class Config:
    oci_cli_profile: str
    compartment_id: str
    tenancy_ocid: str
    region: str

    def known_values(self):
        return {
            "compartment_id": self.compartment_id,
            "tenancy_ocid": self.tenancy_ocid,
            "region": self.region,
        }


def load_config():
    path = paths.config_path()
    if not path.exists():
        raise ConfigError("no config.yml found. Run 'ocigoat config' first.")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [f for f in FIELDS if not raw.get(f)]
    if missing:
        raise ConfigError(
            f"config.yml is missing: {', '.join(missing)}. Run 'ocigoat config' again."
        )
    return Config(**{f: raw[f] for f in FIELDS})


def save_config(config):
    path = paths.config_path()
    data = {f: getattr(config, f) for f in FIELDS}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
