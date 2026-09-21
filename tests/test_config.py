import pytest

from ocigoat.config import Config, load_config, save_config
from ocigoat.errors import ConfigError


def test_load_config_missing_raises(repo_root_override):
    with pytest.raises(ConfigError):
        load_config()


def test_save_and_load_round_trip(repo_root_override):
    original = Config(
        oci_cli_profile="ADMIN",
        compartment_id="ocid1.compartment.oc1..abc",
        tenancy_ocid="ocid1.tenancy.oc1..xyz",
        region="sa-saopaulo-1",
    )
    save_config(original)
    loaded = load_config()
    assert loaded == original


def test_load_config_missing_field_raises(repo_root_override):
    from ocigoat import paths

    paths.config_path().write_text("oci_cli_profile: ADMIN\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config()
