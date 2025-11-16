from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
import os


LABEL_DIR = "labels"
os.makedirs(LABEL_DIR, exist_ok=True)

def generate_label_pdf(consignment):

    filename = f"label_{consignment.id}.pdf"
    filepath = os.path.join(LABEL_DIR, filename)

    # Create Blank PDF
    c = canvas.Canvas(filepath, pagesize=A6)

    # Label Layout
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20,260, f"Consignment ID: {consignment.id}")

    c.setFont("Helvetica", 10)
    c.drawString(20, 230, f"Name: {consignment.name}")
    c.drawString(20, 210, f"{consignment.addressline1}")
    if consignment.addressline2:
        c.drawString(20, 195, f"{consignment.addressline2}")
    c.drawString(20, 180, f"{consignment.addressline3}")
    c.drawString(20, 165, f"{consignment.addressline4}")

    c.drawString(20, 140, f"Weight: {consignment.weight}kg")

    c.save()

    return filepath