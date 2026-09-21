from ocigoat import flags


def test_generate_flag_format():
    flag = flags.generate_flag("SCN-NET-001")
    assert flag.startswith("OCIGOAT{scn-net-001-")
    assert flag.endswith("}")


def test_generate_flag_is_unique_per_call():
    first = flags.generate_flag("SCN-NET-001")
    second = flags.generate_flag("SCN-NET-001")
    assert first != second


def test_hash_flag_deterministic():
    flag = "OCIGOAT{scn-net-001-deadbeef}"
    assert flags.hash_flag(flag) == flags.hash_flag(flag)
    assert flags.hash_flag(flag).startswith("sha256:")


def test_verify_flag_accepts_correct_flag():
    flag = flags.generate_flag("SCN-NET-001")
    expected_hash = flags.hash_flag(flag)
    assert flags.verify_flag(flag, expected_hash) is True


def test_verify_flag_rejects_wrong_flag():
    flag = flags.generate_flag("SCN-NET-001")
    expected_hash = flags.hash_flag(flag)
    assert flags.verify_flag("OCIGOAT{scn-net-001-wrongvalue}", expected_hash) is False


def test_verify_flag_strips_whitespace():
    flag = flags.generate_flag("SCN-NET-001")
    expected_hash = flags.hash_flag(flag)
    assert flags.verify_flag(f"  {flag}\n", expected_hash) is True
