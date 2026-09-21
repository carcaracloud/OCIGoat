import subprocess
from unittest.mock import patch

import pytest

from ocigoat import credential
from ocigoat.errors import CredentialError


def _fake_openssl_run(args, capture_output, text):
    if args[:2] == ["openssl", "genrsa"]:
        out_path = args[args.index("-out") + 1]
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("fake private key\n")
    elif args[:2] == ["openssl", "rsa"]:
        out_path = args[args.index("-out") + 1]
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("fake public key\n")
    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")


def test_generate_keypair_writes_both_files(tmp_path):
    with patch("ocigoat.credential.shutil.which", return_value="/usr/bin/openssl"):
        with patch("ocigoat.credential.subprocess.run", side_effect=_fake_openssl_run):
            private_key, public_key = credential.generate_keypair(tmp_path)
    assert private_key.name == "test-operator.pem"
    assert public_key.name == "test-operator_public.pem"
    assert private_key.read_text() == "fake private key\n"
    assert public_key.read_text() == "fake public key\n"


def test_generate_keypair_missing_openssl_raises(tmp_path):
    with patch("ocigoat.credential.shutil.which", return_value=None):
        with pytest.raises(CredentialError):
            credential.generate_keypair(tmp_path)


def test_generate_keypair_openssl_failure_raises(tmp_path):
    failed = subprocess.CompletedProcess(["openssl"], 1, stdout="", stderr="boom")
    with patch("ocigoat.credential.shutil.which", return_value="/usr/bin/openssl"):
        with patch("ocigoat.credential.subprocess.run", return_value=failed):
            with pytest.raises(CredentialError):
                credential.generate_keypair(tmp_path)


def test_write_test_operator_config_exact_content(tmp_path):
    out_path = credential.write_test_operator_config(
        tmp_path,
        tenancy_ocid="ocid1.tenancy.oc1..xyz",
        region="sa-saopaulo-1",
        user_ocid="ocid1.user.oc1..abc",
        fingerprint="aa:bb:cc",
        private_key_path=tmp_path / "test-operator.pem",
    )
    expected = (
        "[TEST_OPERATOR]\n"
        "user=ocid1.user.oc1..abc\n"
        "fingerprint=aa:bb:cc\n"
        "tenancy=ocid1.tenancy.oc1..xyz\n"
        "region=sa-saopaulo-1\n"
        f"key_file={tmp_path / 'test-operator.pem'}\n"
    )
    assert out_path.read_text() == expected
