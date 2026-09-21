from ocigoat import progress, scenarios


def run(args):
    flaggable = {sid: m for sid, m in scenarios.discover_scenarios().items() if m.flag}
    if not flaggable:
        print("no flaggable scenarios found.")
        return 0

    data = progress.load_progress()
    completed = 0
    for sid in sorted(flaggable):
        entry = data.get(sid)
        if entry and entry.get("submitted_at"):
            print(f"[x] {sid:<20} captured {entry['submitted_at']}")
            completed += 1
        elif entry:
            print(f"[ ] {sid:<20} deployed, not yet captured")
        else:
            print(f"[ ] {sid:<20} not started")

    print(f"\n{completed}/{len(flaggable)} flags captured")
    return 0
