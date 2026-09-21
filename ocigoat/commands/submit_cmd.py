from ocigoat import flags, progress, scenarios, ui
from ocigoat.errors import OcigoatError


def run(args):
    manifest = scenarios.get_scenario(args.scenario_id)
    if not manifest.flag:
        raise OcigoatError(f"{manifest.id} has no flag to submit")

    data = progress.load_progress()
    entry = data.get(manifest.id)
    if entry is None:
        raise OcigoatError(f"no flag recorded for {manifest.id} yet. Run 'ocigoat create {manifest.id}' first.")

    if entry.get("submitted_at"):
        ui.info(f"{manifest.id} already marked complete ({entry['submitted_at']}).")
        return 0

    if not flags.verify_flag(args.flag, entry["flag_hash"]):
        ui.error("incorrect flag.")
        return 1

    progress.mark_submitted(manifest.id)
    ui.info(f"correct. {manifest.id} marked complete.")
    return 0
