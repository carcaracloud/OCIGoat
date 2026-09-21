import pytest

from ocigoat import oci_profile
from ocigoat.errors import ConfigError

FAKE_OCI_CONFIG = """\
[DEFAULT]
user=ocid1.user.oc1..default
fingerprint=11:11:11
tenancy=ocid1.tenancy.oc1..xyz
region=sa-saopaulo-1
key_file=/home/player/.oci/oci_api_key.pem

[SECOND]
user=ocid1.user.oc1..second
fingerprint=22:22:22
tenancy=ocid1.tenancy.oc1..xyz
region=sa-saopaulo-1
key_file=/home/player/.oci/second.pem
"""


@pytest.fixture
def fake_oci_config(tmp_path, monkeypatch):
    config_file = tmp_path / "oci_config_source"
    config_file.write_text(FAKE_OCI_CONFIG, encoding="utf-8")
    monkeypatch.setattr(oci_profile, "REAL_OCI_CONFIG", config_file)
    return config_file


def test_resolve_named_profile(tmp_path, fake_oci_config):
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    out_path = oci_profile.resolve_admin_config_file("SECOND", instance_dir)
    content = out_path.read_text()
    assert content.splitlines()[0] == "[DEFAULT]"
    assert "user=ocid1.user.oc1..second" in content
    assert "key_file=/home/player/.oci/second.pem" in content


def test_resolve_default_profile(tmp_path, fake_oci_config):
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    out_path = oci_profile.resolve_admin_config_file("DEFAULT", instance_dir)
    content = out_path.read_text()
    assert "user=ocid1.user.oc1..default" in content


def test_unknown_profile_raises(tmp_path, fake_oci_config):
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    with pytest.raises(ConfigError):
        oci_profile.resolve_admin_config_file("NOPE", instance_dir)


def test_missing_config_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(oci_profile, "REAL_OCI_CONFIG", tmp_path / "does_not_exist")
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    with pytest.raises(ConfigError):
        oci_profile.resolve_admin_config_file("DEFAULT", instance_dir)
