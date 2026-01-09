from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

import os


LABEL_DIR = "labels"
os.makedirs(LABEL_DIR, exist_ok=True)

def generate_label_pdf(consignment):

    filename = f"label_{consignment.consignment_number}.pdf"
    filepath = os.path.join(LABEL_DIR, filename)

    # Create Blank PDF
    c = canvas.Canvas(filepath, pagesize=A6)

    #Box Dims
    box_x = 15
    box_y = 150
    box_width = 200
    box_height = 220
    # Label Layout
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    c.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)

    c.setFont("Helvetica", 10)
    c.drawString(20, 350, f"Account: {consignment.account_no}")

    c.line(15, 340, 215, 340)

    c.drawString(20, 320, f"{consignment.name}")
    c.drawString(20, 300, f"{consignment.addressline1}")
    if consignment.addressline2:
        c.drawString(20, 275, f"{consignment.addressline2}")
    c.drawString(20, 260, f"{consignment.addressline3}")
    c.drawString(20, 245, f"{consignment.addressline4}")

    # BIG DEPOT NUMBER
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(colors.black)

    # Centered depot number inside the box
    c.drawCentredString(
        box_x + box_width / 2 + 40,
        box_y + box_height - 200,
        f"{consignment.delivery_depot}"
    )

    c.setFont("Helvetica", 10)

    c.drawString(20, 130, f"Consignment No: {consignment.consignment_number}")

    c.drawString(160, 130, f"Weight: {consignment.weight}kg")

    barcode_value = str(consignment.consignment_number) 

    barcode = code128.Code128(barcode_value, barHeight=18*mm, barWidth=2)

   
    barcode_x = box_x + (box_width - barcode.width) / 2
    barcode_y = box_y - 80

    barcode.drawOn(c, barcode_x, barcode_y)

    # Optional: human-readable text under barcode
    c.setFont("Helvetica", 9)
    c.drawCentredString(box_x + box_width/2, barcode_y - 12, barcode_value)

    c.save()

    return filepath