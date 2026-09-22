import re

VARIABLE_BLOCK_START_RE = re.compile(r'variable\s+"([A-Za-z0-9_]+)"\s*\{')
DEFAULT_KEY_RE = re.compile(r'^\s*default\s*=', re.MULTILINE)

KNOWN_AUTOFILL_VARS = {"compartment_id", "tenancy_ocid", "region", "test_user_api_public_key", "flag_content"}


def _variable_blocks(text):
    """Yield (name, body) for each `variable "name" { ... }` block, brace-depth aware
    so nested blocks (e.g. `validation { ... }`) don't truncate the body early."""
    for match in VARIABLE_BLOCK_START_RE.finditer(text):
        name = match.group(1)
        depth = 1
        i = match.end()
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        yield name, text[match.end() : i - 1]


def discover_declared_variables(terraform_dir):
    declared = set()
    for tf_file in sorted(terraform_dir.glob("*.tf")):
        text = tf_file.read_text(encoding="utf-8")
        declared.update(name for name, _body in _variable_blocks(text))
    return declared


def discover_required_variables(terraform_dir):
    """Declared variables with no `default`, i.e. ones Terraform would otherwise
    prompt for interactively if no value is supplied on the command line."""
    required = set()
    for tf_file in sorted(terraform_dir.glob("*.tf")):
        text = tf_file.read_text(encoding="utf-8")
        for name, body in _variable_blocks(text):
            if not DEFAULT_KEY_RE.search(body):
                required.add(name)
    return required


def build_var_args(declared, known_values, extra_vars=None):
    extra_vars = extra_vars or {}
    values = {}
    for name in declared:
        if name in known_values and known_values[name] is not None:
            values[name] = known_values[name]
        elif name in extra_vars:
            values[name] = extra_vars[name]

    args = []
    for name, value in values.items():
        args.append(f"-var={name}={value}")
    return args
