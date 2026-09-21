from unittest.mock import patch

from ocigoat.commands import destroy_cmd
from ocigoat.config import Config
from ocigoat.errors import TerraformError
from ocigoat.instances import InstanceRecord
from ocigoat.manifest import Manifest

from .conftest import make_scenario


def _cfg():
    return Config(
        oci_cli_profile="DEFAULT",
        compartment_id="ocid1.compartment.oc1..abc",
        tenancy_ocid="ocid1.tenancy.oc1..xyz",
        region="sa-saopaulo-1",
    )


def _record(repo_root, scenario_id):
    scenario_dir = make_scenario(repo_root, scenario_id)
    instance_dir = repo_root / "instances" / f"{scenario_id}_deadbeef"
    (instance_dir / "terraform").mkdir(parents=True)
    (instance_dir / "terraform" / "main.tf").write_text("", encoding="utf-8")
    return InstanceRecord(id=instance_dir.name, scenario_id=scenario_id, path=instance_dir), scenario_dir


def test_manual_cleanup_note_decline_skips_destroy(repo_root_override, monkeypatch, capsys):
    record, scenario_dir = _record(repo_root_override, "SCN-FAKE-CLEANUP")
    manifest = Manifest(
        id="SCN-FAKE-CLEANUP", name="x", version="1", resources=["core_vcn"],
        cleanup={"manual_cleanup_note": "abort the thing first"},
    )
    monkeypatch.setattr(destroy_cmd.scenarios, "get_scenario", lambda sid: manifest)
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    with patch("ocigoat.commands.destroy_cmd.terraform.destroy") as destroy_call:
        result = destroy_cmd._destroy_instance(record, _cfg(), assume_yes=False)

    assert result is False
    destroy_call.assert_not_called()
    assert record.path.exists()
    assert "abort the thing first" in capsys.readouterr().out


def test_destroy_failure_leaves_instance_in_place(repo_root_override, monkeypatch):
    record, scenario_dir = _record(repo_root_override, "SCN-FAKE-FAIL")
    (record.path / "terraform" / "terraform.tfstate").write_text(
        '{"resources": [{"type": "oci_core_vcn"}]}', encoding="utf-8"
    )
    manifest = Manifest(id="SCN-FAKE-FAIL", name="x", version="1", resources=["core_vcn"])
    monkeypatch.setattr(destroy_cmd.scenarios, "get_scenario", lambda sid: manifest)
    monkeypatch.setattr(destroy_cmd.oci_profile, "resolve_admin_config_file", lambda *a, **k: record.path / "admin_oci_config")

    with patch("ocigoat.commands.destroy_cmd.terraform.destroy", side_effect=TerraformError("boom", 1)):
        result = destroy_cmd._destroy_instance(record, _cfg(), assume_yes=True)

    assert result is False
    assert record.path.exists()
    assert not (repo_root_override / "instances" / "trash" / record.id).exists()


def test_destroy_success_moves_to_trash(repo_root_override, monkeypatch):
    record, scenario_dir = _record(repo_root_override, "SCN-FAKE-OK")
    (record.path / "terraform" / "terraform.tfstate").write_text(
        '{"resources": [{"type": "oci_core_vcn"}]}', encoding="utf-8"
    )
    manifest = Manifest(id="SCN-FAKE-OK", name="x", version="1", resources=["core_vcn"])
    monkeypatch.setattr(destroy_cmd.scenarios, "get_scenario", lambda sid: manifest)
    monkeypatch.setattr(destroy_cmd.oci_profile, "resolve_admin_config_file", lambda *a, **k: record.path / "admin_oci_config")

    with patch("ocigoat.commands.destroy_cmd.terraform.destroy", return_value=0):
        result = destroy_cmd._destroy_instance(record, _cfg(), assume_yes=True)

    assert result is True
    assert not record.path.exists()
    assert (repo_root_override / "instances" / "trash" / record.id).exists()


def test_extra_vars_persisted_at_create_are_used_at_destroy(repo_root_override, monkeypatch):
    record, scenario_dir = _record(repo_root_override, "SCN-FAKE-VARS")
    (record.path / "terraform" / "main.tf").write_text('variable "foo" {\n  type = string\n}\n', encoding="utf-8")
    (record.path / "extra_vars.json").write_text('{"foo": "bar"}', encoding="utf-8")
    manifest = Manifest(id="SCN-FAKE-VARS", name="x", version="1", resources=["core_vcn"])
    monkeypatch.setattr(destroy_cmd.scenarios, "get_scenario", lambda sid: manifest)
    monkeypatch.setattr(destroy_cmd.oci_profile, "resolve_admin_config_file", lambda *a, **k: record.path / "admin_oci_config")
    (record.path / "terraform" / "terraform.tfstate").write_text(
        '{"resources": [{"type": "oci_core_vcn"}]}', encoding="utf-8"
    )

    with patch("ocigoat.commands.destroy_cmd.terraform.destroy") as destroy_call:
        destroy_cmd._destroy_instance(record, _cfg(), assume_yes=True)

    args, _kwargs = destroy_call.call_args
    assert "-var=foo=bar" in args[1]
