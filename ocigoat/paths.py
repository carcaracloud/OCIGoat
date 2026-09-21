from pathlib import Path

_override_root = None
_override_home = None


def set_repo_root(path):
    global _override_root
    _override_root = Path(path) if path is not None else None


def repo_root():
    if _override_root is not None:
        return _override_root
    return Path(__file__).resolve().parent.parent


def set_home_dir(path):
    global _override_home
    _override_home = Path(path) if path is not None else None


def home_dir():
    if _override_home is not None:
        return _override_home
    return Path.home()


def ocigoat_home():
    return home_dir() / ".ocigoat"


def progress_path():
    return ocigoat_home() / "progress.json"


def certificates_dir():
    return ocigoat_home() / "certificates"


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
