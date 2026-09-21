from types import SimpleNamespace

import pytest

pytest.importorskip("fpdf")

from ocigoat import flags, progress
from ocigoat.commands import certificate_cmd
from ocigoat.errors import OcigoatError

from .conftest import make_scenario

FLAG_EXTRA = "  flag: true\n"


def _capture(scenario_id):
    flag = flags.generate_flag(scenario_id)
    progress.record_flag_hash(scenario_id, flags.hash_flag(flag))
    progress.mark_submitted(scenario_id)


def test_certificate_rejects_when_none_flaggable(repo_root_override, home_dir_override):
    make_scenario(repo_root_override, "SCN-FAKE-NOFLAG")

    with pytest.raises(OcigoatError, match="no flaggable scenarios"):
        certificate_cmd.run(SimpleNamespace(name="Test Player", out=None))


def test_certificate_rejects_when_captures_missing(repo_root_override, home_dir_override):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)

    with pytest.raises(OcigoatError, match="SCN-FAKE-001"):
        certificate_cmd.run(SimpleNamespace(name="Test Player", out=None))


def test_certificate_writes_pdf_once_all_captured(repo_root_override, home_dir_override, tmp_path):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    _capture("SCN-FAKE-001")
    out_path = tmp_path / "cert.pdf"

    code = certificate_cmd.run(SimpleNamespace(name="Test Player", out=out_path))

    assert code == 0
    assert out_path.read_bytes()[:5] == b"%PDF-"


def test_certificate_rejects_non_latin1_name_cleanly(repo_root_override, home_dir_override, tmp_path):
    make_scenario(repo_root_override, "SCN-FAKE-001", manifest_extra=FLAG_EXTRA)
    _capture("SCN-FAKE-001")
    out_path = tmp_path / "cert.pdf"

    with pytest.raises(OcigoatError, match="Latin-1"):
        certificate_cmd.run(SimpleNamespace(name="测试", out=out_path))
