import sys


def info(message):
    print(message)


def warn(message):
    print(f"warning: {message}", file=sys.stderr)


def error(message):
    print(f"error: {message}", file=sys.stderr)


def confirm(prompt, assume_yes=False, default=False):
    if assume_yes:
        return True
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        reply = input(f"{prompt} {suffix} ").strip().lower()
    except EOFError:
        return False
    if not reply:
        return default
    return reply in ("y", "yes")
