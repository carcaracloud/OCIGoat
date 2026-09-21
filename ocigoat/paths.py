from pathlib import Path

_override_root = None


def set_repo_root(path):
    global _override_root
    _override_root = Path(path) if path is not None else None


def repo_root():
    if _override_root is not None:
        return _override_root
    return Path(__file__).resolve().parent.parent


def scenarios_dir():
    return repo_root() / "scenarios"


def instances_dir():
    return repo_root() / "instances"


def trash_dir():
    return instances_dir() / "trash"


def config_path():
    return repo_root() / "config.yml"


def plugin_cache_dir():
    return repo_root() / ".terraform-plugin-cache"
