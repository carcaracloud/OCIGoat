from ocigoat import instances, scenarios


def run(args):
    all_scenarios = scenarios.discover_scenarios()
    active = {}
    for record in instances.find_instances():
        active.setdefault(record.scenario_id, []).append(record.id)

    mode = args.mode or "all"

    rows = []
    for scenario_id in sorted(all_scenarios):
        deployed = scenario_id in active
        if mode == "deployed" and not deployed:
            continue
        if mode == "undeployed" and deployed:
            continue
        manifest = all_scenarios[scenario_id]
        status = ", ".join(active[scenario_id]) if deployed else "-"
        rows.append((scenario_id, manifest.difficulty or "-", status))

    if not rows:
        print("no scenarios match.")
        return 0

    id_width = max(len(r[0]) for r in rows)
    diff_width = max(len(r[1]) for r in rows)
    for scenario_id, difficulty, status in rows:
        print(f"{scenario_id:<{id_width}}  {difficulty:<{diff_width}}  {status}")
    return 0
