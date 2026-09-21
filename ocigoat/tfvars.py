import re

VARIABLE_BLOCK_RE = re.compile(r'^variable\s+"([A-Za-z0-9_]+)"\s*\{', re.MULTILINE)

KNOWN_AUTOFILL_VARS = {"compartment_id", "tenancy_ocid", "region", "test_user_api_public_key"}


def discover_declared_variables(terraform_dir):
    declared = set()
    for tf_file in sorted(terraform_dir.glob("*.tf")):
        text = tf_file.read_text(encoding="utf-8")
        declared.update(VARIABLE_BLOCK_RE.findall(text))
    return declared


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
