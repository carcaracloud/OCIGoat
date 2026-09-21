from unittest.mock import patch

import pytest

from ocigoat.cli import main
from ocigoat.errors import ScenarioNotFoundError


def test_create_dispatches_to_create_cmd():
    with patch("ocigoat.commands.create_cmd.run", return_value=0) as run:
        code = main(["create", "SCN-NET-001", "--yes"])
    assert code == 0
    args = run.call_args[0][0]
    assert args.scenario_id == "SCN-NET-001"
    assert args.yes is True


def test_destroy_requires_target_or_all(capsys):
    with pytest.raises(SystemExit):
        main(["destroy"])


def test_destroy_rejects_target_and_all_together(capsys):
    with pytest.raises(SystemExit):
        main(["destroy", "SCN-NET-001", "--all"])


def test_destroy_dispatches_with_target():
    with patch("ocigoat.commands.destroy_cmd.run", return_value=0) as run:
        code = main(["destroy", "SCN-NET-001"])
    assert code == 0
    args = run.call_args[0][0]
    assert args.target == "SCN-NET-001"
    assert args.all is False


def test_list_dispatches_to_list_cmd():
    with patch("ocigoat.commands.list_cmd.run", return_value=0) as run:
        code = main(["list", "--deployed"])
    assert code == 0
    args = run.call_args[0][0]
    assert args.mode == "deployed"


def test_config_dispatches_to_config_cmd():
    with patch("ocigoat.commands.config_cmd.run", return_value=0) as run:
        code = main(["config", "--region", "sa-saopaulo-1"])
    assert code == 0
    args = run.call_args[0][0]
    assert args.region == "sa-saopaulo-1"


def test_ocigoat_error_from_command_is_caught_and_returns_1():
    with patch("ocigoat.commands.create_cmd.run", side_effect=ScenarioNotFoundError("nope")):
        code = main(["create", "SCN-DOES-NOT-EXIST"])
    assert code == 1
