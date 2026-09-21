import pytest

from ocigoat import paths

MINIMAL_MANIFEST = """\
id: {scenario_id}
name: Fake scenario
version: 1.0.0
resources:
  - core_vcn
requirements:
  terraform: ">=1.5.0"
  oci_provider: "9.2.0"
"""

MINIMAL_MAIN_TF = """\
variable "compartment_id" {{
  type = string
}}
"""


@pytest.fixture
def fake_repo(tmp_path):
    (tmp_path / "scenarios").mkdir()
    yield tmp_path


def make_scenario(repo_root, scenario_id, manifest_extra="", main_tf=MINIMAL_MAIN_TF):
    scenario_dir = repo_root / "scenarios" / scenario_id
    (scenario_dir / "terraform").mkdir(parents=True)
    manifest_text = MINIMAL_MANIFEST.format(scenario_id=scenario_id) + manifest_extra
    (scenario_dir / "manifest.yml").write_text(manifest_text, encoding="utf-8")
    (scenario_dir / "terraform" / "main.tf").write_text(main_tf, encoding="utf-8")
    (scenario_dir / "README.md").write_text("fake readme\n", encoding="utf-8")
    return scenario_dir


@pytest.fixture
def repo_root_override(fake_repo):
    paths.set_repo_root(fake_repo)
    yield fake_repo
    paths.set_repo_root(None)


@pytest.fixture
def real_repo_root():
    paths.set_repo_root(None)
    return paths.repo_root()
