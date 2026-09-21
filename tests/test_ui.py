from unittest.mock import patch

from ocigoat import ui


def test_confirm_assume_yes_skips_input():
    with patch("builtins.input") as fake_input:
        assert ui.confirm("proceed?", assume_yes=True) is True
    fake_input.assert_not_called()


def test_confirm_eof_returns_false():
    with patch("builtins.input", side_effect=EOFError):
        assert ui.confirm("proceed?") is False


def test_confirm_empty_reply_uses_default():
    with patch("builtins.input", return_value=""):
        assert ui.confirm("proceed?", default=True) is True
        assert ui.confirm("proceed?", default=False) is False


def test_confirm_parses_yes_no():
    with patch("builtins.input", return_value="y"):
        assert ui.confirm("proceed?") is True
    with patch("builtins.input", return_value="n"):
        assert ui.confirm("proceed?") is False
