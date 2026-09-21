import json
import secrets
import shutil
import time
from dataclasses import dataclass

from ocigoat import paths
from ocigoat.errors import InstanceExistsError, InstanceNotFoundError


@dataclass
class InstanceRecord:
    id: str
    scenario_id: str
    path: object


def new_instance_id(scenario_id):
    return f"{scenario_id}_{secrets.token_hex(4)}"


def _scenario_id_from_instance_id(instance_id):
    return instance_id.rsplit("_", 1)[0]


def find_instances(scenario_id=None):
    root = paths.instances_dir()
    if not root.exists():
        return []

    records = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name == "trash":
            continue
        entry_scenario_id = _scenario_id_from_instance_id(entry.name)
        if scenario_id is not None and entry_scenario_id != scenario_id:
            continue
        records.append(InstanceRecord(id=entry.name, scenario_id=entry_scenario_id, path=entry))
    return records


def create_instance_dir(scenario_id, scenario_terraform_dir):
    existing = find_instances(scenario_id)
    if existing:
        raise InstanceExistsError(
            f"scenario '{scenario_id}' already has an active instance: {existing[0].id}. "
            f"Run 'ocigoat destroy {scenario_id}' first."
        )

    instance_id = new_instance_id(scenario_id)
    instance_dir = paths.instances_dir() / instance_id
    instance_dir.mkdir(parents=True)
    shutil.copytree(scenario_terraform_dir, instance_dir / "terraform")
    return instance_dir


def find_instance(target):
    root = paths.instances_dir()
    direct = root / target
    if direct.exists() and direct.is_dir():
        return InstanceRecord(id=target, scenario_id=_scenario_id_from_instance_id(target), path=direct)

    matches = find_instances(target)
    if not matches:
        raise InstanceNotFoundError(f"no active instance found for '{target}'")
    if len(matches) > 1:
        ids = ", ".join(m.id for m in matches)
        raise InstanceNotFoundError(f"multiple instances match '{target}': {ids}. Name one exactly.")
    return matches[0]


def move_to_trash(instance_dir):
    trash = paths.trash_dir()
    trash.mkdir(parents=True, exist_ok=True)
    target = trash / instance_dir.name
    if target.exists():
        target = trash / f"{instance_dir.name}_{int(time.time())}"
    shutil.move(str(instance_dir), str(target))
    return target


def write_start_txt(instance_dir, outputs, readme_path):
    lines = ["OCIGoat instance outputs", "=" * 25, ""]
    lines.append(json.dumps(outputs, indent=2))
    lines.append("")
    lines.append(f"Scenario README (start here): {readme_path}")
    (instance_dir / "start.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
