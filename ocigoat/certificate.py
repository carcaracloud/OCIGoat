from pathlib import Path

try:
    from fpdf import FPDF
except ImportError as exc:
    raise ImportError("certificate generation requires: pip install -e '.[certificate]'") from exc

ASSETS_DIR = Path(__file__).parent / "assets"
BACKGROUND = ASSETS_DIR / "certificate_background.webp"
SIGNATURE = ASSETS_DIR / "signature.png"

PAGE_W, PAGE_H = 297, 210

WHITE = (255, 255, 255)
RED = (225, 60, 48)
GRAY_LIGHT = (195, 201, 211)
GRAY_MUTED = (145, 152, 166)

SIGNER_NAME = "Lucas Miranda"
SIGNER_TITLE = "Founder, OCIGoat"


def _centered_text(pdf, y, text, size, color, style=""):
    pdf.set_xy(0, y)
    pdf.set_font("Helvetica", style, size)
    pdf.set_text_color(*color)
    pdf.cell(PAGE_W, size * 0.5, text=text, align="C", new_x="LMARGIN", new_y="NEXT")


def render(player_name, scenario_ids, progress_data, out_path):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False)
    pdf.add_page()

    pdf.image(str(BACKGROUND), x=0, y=0, w=PAGE_W, h=PAGE_H)

    _centered_text(pdf, 52, "CERTIFICATE OF COMPLETION", 23, WHITE, style="B")
    _centered_text(
        pdf, 64,
        "OCIGoat  -  Vulnerable-by-design labs for Oracle Cloud Infrastructure",
        10, GRAY_LIGHT, style="I",
    )
    _centered_text(pdf, 80, "This certifies that", 11, GRAY_LIGHT)
    _centered_text(pdf, 90, player_name, 27, RED, style="B")

    pdf.set_draw_color(*GRAY_MUTED)
    pdf.set_line_width(0.3)
    pdf.line(PAGE_W / 2 - 35, 107, PAGE_W / 2 + 35, 107)

    pdf.set_xy((PAGE_W - 190) / 2, 113)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRAY_LIGHT)
    pdf.multi_cell(
        190, 5.2,
        text=(
            f"has completed all {len(scenario_ids)} flaggable OCIGoat scenarios, capturing a "
            "unique flag through real exploitation of a live Oracle Cloud Infrastructure "
            "tenancy for each one."
        ),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )

    rows = [(sid, progress_data[sid]["submitted_at"][:10]) for sid in scenario_ids]
    mid = (len(rows) + 1) // 2
    columns = (rows[:mid], rows[mid:])
    col_x = (PAGE_W / 2 - 78, PAGE_W / 2 + 8)
    grid_top = 128
    row_h = 5.9

    pdf.set_font("Courier", "", 9)
    for col, x in zip(columns, col_x):
        for i, (sid, date) in enumerate(col):
            y = grid_top + i * row_h
            pdf.set_xy(x, y)
            pdf.set_text_color(*WHITE)
            pdf.cell(45, row_h, text=sid, align="L", new_x="LMARGIN", new_y="TOP")
            pdf.set_xy(x + 45, y)
            pdf.set_text_color(*GRAY_MUTED)
            pdf.cell(25, row_h, text=date, align="L", new_x="LMARGIN", new_y="TOP")

    field_x, field_w = 72, 58
    sig_w, sig_h = 42, 9.2
    sig_x = field_x + (field_w - sig_w) / 2
    pdf.image(str(SIGNATURE), x=sig_x, y=160, w=sig_w, h=sig_h)

    pdf.set_draw_color(*GRAY_MUTED)
    pdf.set_line_width(0.25)
    pdf.line(field_x, 171.5, field_x + field_w, 171.5)

    pdf.set_xy(field_x, 173)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*WHITE)
    pdf.cell(field_w, 4, text=SIGNER_NAME, align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(field_x, 177.2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*GRAY_MUTED)
    pdf.cell(field_w, 3.5, text=SIGNER_TITLE, align="L", new_x="LMARGIN", new_y="NEXT")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path
