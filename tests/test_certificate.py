import pytest

fpdf2 = pytest.importorskip("fpdf")

from ocigoat import certificate


def test_render_produces_a_real_pdf(tmp_path):
    data = {
        "SCN-NET-001": {"submitted_at": "2026-09-21T14:00:00+00:00"},
        "SCN-STORAGE-001": {"submitted_at": "2026-09-21T14:05:00+00:00"},
    }
    out_path = tmp_path / "certificates" / "cert.pdf"

    result = certificate.render("Test Player", sorted(data), data, out_path)

    assert result == out_path
    assert out_path.exists()
    assert out_path.read_bytes()[:5] == b"%PDF-"
    assert out_path.stat().st_size > 500
