from ocigoat import paths
from ocigoat.errors import ScenarioNotFoundError
from ocigoat.manifest import load_manifest


def discover_scenarios():
    scenarios = {}
    for manifest_path in sorted(paths.scenarios_dir().glob("*/manifest.yml")):
        manifest = load_manifest(manifest_path)
        dir_name = manifest_path.parent.name
        if manifest.id != dir_name:
            raise ScenarioNotFoundError(
                f"{manifest_path}: manifest id '{manifest.id}' does not match "
                f"directory name '{dir_name}'"
            )
        scenarios[manifest.id] = manifest
    return scenarios


def get_scenario(scenario_id):
    scenarios = discover_scenarios()
    if scenario_id not in scenarios:
        valid = ", ".join(sorted(scenarios))
        raise ScenarioNotFoundError(
            f"unknown scenario '{scenario_id}'. Valid scenarios: {valid}"
        )
    return scenarios[scenario_id]


def scenario_terraform_dir(manifest):
    return manifest.path.parent / "terraform"


def scenario_readme_path(manifest):
    return manifest.path.parent / "README.md"
