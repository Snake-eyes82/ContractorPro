# src/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os

def generate_project_estimate_pdf(project_data, line_items_data, output_filename="project_estimate.pdf", logo_path=None):
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # --- Custom Styles (for branding) ---
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['h1'],
        alignment=TA_CENTER,
        fontSize=24,
        spaceAfter=10,
        textColor=colors.HexColor('#0056b3') # Example primary color
    )
    sub_header_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['h2'],
        fontSize=16,
        spaceAfter=8,
        spaceBefore=10,
        textColor=colors.HexColor('#333333')
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10

    # --- 1. Company Logo (if provided) ---
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5 * inch, height=0.75 * inch)
            story.append(logo)
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            print(f"Warning: Could not load logo from {logo_path}: {e}")
            pass

    # --- 2. Main Title ---
    story.append(Paragraph("Project Estimate", header_style))
    story.append(Spacer(1, 0.2 * inch))

    # --- 3. Project Information ---
    story.append(Paragraph("General Project Information:", sub_header_style))
    project_info_data = [
        ["Project Name:", project_data.get('project_name', '')],
        ["Project ID:", str(project_data.get('project_id', ''))],
        ["Client Name:", project_data.get('client_name', '')],
        ["Client Contact:", project_data.get('client_contact', '')],
        ["Client Phone:", project_data.get('client_phone', '')],
        ["Client Email:", project_data.get('client_email', '')],
        # Combine address components for display
        ["Client Address:", f"{project_data.get('client_address_street', '')}, {project_data.get('client_address_city', '')}, {project_data.get('client_address_state', '')} {project_data.get('client_address_zip', '')}"],
        ["Project Address:", f"{project_data.get('project_address_street', '')}, {project_data.get('project_address_city', '')}, {project_data.get('project_address_state', '')} {project_data.get('project_address_zip', '')}"],
        ["Estimate Date:", project_data.get('estimate_date', '')],
        ["Bid Due Date:", project_data.get('bid_due_date', '')],
        ["Project Status:", project_data.get('project_status', '')],
        ["Contract Type:", project_data.get('contract_type', '')]
    ]
    project_info_table = Table(project_info_data, colWidths=[1.5 * inch, 5.5 * inch])
    project_info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(project_info_table)
    story.append(Spacer(1, 0.1 * inch))

    # --- 4. Scope of Work ---
    story.append(Paragraph("Scope of Work:", sub_header_style))
    story.append(Paragraph(project_data.get('scope_of_work', 'No scope provided.'), normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # --- 5. Project Notes ---
    story.append(Paragraph("Project Notes:", sub_header_style))
    story.append(Paragraph(project_data.get('project_notes', 'No notes provided.'), normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # --- 6. Estimate Line Items ---
    story.append(Paragraph("Detailed Estimate Line Items:", sub_header_style))
    table_headers = ["ID", "Description", "Category", "UOM", "Quantity", "Unit Cost", "Total"]
    table_data = [table_headers]

    total_direct_cost = 0.0
    for item in line_items_data:
        row = [
            str(item.get('line_item_id', '')),
            item.get('description', ''),
            item.get('category', ''),
            item.get('unit_of_measure_uom', ''),
            f"{item.get('quantity', 0.0):.2f}",
            f"${item.get('unit_cost', 0.0):.2f}",
            f"${item.get('total_cost', 0.0):.2f}"
        ]
        table_data.append(row)
        total_direct_cost += item.get('total_cost', 0.0)

    col_widths = [0.5*inch, 2.0*inch, 1.0*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.8*inch]
    line_item_table = Table(table_data, colWidths=col_widths)
    line_item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (-3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#000000')),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(line_item_table)
    story.append(Spacer(1, 0.2 * inch))

    # --- 7. Summary ---
    story.append(Paragraph("Financial Summary:", sub_header_style))

    markup_percentage = project_data.get('markup_percentage', 0.0)
    overhead_percentage = project_data.get('overhead_percentage', 0.0)
    # profit_percentage = project_data.get('profit_percentage', 0.0) # Still omitted from client PDF

    total_overhead_cost = total_direct_cost * (overhead_percentage / 100.0)

    # Final Project Estimate for client view: Total Direct Cost + Total Overhead + (Total Direct Cost + Total Overhead) * (Markup Percentage / 100)
    # This aligns with the previous internal calculation being shown for Markup, but now includes overhead.
    # If the markup is truly meant to be applied *last* on everything (Direct + Overhead), then the calculation below is correct.
    # Based on image_a121d0.png, it looks like:
    # Total Direct Cost ($400)
    # Overhead Percentage (5%) -> Total Overhead ($20)
    # Markup Percentage (20%)
    # Final Project Estimate ($604.80)
    # Calculation from image_a121d0.png: (400 + 20) * 1.20 = 420 * 1.20 = 504.
    # Ah, wait, image_a121d0.png shows:
    # Total Direct Cost: $400.00
    # Overhead Percentage: 5.00%
    # Total Overhead: $20.00 (400 * 0.05)
    # Profit Percentage: 20.00%
    # Total Profit: $84.00 ( (400 + 20) * 0.20 )
    # Markup Percentage: 20.00%
    # Final Project Estimate: $604.80 ( (400 + 20 + 84) * 1.20 ) -> (504 * 1.2) = 604.80

    # This means Markup % *is* applied on the total (Direct + Overhead + Profit).
    # Since we are removing Profit from the client PDF, we need to decide if Markup % still applies
    # to the *internal* profit for the calculation, or if the markup *is* the profit for the client.

    # Given your instruction "we can keep the overhead in it just get the profit out of it",
    # and the previous client PDF (image_ad7717.png) showing only Markup % applied to Direct Cost.
    # And the new provided PDF (image_a121d0.png) showing Overhead, Profit, and then Markup applied on the *total*.

    # Let's go with the calculation shown in image_a121d0.png for *your internal app view*,
    # but for the *client PDF*, we will only show Direct Cost and Overhead Cost,
    # and apply the Markup Percentage to (Direct Cost + Overhead Cost) to get the final estimate.
    # This means the `profit_percentage` from the Project model is strictly internal and not part of this client PDF calculation.

    # Calculation for the client-facing PDF summary (based on image_a28e93.png and your request):
    # Total Direct Cost
    # Total Overhead
    # Final Project Estimate = (Total Direct Cost + Total Overhead) * (1 + Markup Percentage / 100)

    final_project_estimate_for_client = (total_direct_cost + total_overhead_cost) * (1 + markup_percentage / 100.0)


    summary_data = [
        ["Total Direct Cost:", f"${total_direct_cost:.2f}"],
        ["Markup Percentage:", f"{markup_percentage:.2f}%"],
        ["Total Overhead ({}%):".format(overhead_percentage), f"${total_overhead_cost:.2f}"], # Show Overhead
        # "Total Profit" row is still omitted from client PDF.
        ["Final Project Estimate:", f"${final_project_estimate_for_client:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.blue),
        ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#EEEEEE')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#CCFFCC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#000000')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2 * inch))

    # Build the PDF
    try:
        doc.build(story)
        print(f"PDF generated successfully: {output_filename}")
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    from datetime import date
    dummy_project = {
        'project_name': "Demo Project",
        'project_id': 101,
        'project_address_street': "123 Main St",
        'project_address_city': "Anytown",
        'project_address_state': "CA",
        'project_address_zip': "90210",
        'estimate_date': date.today().strftime("%Y-%m-%d"),
        'bid_due_date': date.today().strftime("%Y-%m-%d"),
        'client_name': "Acme Corp",
        'client_contact': "Jane Doe",
        'client_phone': "555-123-4567",
        'client_email': "jane.doe@example.com",
        'client_address_street': "456 Oak Ave",
        'client_address_city': "Othercity",
        'client_address_state': "NY",
        'client_address_zip': "10001",
        'markup_percentage': 20.0,
        'overhead_percentage': 5.0, # Will now be shown
        'profit_percentage': 10.0,  # Still omitted from client PDF
        'scope_of_work': "This is a detailed scope of work for the demo project, including all tasks and deliverables. It aims to provide a comprehensive overview of the services to be rendered.",
        'project_notes': "These are some important notes about the project, such as special considerations or client requests. This section can contain a lot of text."
    }

    dummy_line_items = [
        {'line_item_id': 1, 'description': 'Item A', 'category': 'Labor', 'unit_of_measure_uom': 'hr', 'quantity': 10.0, 'unit_cost': 50.0, 'total_cost': 500.0},
        {'line_item_id': 2, 'description': 'Item B with a longer description to test wrapping and table layout', 'category': 'Materials', 'unit_of_measure_uom': 'unit', 'quantity': 5.0, 'unit_cost': 25.0, 'total_cost': 125.0},
        {'line_item_id': 3, 'description': 'Item C', 'category': 'Subcontractor', 'unit_of_measure_uom': 'job', 'quantity': 1.0, 'unit_cost': 300.0, 'total_cost': 300.0},
    ]

    test_logo_path = "my_company_logo.png" # Create this file for testing logo
    if not os.path.exists(test_logo_path):
         print(f"NOTE: For logo test, please create a dummy image named '{test_logo_path}' in this directory.")
         test_logo_path = None

    generate_project_estimate_pdf(dummy_project, dummy_line_items, "test_estimate_with_overhead.pdf", logo_path=test_logo_path)
    # generate_project_estimate_pdf(dummy_project, dummy_line_items, "test_estimate_no_logo.pdf") # Can uncomment for additional test