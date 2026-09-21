import pytest

from ocigoat.errors import ManifestError
from ocigoat.manifest import load_manifest
from ocigoat.scenarios import discover_scenarios

from .conftest import make_scenario


def test_loads_all_real_manifests(real_repo_root):
    scenarios = discover_scenarios()
    assert len(scenarios) == 16
    for scenario_id, manifest in scenarios.items():
        assert manifest.id == scenario_id
        assert manifest.name
        assert manifest.resources


def test_player_credential_defaults_false(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    manifest = load_manifest(scenario_dir / "manifest.yml")
    assert manifest.player_credential is False
    assert manifest.manual_cleanup_note is None


def test_player_credential_and_cleanup_note_when_present(repo_root_override):
    extra = "  player_credential: true\n\ncleanup:\n  manual_cleanup_note: >\n    do the thing first\n"
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-002", manifest_extra=extra)
    manifest = load_manifest(scenario_dir / "manifest.yml")
    assert manifest.player_credential is True
    assert "do the thing first" in manifest.manual_cleanup_note


def test_missing_required_field_raises(tmp_path):
    bad = tmp_path / "manifest.yml"
    bad.write_text("name: no id here\nresources: []\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(bad)
