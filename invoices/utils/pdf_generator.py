from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from django.conf import settings
from datetime import datetime
import os

# ============================================================
# Register a font that supports ₹ (Rupee symbol)
# ============================================================
FONT_NAME = 'Helvetica'  # default fallback

try:
    # Try common system fonts that support ₹
    font_paths = [
        'C:/Windows/Fonts/arial.ttf',                        # Windows
        'C:/Windows/Fonts/calibri.ttf',                      # Windows alt
        'C:/Windows/Fonts/segoeui.ttf',                      # Windows alt
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',   # Linux
        '/System/Library/Fonts/Helvetica.ttc',               # Mac
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            pdfmetrics.registerFont(TTFont('CustomFont', fp))
            FONT_NAME = 'CustomFont'
            print(f"✅ PDF Font registered: {fp}")
            break
    else:
        print("⚠️ No ₹-compatible font found, using Helvetica")
except Exception as e:
    print(f"⚠️ Font registration failed: {e}")


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    story = []

    # ============================================================
    # STYLES — All use FONT_NAME (which supports ₹)
    # ============================================================
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName=FONT_NAME,          # ✅ USE FONT_NAME
    )

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#3498db'),
        alignment=TA_RIGHT,
        spaceAfter=30,
        fontName=FONT_NAME,          # ✅ USE FONT_NAME
    )

    bill_to_style = ParagraphStyle(
        'BillToStyle',
        parent=styles['Heading4'],
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        fontName=FONT_NAME,          # ✅ USE FONT_NAME
    )

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName=FONT_NAME,          # ✅ USE FONT_NAME
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,          # ✅ USE FONT_NAME
    )

    # ============================================================
    # HEADER
    # ============================================================
    story.append(Paragraph(f"<b>{settings.COMPANY_NAME}</b>", header_style))
    story.append(Paragraph(
        f"{settings.COMPANY_ADDRESS}, {settings.COMPANY_CITY}, {settings.COMPANY_STATE}",
        normal_style
    ))
    story.append(Spacer(1, 0.2 * inch))

    # ============================================================
    # INVOICE INFO
    # ============================================================
    invoice_info = [
        ['Invoice:', invoice.invoice_number],
        ['Date:', invoice.issue_date.strftime('%Y-%m-%d') if hasattr(invoice.issue_date, 'strftime') else str(invoice.issue_date)],
        ['Due Date:', invoice.due_date.strftime('%Y-%m-%d') if hasattr(invoice.due_date, 'strftime') else str(invoice.due_date)],
        ['Status:', invoice.get_status_display()],
    ]

    info_table = Table(invoice_info, colWidths=[1.5 * inch, 2 * inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),        # ✅ USE FONT_NAME
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3 * inch))

    # ============================================================
    # BILL TO
    # ============================================================
    story.append(Paragraph("<b>Bill To:</b>", bill_to_style))
    story.append(Paragraph(invoice.customer.name, normal_style))
    story.append(Paragraph(invoice.customer.address_line1, normal_style))
    if invoice.customer.address_line2:
        story.append(Paragraph(invoice.customer.address_line2, normal_style))
    story.append(Paragraph(
        f"{invoice.customer.city}, {invoice.customer.state} {invoice.customer.postal_code}",
        normal_style
    ))
    story.append(Paragraph(invoice.customer.country, normal_style))
    if invoice.customer.phone:
        story.append(Paragraph(f"Phone: {invoice.customer.phone}", normal_style))
    if invoice.customer.email:
        story.append(Paragraph(f"Email: {invoice.customer.email}", normal_style))

    story.append(Spacer(1, 0.3 * inch))

    # ============================================================
    # ITEMS TABLE
    # ============================================================
    items_data = [
        ['#', 'Description', 'Qty', 'Price', 'Discount', 'Subtotal']
    ]

    for idx, item in enumerate(invoice.items.all(), 1):
        items_data.append([
            str(idx),
            item.description,
            str(item.quantity),
            f"{settings.CURRENCY} {item.price:.2f}",
            str(item.discount) if item.discount else '0',
            f"{settings.CURRENCY} {item.subtotal:.2f}"
        ])

    items_table = Table(
        items_data,
        colWidths=[0.5 * inch, 3 * inch, 0.7 * inch, 1 * inch, 0.8 * inch, 1.2 * inch]
    )
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),          # ✅ USE FONT_NAME
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),         # ✅ USE FONT_NAME
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3 * inch))

    # ============================================================
    # TOTALS
    # ============================================================
    totals_data = [
        ['Subtotal:', f"{settings.CURRENCY} {invoice.subtotal:.2f}"],
    ]
    if invoice.discount > 0:
        totals_data.append(['Discount:', f"{settings.CURRENCY} {invoice.discount:.2f}"])
    if invoice.shipping > 0:
        totals_data.append(['Shipping:', f"{settings.CURRENCY} {invoice.shipping:.2f}"])
    if invoice.vat > 0:
        totals_data.append(['VAT:', f"{settings.CURRENCY} {invoice.vat:.2f}"])
    totals_data.append(['Total:', f"{settings.CURRENCY} {invoice.total:.2f}"])

    totals_table = Table(totals_data, colWidths=[2 * inch, 1.5 * inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),         # ✅ USE FONT_NAME
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, -1), (-1, -1), FONT_NAME),        # ✅ USE FONT_NAME
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2c3e50')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#2c3e50')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#2c3e50')),
    ]))
    story.append(totals_table)

    # ============================================================
    # NOTES
    # ============================================================
    if invoice.notes:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("<b>Notes:</b>", bill_to_style))
        story.append(Paragraph(invoice.notes, normal_style))

    # ============================================================
    # FOOTER
    # ============================================================
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()