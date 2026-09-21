from dataclasses import dataclass, field

import yaml

from ocigoat.errors import ManifestError

REQUIRED_FIELDS = ("id", "name", "resources")


@dataclass
class Manifest:
    id: str
    name: str
    version: str
    category: list = field(default_factory=list)
    difficulty: str = ""
    resources: list = field(default_factory=list)
    requirements: dict = field(default_factory=dict)
    cost: dict = field(default_factory=dict)
    cleanup: dict = field(default_factory=dict)
    path: object = None

    @property
    def player_credential(self):
        return bool(self.requirements.get("player_credential", False))

    @property
    def flag(self):
        return bool(self.requirements.get("flag", False))

    @property
    def manual_cleanup_note(self):
        return self.cleanup.get("manual_cleanup_note")


def load_manifest(path):
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path}: invalid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ManifestError(f"{path}: manifest did not parse to a mapping")

    missing = [f for f in REQUIRED_FIELDS if f not in raw]
    if missing:
        raise ManifestError(f"{path}: missing required field(s): {', '.join(missing)}")

    return Manifest(
        id=raw["id"],
        name=raw["name"],
        version=raw.get("version", ""),
        category=raw.get("category", []),
        difficulty=raw.get("difficulty", ""),
        resources=raw.get("resources", []),
        requirements=raw.get("requirements", {}) or {},
        cost=raw.get("cost", {}) or {},
        cleanup=raw.get("cleanup", {}) or {},
        path=path,
    )
