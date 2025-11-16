from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
import os


LABEL_DIR = "labels"
os.makedirs(LABEL_DIR, exist_ok=True)

def generate_label_pdf(consignment):

    filename = f"label_{consignment.id}.pdf"
    filepath = os.path.join(LABEL_DIR, filename)

    # Create Blank PDF
    c = canvas.Canvas(filepath, pagesize=A6)

    #Box Dims
    box_x = 15
    box_y = 150
    box_width = 170
    box_height = 100
    # Label Layout
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    c.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)

    c.setFont("Helvetica", 10)
    c.drawString(20, 230, f"{consignment.name}")
    c.drawString(20, 210, f"{consignment.addressline1}")
    if consignment.addressline2:
        c.drawString(20, 195, f"{consignment.addressline2}")
    c.drawString(20, 180, f"{consignment.addressline3}")
    c.drawString(20, 165, f"{consignment.addressline4}")

    c.drawString(20, 130, f"Consignment ID: {consignment.id}")

    c.drawString(20, 100, f"Weight: {consignment.weight}kg")

    c.save()

    return filepath