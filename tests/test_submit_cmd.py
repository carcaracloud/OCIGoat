from types import SimpleNamespace

import pytest

from ocigoat import progress
from ocigoat.commands import submit_cmd
from ocigoat.errors import OcigoatError
from ocigoat.manifest import Manifest


def _args(scenario_id, flag):
    return SimpleNamespace(scenario_id=scenario_id, flag=flag)


def test_submit_rejects_scenario_without_flag(home_dir_override, monkeypatch):
    manifest = Manifest(id="SCN-FAKE", name="x", version="1", resources=["core_vcn"])
    monkeypatch.setattr(submit_cmd.scenarios, "get_scenario", lambda sid: manifest)

    with pytest.raises(OcigoatError):
        submit_cmd.run(_args("SCN-FAKE", "whatever"))


def test_submit_rejects_when_never_deployed(home_dir_override, monkeypatch):
    manifest = Manifest(
        id="SCN-FAKE", name="x", version="1", resources=["core_vcn"], requirements={"flag": True}
    )
    monkeypatch.setattr(submit_cmd.scenarios, "get_scenario", lambda sid: manifest)

    with pytest.raises(OcigoatError):
        submit_cmd.run(_args("SCN-FAKE", "whatever"))


def test_submit_correct_flag_marks_complete(home_dir_override, monkeypatch):
    manifest = Manifest(
        id="SCN-FAKE", name="x", version="1", resources=["core_vcn"], requirements={"flag": True}
    )
    monkeypatch.setattr(submit_cmd.scenarios, "get_scenario", lambda sid: manifest)

    from ocigoat import flags

    flag = flags.generate_flag("SCN-FAKE")
    progress.record_flag_hash("SCN-FAKE", flags.hash_flag(flag))

    code = submit_cmd.run(_args("SCN-FAKE", flag))

    assert code == 0
    assert progress.load_progress()["SCN-FAKE"]["submitted_at"] is not None


def test_submit_wrong_flag_does_not_mark_complete(home_dir_override, monkeypatch):
    manifest = Manifest(
        id="SCN-FAKE", name="x", version="1", resources=["core_vcn"], requirements={"flag": True}
    )
    monkeypatch.setattr(submit_cmd.scenarios, "get_scenario", lambda sid: manifest)

    from ocigoat import flags

    flag = flags.generate_flag("SCN-FAKE")
    progress.record_flag_hash("SCN-FAKE", flags.hash_flag(flag))

    code = submit_cmd.run(_args("SCN-FAKE", "OCIGOAT{scn-fake-wrong}"))

    assert code == 1
    assert progress.load_progress()["SCN-FAKE"]["submitted_at"] is None


def test_submit_already_complete_is_idempotent(home_dir_override, monkeypatch):
    manifest = Manifest(
        id="SCN-FAKE", name="x", version="1", resources=["core_vcn"], requirements={"flag": True}
    )
    monkeypatch.setattr(submit_cmd.scenarios, "get_scenario", lambda sid: manifest)

    from ocigoat import flags

    flag = flags.generate_flag("SCN-FAKE")
    progress.record_flag_hash("SCN-FAKE", flags.hash_flag(flag))
    submit_cmd.run(_args("SCN-FAKE", flag))
    first_timestamp = progress.load_progress()["SCN-FAKE"]["submitted_at"]

    code = submit_cmd.run(_args("SCN-FAKE", flag))

    assert code == 0
    assert progress.load_progress()["SCN-FAKE"]["submitted_at"] == first_timestamp
