import hashlib
import hmac
import secrets

FLAG_FORMAT = "OCIGOAT{{{scenario_id}-{suffix}}}"


def generate_flag(scenario_id):
    return FLAG_FORMAT.format(scenario_id=scenario_id.lower(), suffix=secrets.token_hex(8))


def hash_flag(flag):
    digest = hashlib.sha256(flag.strip().encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def verify_flag(flag, expected_hash):
    return hmac.compare_digest(hash_flag(flag), expected_hash)
