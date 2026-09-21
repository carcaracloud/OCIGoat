from types import SimpleNamespace

from ocigoat import flags, progress
from ocigoat.commands import progress_cmd

from .conftest import make_scenario

FLAG_EXTRA = "  flag: true\n"


def test_progress_reports_not_started(repo_root_override, home_dir_override, capsys):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)

    code = progress_cmd.run(SimpleNamespace())

    out = capsys.readouterr().out
    assert code == 0
    assert "SCN-FAKE-001" in out
    assert "not started" in out
    assert "0/1 flags captured" in out


def test_progress_reports_deployed_not_captured(repo_root_override, home_dir_override, capsys):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    progress.record_flag_hash("SCN-FAKE-001", "sha256:abc")

    code = progress_cmd.run(SimpleNamespace())

    out = capsys.readouterr().out
    assert code == 0
    assert "deployed, not yet captured" in out


def test_progress_reports_captured(repo_root_override, home_dir_override, capsys):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    flag = flags.generate_flag("SCN-FAKE-001")
    progress.record_flag_hash("SCN-FAKE-001", flags.hash_flag(flag))
    progress.mark_submitted("SCN-FAKE-001")

    code = progress_cmd.run(SimpleNamespace())

    out = capsys.readouterr().out
    assert code == 0
    assert "captured" in out
    assert "1/1 flags captured" in out


def test_progress_ignores_non_flaggable_scenarios(repo_root_override, home_dir_override, capsys):
    make_scenario(repo_root_override, "SCN-FAKE-NOFLAG")

    code = progress_cmd.run(SimpleNamespace())

    out = capsys.readouterr().out
    assert code == 0
    assert "no flaggable scenarios found" in out
