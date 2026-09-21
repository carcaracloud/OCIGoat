import json
import os
from datetime import datetime, timezone

from ocigoat import paths


def load_progress():
    path = paths.progress_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_progress(data):
    home = paths.ocigoat_home()
    home.mkdir(parents=True, exist_ok=True)
    tmp_path = home / "progress.json.tmp"
    tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp_path, paths.progress_path())


def record_flag_hash(scenario_id, flag_hash):
    data = load_progress()
    existing = data.get(scenario_id)
    if existing and existing.get("submitted_at"):
        return data
    data[scenario_id] = {"flag_hash": flag_hash, "submitted_at": None}
    save_progress(data)
    return data


def mark_submitted(scenario_id):
    data = load_progress()
    data[scenario_id]["submitted_at"] = datetime.now(timezone.utc).isoformat()
    save_progress(data)
    return data
