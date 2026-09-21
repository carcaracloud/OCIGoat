import pytest

from ocigoat import instances
from ocigoat.errors import InstanceExistsError, InstanceNotFoundError

from .conftest import make_scenario


def test_create_instance_dir_copies_terraform(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    instance_dir = instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")
    assert instance_dir.name.startswith("SCN-FAKE-001_")
    assert (instance_dir / "terraform" / "main.tf").exists()


def test_create_instance_dir_refuses_second_active_instance(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")
    with pytest.raises(InstanceExistsError):
        instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")


def test_find_instances_excludes_trash(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    instance_dir = instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")
    instances.move_to_trash(instance_dir)
    assert instances.find_instances("SCN-FAKE-001") == []


def test_move_to_trash_handles_name_collision(repo_root_override):
    from ocigoat import paths

    colliding_dir = paths.instances_dir() / "SCN-FAKE-001_dupe"
    colliding_dir.mkdir(parents=True)
    already_in_trash = paths.trash_dir() / "SCN-FAKE-001_dupe"
    already_in_trash.mkdir(parents=True)

    moved = instances.move_to_trash(colliding_dir)
    assert moved.exists()
    assert moved != already_in_trash
    assert already_in_trash.exists()


def test_find_instance_by_exact_id(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    instance_dir = instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")
    record = instances.find_instance(instance_dir.name)
    assert record.path == instance_dir


def test_find_instance_by_scenario_id(repo_root_override):
    scenario_dir = make_scenario(repo_root_override, "SCN-FAKE-001")
    instance_dir = instances.create_instance_dir("SCN-FAKE-001", scenario_dir / "terraform")
    record = instances.find_instance("SCN-FAKE-001")
    assert record.path == instance_dir


def test_find_instance_missing_raises(repo_root_override):
    with pytest.raises(InstanceNotFoundError):
        instances.find_instance("SCN-DOES-NOT-EXIST")
