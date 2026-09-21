import subprocess
from unittest.mock import patch

import pytest

from ocigoat import terraform
from ocigoat.errors import TerraformError


def test_init_success(tmp_path):
    ok = subprocess.CompletedProcess(["terraform", "init"], 0)
    with patch("ocigoat.terraform.subprocess.run", return_value=ok) as run:
        terraform.init(tmp_path, tmp_path / "cache", {"FOO": "bar"})
    args, kwargs = run.call_args
    assert args[0] == ["terraform", "init", "-input=true"]
    assert kwargs["env"]["TF_PLUGIN_CACHE_DIR"] == str(tmp_path / "cache")
    assert kwargs["cwd"] == tmp_path


def test_apply_raises_on_nonzero_exit(tmp_path):
    failed = subprocess.CompletedProcess(["terraform", "apply"], 1)
    with patch("ocigoat.terraform.subprocess.run", return_value=failed):
        with pytest.raises(TerraformError) as exc_info:
            terraform.apply(tmp_path, tmp_path / "tfplan", {})
    assert exc_info.value.returncode == 1


def test_plan_includes_var_args_and_out_path(tmp_path):
    ok = subprocess.CompletedProcess(["terraform", "plan"], 0)
    with patch("ocigoat.terraform.subprocess.run", return_value=ok) as run:
        terraform.plan(tmp_path, ["-var=compartment_id=abc"], tmp_path / "tfplan", {})
    args, _ = run.call_args
    assert args[0] == [
        "terraform",
        "plan",
        "-input=true",
        f"-out={tmp_path / 'tfplan'}",
        "-var=compartment_id=abc",
    ]


def test_destroy_never_includes_undeclared_var_names(tmp_path):
    ok = subprocess.CompletedProcess(["terraform", "destroy"], 0)
    with patch("ocigoat.terraform.subprocess.run", return_value=ok) as run:
        terraform.destroy(tmp_path, ["-var=compartment_id=abc"], {})
    args, _ = run.call_args
    assert args[0] == ["terraform", "destroy", "-input=true", "-auto-approve", "-var=compartment_id=abc"]


def test_has_state_false_when_no_file(tmp_path):
    assert terraform.has_state(tmp_path) is False


def test_has_state_false_when_resources_empty(tmp_path):
    (tmp_path / "terraform.tfstate").write_text('{"resources": []}', encoding="utf-8")
    assert terraform.has_state(tmp_path) is False


def test_has_state_true_when_resources_present(tmp_path):
    (tmp_path / "terraform.tfstate").write_text('{"resources": [{"type": "oci_core_vcn"}]}', encoding="utf-8")
    assert terraform.has_state(tmp_path) is True


def test_output_json_parses_values(tmp_path):
    raw = subprocess.CompletedProcess(
        ["terraform", "output", "-json"],
        0,
        stdout='{"bucket_name": {"value": "my-bucket"}}',
        stderr="",
    )
    with patch("ocigoat.terraform.subprocess.run", return_value=raw):
        outputs = terraform.output_json(tmp_path, {})
    assert outputs == {"bucket_name": "my-bucket"}
