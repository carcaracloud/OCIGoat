from ocigoat import paths, progress, scenarios, ui
from ocigoat.errors import OcigoatError


def run(args):
    flaggable = sorted(sid for sid, m in scenarios.discover_scenarios().items() if m.flag)
    if not flaggable:
        raise OcigoatError("no flaggable scenarios found; nothing to certify.")

    data = progress.load_progress()
    missing = [sid for sid in flaggable if not data.get(sid, {}).get("submitted_at")]
    if missing:
        raise OcigoatError(
            f"certificate requires every flaggable scenario to be captured. "
            f"missing: {', '.join(missing)}. Run 'ocigoat progress' for details."
        )

    try:
        from ocigoat import certificate
        from fpdf.errors import FPDFUnicodeEncodingException
    except ImportError as exc:
        raise OcigoatError("certificate generation requires: pip install -e '.[certificate]'") from exc

    out_path = args.out or (paths.certificates_dir() / "ocigoat-certificate.pdf")
    try:
        certificate.render(args.name, flaggable, data, out_path)
    except FPDFUnicodeEncodingException as exc:
        raise OcigoatError(
            f"certificate name has a character the PDF font can't render: {exc.character!r}. "
            "Use Latin-1 characters only (basic accents are fine, e.g. \"João\")."
        ) from exc
    ui.info(f"certificate written to {out_path}")
    return 0
