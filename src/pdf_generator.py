# src/pdf_generator.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PySide6.QtWidgets import QFileDialog # For saving file dialog

def register_fonts():
    """Registers standard fonts if not already registered."""
    try:
        # Register a commonly available font that supports a wider range of characters
        # Times-Roman, Helvetica, Courier are built-in.
        # If you need specific custom fonts, you'd register them here.
        # For now, let's use a standard font that's always available.
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arialbd.ttf'))
    except Exception:
        # Fallback if fonts are not found or already registered
        pass

# Ensure fonts are registered when the module is imported
register_fonts()


def generate_pdf_estimate(project_data: dict, line_items_data: list, financial_summary_data: dict):
    """
    Generates a PDF estimate document for a given project.

    Args:
        project_data (dict): Dictionary containing general project information.
        line_items_data (list): List of dictionaries, each representing a line item.
        financial_summary_data (dict): Dictionary containing calculated financial totals.
    """
    # Use QFileDialog to get a save file path from the user
    # Start in the user's documents directory or current working directory
    default_filename = f"Project_Estimate_{project_data['project_name'].replace(' ', '_')}_{project_data['project_id']}.pdf"
    file_path, _ = QFileDialog.getSaveFileName(
        None, "Save Project Estimate PDF", default_filename, "PDF Files (*.pdf);;All Files (*)"
    )

    if not file_path:
        return # User cancelled the save operation

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    h1_style = ParagraphStyle(
        name='h1_custom',
        parent=styles['h1'],
        fontSize=18,
        spaceAfter=14,
        alignment=1, # Center
        fontName='Helvetica-Bold'
    )
    h2_style = ParagraphStyle(
        name='h2_custom',
        parent=styles['h2'],
        fontSize=14,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        name='normal_custom',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica'
    )
    bold_style = ParagraphStyle(
        name='bold_custom',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    total_style = ParagraphStyle(
        name='total_custom',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=10,
        alignment=2, # Right alignment
        fontName='Helvetica-Bold'
    )

    Story = []

    # Title
    Story.append(Paragraph("Project Estimate", h1_style))
    Story.append(Spacer(1, 0.2 * inch))

    # Project and Client Information
    Story.append(Paragraph("Project Information", h2_style))
    Story.append(Paragraph(f"<b>Project Name:</b> {project_data['project_name']}", bold_style))
    Story.append(Paragraph(f"<b>Project ID:</b> {project_data['project_id']}", bold_style))
    Story.append(Paragraph(f"<b>Project Address:</b> {project_data['project_address']}", normal_style))
    Story.append(Paragraph(f"<b>Estimate Date:</b> {project_data['estimate_date']}", normal_style))
    Story.append(Paragraph(f"<b>Bid Due Date:</b> {project_data['bid_due_date']}", normal_style))
    Story.append(Spacer(1, 0.1 * inch))

    Story.append(Paragraph("Client Information", h2_style))
    Story.append(Paragraph(f"<b>Client Name:</b> {project_data['client_name']}", bold_style))
    Story.append(Paragraph(f"<b>Contact Person:</b> {project_data['client_contact']}", normal_style))
    Story.append(Paragraph(f"<b>Phone:</b> {project_data['client_phone']}", normal_style))
    Story.append(Paragraph(f"<b>Email:</b> {project_data['client_email']}", normal_style))
    Story.append(Paragraph(f"<b>Client Address:</b> {project_data['client_address']}", normal_style))
    Story.append(Spacer(1, 0.2 * inch))

    # Scope of Work
    if project_data['scope_of_work']:
        Story.append(Paragraph("Scope of Work", h2_style))
        Story.append(Paragraph(project_data['scope_of_work'], normal_style))
        Story.append(Spacer(1, 0.2 * inch))

    # Line Items Table
    Story.append(Paragraph("Estimate Line Items", h2_style))
    data = [["Description", "Category", "UOM", "Quantity", "Unit Cost", "Total"]]
    for item in line_items_data:
        data.append([
            item["description"],
            item["category"],
            item["uom"],
            f"{item['quantity']:.2f}",
            f"${item['unit_cost']:.2f}",
            f"${item['total']:.2f}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ADD8E6')), # Light Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Light background for rows
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    Story.append(table)
    Story.append(Spacer(1, 0.2 * inch))

    # Financial Summary (Client View - NO INTERNAL PROFIT)
    Story.append(Paragraph("Summary", h2_style))
    summary_data = []

    # Total Direct Cost
    summary_data.append(["Total Direct Cost:", f"${financial_summary_data['total_direct_cost']:.2f}"])

    # Markup Percentage (Visible to client)
    markup_percent = financial_summary_data['markup_percentage']
    summary_data.append(["Markup Percentage:", f"{markup_percent:.2f}%"])

    # Calculate subtotal after markup
    # This assumes markup is directly applied to the total direct cost to get the final client price
    # Based on your image: Final Project Estimate = Total Direct Cost * (1 + Markup %)
    # We explicitly exclude Overhead and Profit here as per your request
    final_estimate_for_client = financial_summary_data['total_direct_cost'] * (1 + markup_percent / 100.0)

    # Final Project Estimate
    summary_data.append(["Final Project Estimate:", f"${final_estimate_for_client:.2f}"])

    summary_table = Table(summary_data, colWidths=[3.5 * inch, 2.0 * inch]) # Adjust column widths
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'), # Align values to right
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), # Left column bold
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'), # Right column normal
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen), # Highlight final estimate
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
    ]))
    Story.append(summary_table)
    Story.append(Spacer(1, 0.2 * inch))

    # Project Notes
    if project_data['project_notes']:
        Story.append(Paragraph("Project Notes", h2_style))
        Story.append(Paragraph(project_data['project_notes'], normal_style))
        Story.append(Spacer(1, 0.2 * inch))

    # Build the PDF
    doc.build(Story)