import shutil
import subprocess

from ocigoat.errors import CredentialError

PRIVATE_KEY_NAME = "test-operator.pem"
PUBLIC_KEY_NAME = "test-operator_public.pem"


def generate_keypair(instance_dir):
    if shutil.which("openssl") is None:
        raise CredentialError("openssl not found on PATH; required to generate the test credential")

    private_key = instance_dir / PRIVATE_KEY_NAME
    public_key = instance_dir / PUBLIC_KEY_NAME

    gen = subprocess.run(
        ["openssl", "genrsa", "-out", str(private_key), "2048"],
        capture_output=True,
        text=True,
    )
    if gen.returncode != 0:
        raise CredentialError(f"openssl genrsa failed: {gen.stderr.strip()}")

    private_key.chmod(0o600)

    pub = subprocess.run(
        ["openssl", "rsa", "-pubout", "-in", str(private_key), "-out", str(public_key)],
        capture_output=True,
        text=True,
    )
    if pub.returncode != 0:
        raise CredentialError(f"openssl rsa -pubout failed: {pub.stderr.strip()}")

    return private_key, public_key


def write_test_operator_config(instance_dir, tenancy_ocid, region, user_ocid, fingerprint, private_key_path, out_name="oci_config"):
    out_path = instance_dir / out_name
    lines = [
        "[TEST_OPERATOR]",
        f"user={user_ocid}",
        f"fingerprint={fingerprint}",
        f"tenancy={tenancy_ocid}",
        f"region={region}",
        f"key_file={private_key_path}",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
