from ocigoat import paths, progress


def test_load_progress_missing_file_returns_empty(home_dir_override):
    assert progress.load_progress() == {}


def test_record_flag_hash_writes_unsubmitted_entry(home_dir_override):
    data = progress.record_flag_hash("SCN-NET-001", "sha256:abc")
    assert data["SCN-NET-001"] == {"flag_hash": "sha256:abc", "submitted_at": None}
    assert progress.load_progress() == data


def test_record_flag_hash_noop_if_already_submitted(home_dir_override):
    progress.record_flag_hash("SCN-NET-001", "sha256:abc")
    progress.mark_submitted("SCN-NET-001")
    before = progress.load_progress()

    progress.record_flag_hash("SCN-NET-001", "sha256:different")

    after = progress.load_progress()
    assert after == before
    assert after["SCN-NET-001"]["flag_hash"] == "sha256:abc"


def test_mark_submitted_sets_timestamp(home_dir_override):
    progress.record_flag_hash("SCN-NET-001", "sha256:abc")
    data = progress.mark_submitted("SCN-NET-001")
    assert data["SCN-NET-001"]["submitted_at"] is not None


def test_save_progress_is_crash_safe_no_partial_file(home_dir_override):
    progress.record_flag_hash("SCN-NET-001", "sha256:abc")
    tmp_leftover = paths.ocigoat_home() / "progress.json.tmp"
    assert not tmp_leftover.exists()
    assert paths.progress_path().exists()
