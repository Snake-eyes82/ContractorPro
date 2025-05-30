# src/estimate_line_items_view.py (Comprehensive Update)
import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QComboBox, QGridLayout, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction

from database import Session, Project, EstimateLineItem
# Import create_engine, declarative_base, sessionmaker, relationship if not already imported in database.py's global scope
# Assuming database.py handles the imports needed for its models
# For the view, we primarily need Session, Project, and EstimateLineItem
# from datetime import date # Already handled by QDateEdit for date widgets, not directly needed here

# Import for PDF generation (will be created/updated next)
from pdf_generator import generate_project_estimate_pdf # This will need to be implemented

class EstimateLineItemsWindow(QMainWindow):
    project_updated_signal = Signal() # Declare the signal here
    def __init__(self, project_id: int, parent=None):
        super().__init__(parent)
        self.db_session = Session()
        self.current_project_id = project_id
        self.project = None # To store the loaded Project object
        self.load_project_data() # Load project details including percentages

        self.setWindowTitle(f"Estimate Line Items for Project ID: {self.current_project_id}")
        self.setGeometry(100, 100, 1200, 800) # Increased size for better layout
        self.setMinimumSize(QSize(1000, 700))

        self.init_ui()
        self.load_line_items()
        self.calculate_financial_summary() # Initial calculation after loading line items

    def load_project_data(self):
        """Loads the associated Project details, including percentages."""
        try:
            self.project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if not self.project:
                QMessageBox.critical(self, "Error", f"Project with ID {self.current_project_id} not found.")
                # self.close() # Maybe close if no project, or disable all functionality
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load project details: {e}")
            self.project = None

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Section: Project Name and ID
        top_info_layout = QHBoxLayout()
        self.project_name_label = QLabel("Project Name: N/A")
        if self.project:
            self.project_name_label.setText(f"Project Name: {self.project.project_name}")
        top_info_layout.addWidget(self.project_name_label)
        top_info_layout.addStretch(1)
        top_info_layout.addWidget(QLabel(f"Project ID: {self.current_project_id}"))
        main_layout.addLayout(top_info_layout)

        main_layout.addWidget(QLabel("<h2>Estimate Line Items</h2>", alignment=Qt.AlignCenter))

        # --- Input Form for Line Items ---
        input_form_group = QGroupBox("Line Item Details")
        input_form_layout = QFormLayout(input_form_group)
        input_form_layout.setContentsMargins(10, 20, 10, 10)
        input_form_layout.setSpacing(8)

        self.description_input = QLineEdit()
        input_form_layout.addRow("Description:", self.description_input)

        self.category_input = QLineEdit() # Could be QComboBox for predefined categories later
        input_form_layout.addRow("Category:", self.category_input)

        self.uom_input = QLineEdit() # Unit of Measure
        input_form_layout.addRow("Unit of Measure (UOM):", self.uom_input)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 9999999.99)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setValue(0.01)
        self.quantity_input.setSingleStep(0.01)
        input_form_layout.addRow("Quantity:", self.quantity_input)

        self.unit_cost_input = QDoubleSpinBox()
        self.unit_cost_input.setRange(0.01, 9999999.99)
        self.unit_cost_input.setDecimals(2)
        self.unit_cost_input.setValue(0.01)
        self.unit_cost_input.setSingleStep(0.01)
        input_form_layout.addRow("Unit Cost:", self.unit_cost_input)

        self.total_item_cost_label = QLabel("$0.00")
        input_form_layout.addRow("Total Item Cost:", self.total_item_cost_label)

        # Connect signals for auto-calculation
        self.quantity_input.valueChanged.connect(self.calculate_item_total)
        self.unit_cost_input.valueChanged.connect(self.calculate_item_total)

        main_layout.addWidget(input_form_group)

        # --- Action Buttons for Line Items ---
        buttons_layout = QHBoxLayout()
        self.add_line_item_button = QPushButton("Add Line Item")
        self.add_line_item_button.clicked.connect(self.add_line_item)
        buttons_layout.addWidget(self.add_line_item_button)

        self.update_line_item_button = QPushButton("Update Line Item")
        self.update_line_item_button.clicked.connect(self.update_line_item)
        self.update_line_item_button.setEnabled(False) # Disabled until an item is selected
        buttons_layout.addWidget(self.update_line_item_button)

        self.delete_line_item_button = QPushButton("Delete Line Item")
        self.delete_line_item_button.clicked.connect(self.delete_line_item)
        self.delete_line_item_button.setEnabled(False) # Disabled until an item is selected
        buttons_layout.addWidget(self.delete_line_item_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_form_inputs)
        buttons_layout.addWidget(self.clear_form_button)
        buttons_layout.addStretch(1) # Push buttons to the left

        main_layout.addLayout(buttons_layout)

        # --- Table for Current Line Items ---
        self.line_items_table = QTableWidget()
        self.line_items_table.setColumnCount(7) # ID, Description, Category, UOM, Quantity, Unit Cost, Total
        self.line_items_table.setHorizontalHeaderLabels([
            "ID", "Description", "Category", "UOM", "Quantity", "Unit Cost", "Total"
        ])
        self.line_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.line_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.line_items_table.itemSelectionChanged.connect(self.load_selected_line_item)
        main_layout.addWidget(self.line_items_table)

        # --- Financial Summary Section ---
        financial_summary_group = QGroupBox("Financial Summary")
        financial_summary_layout = QFormLayout(financial_summary_group)
        financial_summary_layout.setContentsMargins(10, 20, 10, 10)
        financial_summary_layout.setSpacing(8)

        # Display percentages loaded from Project
        self.markup_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Markup Percentage:", self.markup_percentage_label)

        self.overhead_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Overhead Percentage:", self.overhead_percentage_label)

        self.profit_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Profit Percentage:", self.profit_percentage_label)


        # Calculated summary values
        self.total_direct_cost_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Direct Cost:", self.total_direct_cost_label)

        self.total_overhead_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Overhead:", self.total_overhead_label)

        self.total_profit_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Profit:", self.total_profit_label)

        self.final_project_estimate_label = QLabel("<font color='blue' size='5'>$0.00</font>")
        financial_summary_layout.addRow("<b>Final Project Estimate:</b>", self.final_project_estimate_label)

        main_layout.addWidget(financial_summary_group)

        main_layout.addStretch(1) # Pushes everything to the top

        # --- Generate PDF Button ---
        pdf_button_layout = QHBoxLayout()
        pdf_button_layout.addStretch(1)
        self.generate_pdf_button = QPushButton("Generate PDF Estimate")
        self.generate_pdf_button.clicked.connect(self.generate_estimate_pdf)
        pdf_button_layout.addWidget(self.generate_pdf_button)
        pdf_button_layout.addStretch(1) # Center the button
        main_layout.addLayout(pdf_button_layout)


    def calculate_item_total(self):
        """Calculates and displays the total for the current line item input."""
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()
        total = quantity * unit_cost
        self.total_item_cost_label.setText(f"${total:.2f}")

    def load_line_items(self):
        """Loads all line items for the current project into the table."""
        self.line_items_table.setRowCount(0) # Clear existing rows
        try:
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()
            for row_idx, item in enumerate(line_items):
                self.line_items_table.insertRow(row_idx)
                self.line_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.line_item_id)))
                self.line_items_table.setItem(row_idx, 1, QTableWidgetItem(item.description))
                self.line_items_table.setItem(row_idx, 2, QTableWidgetItem(item.category or "")) # Handle None
                self.line_items_table.setItem(row_idx, 3, QTableWidgetItem(item.unit_of_measure_uom or "")) # Handle None
                self.line_items_table.setItem(row_idx, 4, QTableWidgetItem(f"{item.quantity:.2f}"))
                self.line_items_table.setItem(row_idx, 5, QTableWidgetItem(f"${item.unit_cost:.2f}"))
                self.line_items_table.setItem(row_idx, 6, QTableWidgetItem(f"${item.total_cost:.2f}"))
            self.calculate_financial_summary() # Recalculate after loading
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load line items: {e}")

    def add_line_item(self):
        description = self.description_input.text().strip()
        category = self.category_input.text().strip()
        uom = self.uom_input.text().strip()
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()
        total_cost = quantity * unit_cost

        if not description:
            QMessageBox.warning(self, "Input Error", "Description cannot be empty.")
            return
        if quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Quantity and Unit Cost must be greater than zero.")
            return

        try:
            new_item = EstimateLineItem(
                project_id=self.current_project_id,
                description=description,
                category=category if category else None,
                unit_of_measure_uom=uom if uom else None,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total_cost
            )
            self.db_session.add(new_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Line item added successfully!")
            self.clear_form_inputs()
            self.load_line_items() # Reload table and summary
            self.project_updated_signal.emit()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add line item: {e}")

    def update_line_item(self):
        selected_rows = self.line_items_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a line item to update.")
            return

        row = selected_rows[0].row()
        line_item_id = int(self.line_items_table.item(row, 0).text())

        description = self.description_input.text().strip()
        category = self.category_input.text().strip()
        uom = self.uom_input.text().strip()
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()
        total_cost = quantity * unit_cost

        if not description:
            QMessageBox.warning(self, "Input Error", "Description cannot be empty.")
            return
        if quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Quantity and Unit Cost must be greater than zero.")
            return

        try:
            item_to_update = self.db_session.query(EstimateLineItem).filter_by(line_item_id=line_item_id).first()
            if item_to_update:
                item_to_update.description = description
                item_to_update.category = category if category else None
                item_to_update.unit_of_measure_uom = uom if uom else None
                item_to_update.quantity = quantity
                item_to_update.unit_cost = unit_cost
                item_to_update.total_cost = total_cost
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Line item updated successfully!")
                self.clear_form_inputs()
                self.load_line_items() # Reload table and summary
                self.project_updated_signal.emit()
            else:
                QMessageBox.warning(self, "Error", "Line item not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update line item: {e}")

    def delete_line_item(self):
        selected_rows = self.line_items_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a line item to delete.")
            return

        row = selected_rows[0].row()
        line_item_id = int(self.line_items_table.item(row, 0).text())

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete line item ID {line_item_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                item_to_delete = self.db_session.query(EstimateLineItem).filter_by(line_item_id=line_item_id).first()
                if item_to_delete:
                    self.db_session.delete(item_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Line item deleted successfully!")
                    self.clear_form_inputs()
                    self.load_line_items() # Reload table and summary
                    self.project_updated_signal.emit()
                else:
                    QMessageBox.warning(self, "Error", "Line item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete line item: {e}")

    def load_selected_line_item(self):
        """Loads data from the selected table row into the input fields."""
        selected_rows = self.line_items_table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            self.description_input.setText(self.line_items_table.item(row, 1).text())
            self.category_input.setText(self.line_items_table.item(row, 2).text())
            self.uom_input.setText(self.line_items_table.item(row, 3).text())
            self.quantity_input.setValue(float(self.line_items_table.item(row, 4).text()))
            self.unit_cost_input.setValue(float(self.line_items_table.item(row, 5).text().replace('$', ''))) # Remove $
            self.calculate_item_total() # Update total item cost label

            self.update_line_item_button.setEnabled(True)
            self.delete_line_item_button.setEnabled(True)
            self.add_line_item_button.setEnabled(False) # Disable Add when updating
        else:
            self.clear_form_inputs()
            self.update_line_item_button.setEnabled(False)
            self.delete_line_item_button.setEnabled(False)
            self.add_line_item_button.setEnabled(True)


    def clear_form_inputs(self):
        self.description_input.clear()
        self.category_input.clear()
        self.uom_input.clear()
        self.quantity_input.setValue(0.01)
        self.unit_cost_input.setValue(0.01)
        self.total_item_cost_label.setText("$0.00")
        self.line_items_table.clearSelection() # Deselect any rows

        self.update_line_item_button.setEnabled(False)
        self.delete_line_item_button.setEnabled(False)
        self.add_line_item_button.setEnabled(True)

    def calculate_financial_summary(self):
        """Calculates and updates the financial summary section."""
        total_direct_cost = 0.0
        # Sum up total_cost from all line items in the table
        for row in range(self.line_items_table.rowCount()):
            item_total_str = self.line_items_table.item(row, 6).text().replace('$', '')
            try:
                total_direct_cost += float(item_total_str)
            except ValueError:
                pass # Skip if value is not a valid number

        self.total_direct_cost_label.setText(f"${total_direct_cost:.2f}")

        markup_percent = self.project.markup_percentage if self.project and self.project.markup_percentage is not None else 0.0
        overhead_percent = self.project.overhead_percentage if self.project and self.project.overhead_percentage is not None else 0.0
        profit_percent = self.project.profit_percentage if self.project and self.project.profit_percentage is not None else 0.0

        self.markup_percentage_label.setText(f"{markup_percent:.2f}%")
        self.overhead_percentage_label.setText(f"{overhead_percent:.2f}%")
        self.profit_percentage_label.setText(f"{profit_percent:.2f}%") # This will be hidden/removed for client view later

        # Calculations
        total_overhead = total_direct_cost * (overhead_percent / 100.0)
        # Profit is typically calculated on (Direct Cost + Overhead)
        total_profit = (total_direct_cost + total_overhead) * (profit_percent / 100.0)
        # Markup is usually applied on total direct cost, but the screenshot seems to have a different structure.
        # Let's assume Markup is applied on Total Direct Cost + Overhead + Profit.
        # However, the previous structure of Markup% being a separate field is usually for the final price.
        # For now, let's keep it simple with Direct, Overhead, Profit adding up.
        # If Markup means a final *percentage increase* on the sum, we'll apply it last.
        # If Markup is meant to be profit, then profit_percentage should be used for that.
        # Let's stick to the structure in the report: Direct, Markup (shown as a separate percentage), Overhead, Profit.
        # The report screenshot shows markup % but then $0.00 for overhead and profit.
        # The prompt says "overhead and profit do not show up" and "we would not like any clients to see the profit margin".
        # This implies markup is visible, profit isn't.

        # Let's re-interpret based on common estimation practices and your report:
        # Total Direct Cost (already calculated)
        # Total Overhead = Direct Cost * (Overhead % / 100)
        # Subtotal (Direct + Overhead) = Total Direct Cost + Total Overhead
        # Total Profit = Subtotal * (Profit % / 100)
        # Estimated Price = Subtotal + Total Profit
        # Final Markup (if applied as a separate line item on the final price)

        # Given your report shows Markup Percentage: 20.00%, but then Overhead and Profit are 0.00% and $0.00,
        # it suggests Markup might be the only "profit-like" field shown to the client on the PDF,
        # and Overhead/Profit are internal.
        # For the internal calculation in the app, we need to use all three:

        self.total_overhead_label.setText(f"${total_overhead:.2f}")
        self.total_profit_label.setText(f"${total_profit:.2f}")

        # The "Final Project Estimate" should include all costs and profits.
        # The report shows Markup Percentage 20.00% applied. Let's assume this markup
        # is distinct from the "Profit %" field and is the final percentage added.
        # If Markup % is meant to be the *actual* profit, then `profit_percentage`
        # should ideally be renamed or reused.

        # For the calculations based on your request:
        # Calculate Total Cost (Direct + Overhead)
        subtotal_before_profit = total_direct_cost + total_overhead
        final_estimate = subtotal_before_profit + total_profit

        # If Markup is a separate, final percentage applied to the entire sum:
        # final_estimate_with_markup = final_estimate * (1 + markup_percent / 100.0)
        # However, your report shows Markup alongside Direct Cost, then Overhead and Profit as 0.
        # This implies the 20% Markup is already being *calculated* into the Total Direct Cost shown,
        # or it's a separate calculation line not yet visible.

        # Given the report's display:
        # Total Direct Cost: $57.22 (this should include material, labor etc. line items)
        # Markup Percentage: 20.00%
        # Total Overhead (0.00%): $0.00
        # Total Profit (0.00%): $0.00
        # Final Project Estimate: $68.66

        # This implies:
        # $57.22 * (1 + 20.00 / 100) = $57.22 * 1.20 = $68.664 (which rounds to $68.66)
        # So, it looks like only Markup is applied to the Direct Cost for the FINAL client estimate.
        # The Overhead and Profit percentages you've added to the Project model might be for internal tracking only.

        # Let's adjust calculations to match the PDF behavior in image_ad7717.png
        # For the client-facing "Final Project Estimate" (which the PDF reflects)
        # it seems to be Total Direct Cost + (Total Direct Cost * Markup Percentage / 100)
        # For internal view, we'll show all three.

        # Internal calculations for display in the app:
        # (Total Direct Cost + Overhead + Profit)
        final_project_estimate_internal = total_direct_cost + total_overhead + total_profit
        self.final_project_estimate_label.setText(f"<font color='blue' size='5'>${final_project_estimate_internal:.2f}</font>")

        # For the PDF, we will use the `markup_percentage` in the final calculation,
        # and omit `overhead_percentage` and `profit_percentage` details from the client view.


    def generate_estimate_pdf(self):
        """Generates a PDF estimate based on current project data and line items."""
        if not self.project:
            QMessageBox.warning(self, "Error", "No project data available to generate PDF.")
            return

        # Gather all necessary data for the PDF
        project_data = {
            "project_name": self.project.project_name,
            "project_id": self.project.project_id,
            "client_name": self.project.client_name,
            "client_contact": self.project.client_contact,
            "client_phone": self.project.client_phone,
            "client_email": self.project.client_email,
            "client_address_street": self.project.client_address_street, # Pass individual components
            "client_address_city": self.project.client_address_city,
            "client_address_state": self.project.client_address_state,
            "client_address_zip": self.project.client_address_zip,
            "project_address_street": self.project.project_address_street, # Pass individual components
            "project_address_city": self.project.project_address_city,
            "project_address_state": self.project.project_address_state,
            "project_address_zip": self.project.project_address_zip,
            "estimate_date": self.project.estimate_date.strftime("%Y-%m-%d") if self.project.estimate_date else "N/A",
            "bid_due_date": self.project.bid_due_date.strftime("%Y-%m-%d") if self.project.bid_due_date else "N/A",
            "project_status": self.project.project_status,
            "contract_type": self.project.contract_type,
            "scope_of_work": self.project.scope_of_work,
            "project_notes": self.project.project_notes,
            "markup_percentage": self.project.markup_percentage if self.project.markup_percentage is not None else 0.0,
            "overhead_percentage": self.project.overhead_percentage if self.project.overhead_percentage is not None else 0.0,
            "profit_percentage": self.project.profit_percentage if self.project.profit_percentage is not None else 0.0,
        }

        line_items_data = []
        for row in range(self.line_items_table.rowCount()):
            line_items_data.append({
                "line_item_id": int(self.line_items_table.item(row, 0).text()), # Use line_item_id as expected by pdf_generator
                "description": self.line_items_table.item(row, 1).text(),
                "category": self.line_items_table.item(row, 2).text(),
                "unit_of_measure_uom": self.line_items_table.item(row, 3).text(), # Use full name
                "quantity": float(self.line_items_table.item(row, 4).text()),
                "unit_cost": float(self.line_items_table.item(row, 5).text().replace('$', '')),
                "total_cost": float(self.line_items_table.item(row, 6).text().replace('$', '')) # Use total_cost
            })

        # Define the output filename - use project name for clarity
        # Make sure the filename is valid and doesn't contain invalid characters
        project_name_safe = "".join([c if c.isalnum() or c in (' ', '_', '-') else '' for c in project_data["project_name"]]).strip()
        output_filename = f"Estimate_{project_name_safe.replace(' ', '_')}_{project_data['project_id']}.pdf"
        output_filename = os.path.join(os.getcwd(), output_filename) # Save in current working directory
        default_filename = f"Estimate_{project_name_safe.replace(' ', '_')}_{project_data['project_id']}.pdf"
        # Open file dialog to let user choose save location and name
        # QFileDialog.getSaveFileName returns a tuple (filename, selected_filter)
        # We only need the filename, so we use output_filename, _
        output_filename, _ = QFileDialog.getSaveFileName(
        self,
        "Save Project Estimate PDF",
        default_filename,
        "PDF Files (*.pdf);;All Files (*)"
        )

        # For now, let's assume no logo path or a fixed one for testing
        # We will implement dynamic logo upload later
        # Example: logo_path = "path/to/your/logo.png"
        logo_path = None # Set to None for now, or provide a test logo path if you have one.

        try:
            # Call the generate_project_estimate_pdf function with the correct arguments
            success = generate_project_estimate_pdf(
                project_data,
                line_items_data,
                output_filename, # This must be a string filename!
                logo_path
            )

            if success:
                QMessageBox.information(self, "PDF Generated", f"Project Estimate PDF saved as:\n{output_filename}")
                # Optional: Open the PDF after generation
                import subprocess
                try:
                    subprocess.Popen([output_filename], shell=True)
                except Exception as open_error:
                    print(f"Could not open PDF automatically: {open_error}")
            else:
                QMessageBox.critical(self, "PDF Generation Failed", "An error occurred during PDF generation. Check console for details.")

        except Exception as e:
            QMessageBox.critical(self, "PDF Generation Error", f"Failed to generate PDF: {e}")
            print(f"Error generating PDF: {e}")

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)

# -----------------------------------------------------------------------------
# Standalone testing block
# -----------------------------------------------------------------------------
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     from database import create_db_and_tables, Project, EstimateLineItem, Session
#     from datetime import date # Explicit import for the test block

#     create_db_and_tables()

#     session = Session()
#     # # Ensure a project exists for testing
#     # test_project = session.query(Project).filter_by(project_name="Test Project with Line Items").first()
#     # if not test_project:
#     #     new_project = Project(
#     #         project_name="Test Project with Line Items",
#     #         client_name="Acme Corp",
#     #         client_contact="Wile E. Coyote",
#     #         client_phone="555-BUG-BUNY",
#     #         client_email="wile.e@acme.com",
#     #         client_address_street="1 Roadrunner Lane",
#     #         client_address_city="Desert",
#     #         client_address_state="AZ",
#     #         client_address_zip="85001",
#     #         project_address_street="A Canyon Edge",
#     #         project_address_city="Canyonland",
#     #         project_address_state="AZ",
#     #         project_address_zip="85002",
#     #         estimate_date=date(2025, 5, 20),
#     #         bid_due_date=date(2025, 6, 1),
#     #         project_status="New",
#     #         contract_type="Fixed Price",
#     #         markup_percentage=20.0, # Test value
#     #         overhead_percentage=5.0, # Test value
#     #         profit_percentage=10.0, # Test value
#     #         scope_of_work="Testing scope for line items.",
#     #         project_notes="Testing notes for line items."
#     #     )
#     #     session.add(new_project)
#     #     session.commit()
#     #     test_project_id = new_project.project_id

#     #     # Add some sample line items
#     #     line_item1 = EstimateLineItem(
#     #         project_id=test_project_id,
#     #         description="Material A",
#     #         category="Materials",
#     #         unit_of_measure_uom="Pcs",
#     #         quantity=10.0,
#     #         unit_cost=5.0,
#     #         total_cost=50.0
#     #     )
#     #     line_item2 = EstimateLineItem(
#     #         project_id=test_project_id,
#     #         description="Labor B",
#     #         category="Labor",
#     #         unit_of_measure_uom="Hrs",
#     #         quantity=5.0,
#     #         unit_cost=25.0,
#     #         total_cost=125.0
#     #     )
#     #     session.add_all([line_item1, line_item2])
#     #     session.commit()
#     # else:
#     #     test_project_id = test_project.project_id

#     session.close()

#     window = EstimateLineItemsWindow(project_id=test_project_id)
#     window.show()
#     sys.exit(app.exec())