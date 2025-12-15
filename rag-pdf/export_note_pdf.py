from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

def generate_note_pdf(title: str, content: str, sources: str, output_path: str):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)

    elements = []

    elements.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for para in content.split("\n\n"):
        elements.append(Paragraph(para, styles["BodyText"]))
        elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 16))
    elements.append(Paragraph("<b>Sources</b>", styles["Heading2"]))
    elements.append(Paragraph(sources, styles["BodyText"]))

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            f"<i>Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}</i>",
            styles["Normal"]
        )
    )

    doc.build(elements)
