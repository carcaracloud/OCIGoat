import argparse
import sys
from pathlib import Path

from ocigoat import ui
from ocigoat.commands import certificate_cmd, config_cmd, create_cmd, destroy_cmd, list_cmd, progress_cmd, submit_cmd
from ocigoat.errors import OcigoatError


def build_parser():
    parser = argparse.ArgumentParser(prog="ocigoat", description="Deploy and tear down OCIGoat scenarios")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config", help="set up compartment, tenancy, region, and admin profile")
    config_parser.add_argument("--profile", help="OCI CLI profile name to use as admin")
    config_parser.add_argument("--compartment-id", dest="compartment_id")
    config_parser.add_argument("--tenancy-ocid", dest="tenancy_ocid")
    config_parser.add_argument("--region")
    config_parser.set_defaults(func=config_cmd.run)

    list_parser = subparsers.add_parser("list", help="list scenarios and their deployment status")
    mode_group = list_parser.add_mutually_exclusive_group()
    mode_group.add_argument("--deployed", action="store_const", dest="mode", const="deployed")
    mode_group.add_argument("--undeployed", action="store_const", dest="mode", const="undeployed")
    mode_group.add_argument("--all", action="store_const", dest="mode", const="all")
    list_parser.set_defaults(func=list_cmd.run, mode=None)

    create_parser = subparsers.add_parser("create", help="deploy a scenario")
    create_parser.add_argument("scenario_id")
    create_parser.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompts")
    create_parser.add_argument("--plan-only", action="store_true", help="run terraform plan and stop")
    create_parser.add_argument("--var", action="append", help="extra -var KEY=VALUE, repeatable")
    create_parser.set_defaults(func=create_cmd.run)

    destroy_parser = subparsers.add_parser("destroy", help="tear down a deployed scenario")
    destroy_parser.add_argument("target", nargs="?", help="scenario ID or instance ID")
    destroy_parser.add_argument("--all", action="store_true", help="destroy every active instance")
    destroy_parser.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompts")
    destroy_parser.add_argument("--var", action="append", help="override a persisted -var KEY=VALUE, repeatable")
    destroy_parser.set_defaults(func=destroy_cmd.run)

    submit_parser = subparsers.add_parser("submit", help="submit a captured flag for a scenario")
    submit_parser.add_argument("scenario_id")
    submit_parser.add_argument("flag")
    submit_parser.set_defaults(func=submit_cmd.run)

    progress_parser = subparsers.add_parser("progress", help="show flag-capture progress")
    progress_parser.set_defaults(func=progress_cmd.run)

    certificate_parser = subparsers.add_parser("certificate", help="generate a local certificate of completion")
    certificate_parser.add_argument("--name", required=True, help="name to print on the certificate")
    certificate_parser.add_argument("--out", type=Path, default=None, help="output PDF path")
    certificate_parser.set_defaults(func=certificate_cmd.run)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "destroy":
        if not args.all and not args.target:
            parser.error("destroy requires a target (scenario/instance ID) or --all")
        if args.all and args.target:
            parser.error("pass either a target or --all, not both")

    try:
        return args.func(args)
    except OcigoatError as exc:
        ui.error(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
