from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ocigoat.commands import create_cmd
from ocigoat.config import Config
from ocigoat.errors import OcigoatError, TerraformError
from ocigoat.manifest import Manifest

from .conftest import make_scenario

FLAG_EXTRA = "  flag: true\n"

MAIN_TF_WITH_REQUIRED_EMAIL = """\
variable "compartment_id" {
  type = string
}

variable "test_user_email" {
  type = string
}
"""


def _args(scenario_id, plan_only=False, yes=True, var=None):
    return SimpleNamespace(scenario_id=scenario_id, plan_only=plan_only, yes=yes, var=var)


def _cfg():
    return Config(
        oci_cli_profile="DEFAULT",
        compartment_id="ocid1.compartment.oc1..abc",
        tenancy_ocid="ocid1.tenancy.oc1..xyz",
        region="sa-saopaulo-1",
    )


def _patch_common(monkeypatch):
    monkeypatch.setattr(create_cmd.config_module, "load_config", lambda: _cfg())
    monkeypatch.setattr(create_cmd.oci_profile, "resolve_admin_config_file", lambda *a, **k: "fake-admin-config")
    monkeypatch.setattr(create_cmd.terraform, "init", lambda *a, **k: 0)
    monkeypatch.setattr(create_cmd.terraform, "plan", lambda *a, **k: 0)
    monkeypatch.setattr(create_cmd.terraform, "output_json", lambda *a, **k: {})


def test_flag_not_recorded_when_apply_fails(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    _patch_common(monkeypatch)
    monkeypatch.setattr(create_cmd.terraform, "apply", lambda *a, **k: (_ for _ in ()).throw(TerraformError("boom", 1)))

    with pytest.raises(TerraformError):
        create_cmd.run(_args("SCN-FAKE-001"))

    from ocigoat import progress

    assert progress.load_progress() == {}


def test_flag_not_recorded_on_plan_only(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    _patch_common(monkeypatch)
    with patch.object(create_cmd.terraform, "apply") as apply_mock:
        code = create_cmd.run(_args("SCN-FAKE-001", plan_only=True))

    apply_mock.assert_not_called()
    assert code == 0

    from ocigoat import progress

    assert progress.load_progress() == {}


def test_flag_recorded_after_successful_apply(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    _patch_common(monkeypatch)
    monkeypatch.setattr(create_cmd.terraform, "apply", lambda *a, **k: 0)

    code = create_cmd.run(_args("SCN-FAKE-001"))

    assert code == 0
    from ocigoat import progress

    data = progress.load_progress()
    assert "SCN-FAKE-001" in data
    assert data["SCN-FAKE-001"]["submitted_at"] is None
    assert data["SCN-FAKE-001"]["flag_hash"].startswith("sha256:")


def test_missing_required_variable_raises_before_touching_terraform(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-003", main_tf=MAIN_TF_WITH_REQUIRED_EMAIL)
    _patch_common(monkeypatch)
    with patch.object(create_cmd.terraform, "init") as init_mock, \
         patch.object(create_cmd.terraform, "plan") as plan_mock:
        with pytest.raises(OcigoatError, match="test_user_email"):
            create_cmd.run(_args("SCN-FAKE-003"))

    init_mock.assert_not_called()
    plan_mock.assert_not_called()

    from ocigoat import instances

    assert instances.find_instances() == []


def test_missing_required_variable_satisfied_by_cli_var(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-003", main_tf=MAIN_TF_WITH_REQUIRED_EMAIL)
    _patch_common(monkeypatch)
    monkeypatch.setattr(create_cmd.terraform, "apply", lambda *a, **k: 0)

    code = create_cmd.run(_args("SCN-FAKE-003", var=["test_user_email=player@example.com"]))

    assert code == 0


def test_no_flag_handling_for_scenario_without_flag(repo_root_override, home_dir_override, monkeypatch):
    make_scenario(repo_root_override, "SCN-FAKE-002")
    _patch_common(monkeypatch)
    monkeypatch.setattr(create_cmd.terraform, "apply", lambda *a, **k: 0)

    code = create_cmd.run(_args("SCN-FAKE-002"))

    assert code == 0
    from ocigoat import progress

    assert progress.load_progress() == {}
