try:
    from fpdf import FPDF
except ImportError as exc:
    raise ImportError("certificate generation requires: pip install -e '.[certificate]'") from exc


def render(player_name, scenario_ids, progress_data, out_path):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, text="OCIGoat Certificate of Completion", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 12, text=f"Awarded to {player_name}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    for sid in scenario_ids:
        submitted_at = progress_data[sid]["submitted_at"]
        pdf.cell(0, 6, text=f"  {sid}   captured {submitted_at}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 5,
        text="Self-issued locally by the ocigoat CLI, based on real flags captured while exploiting "
        "each scenario against a real OCI tenancy. Not a proctored or externally verifiable credential.",
        new_x="LMARGIN", new_y="NEXT",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path
