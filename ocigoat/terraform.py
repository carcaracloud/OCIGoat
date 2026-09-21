import json
import subprocess

from ocigoat.errors import TerraformError


def _run_interactive(args, cwd, env):
    result = subprocess.run(args, cwd=cwd, env=env)
    if result.returncode != 0:
        raise TerraformError(f"'{' '.join(args)}' exited with {result.returncode}", result.returncode)
    return result.returncode


def init(terraform_dir, plugin_cache_dir, env):
    run_env = dict(env)
    run_env["TF_PLUGIN_CACHE_DIR"] = str(plugin_cache_dir)
    return _run_interactive(["terraform", "init", "-input=true"], terraform_dir, run_env)


def plan(terraform_dir, var_args, out_path, env):
    args = ["terraform", "plan", "-input=true", f"-out={out_path}"] + list(var_args)
    return _run_interactive(args, terraform_dir, env)


def apply(terraform_dir, plan_path, env):
    return _run_interactive(["terraform", "apply", "-input=true", str(plan_path)], terraform_dir, env)


def destroy(terraform_dir, var_args, env):
    args = ["terraform", "destroy", "-input=true", "-auto-approve"] + list(var_args)
    return _run_interactive(args, terraform_dir, env)


def has_state(terraform_dir):
    state_file = terraform_dir / "terraform.tfstate"
    if not state_file.exists():
        return False
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return bool(data.get("resources"))


def output_json(terraform_dir, env):
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=terraform_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise TerraformError(f"terraform output failed: {result.stderr.strip()}", result.returncode)
    parsed = json.loads(result.stdout)
    return {key: value.get("value") for key, value in parsed.items()}
