# src/project_details_window.py (MODIFIED)
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QTextEdit, QMessageBox, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout, QDateEdit,
    QTabWidget, QComboBox, QDoubleSpinBox, QAbstractSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, QDate, Signal, QSize
from datetime import date

# Import your database models
from src.database import Session, Project, EstimateLineItem

# --- PDF GENERATION LIBRARY (Install if you haven't) ---
# You'll need ReportLab for PDF generation.
# If you don't have it, open your terminal and run:
# pip install reportlab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

class ProjectDetailsWindow(QMainWindow):
    # Define a custom signal to notify the main window of project changes
    project_updated_signal = Signal()
    project_deleted_signal = Signal(int) # Signal to send deleted project ID

    def __init__(self, project_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Details")
        self.setGeometry(200, 200, 1000, 800) # Adjust size for new window
        self.setMinimumSize(QSize(600, 500))

        self.db_session = Session()
        self.current_project_id = project_id
        self.current_line_item_id = None
        self.current_project_direct_cost = 0.0 # To store the sum of direct costs

        # --- IMPORTANT for QMainWindow: Create a central widget and set its layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget) # This layout now applies to the central widget

        self.init_ui() # Call init_ui to populate the layout on the central widget
        self.load_project_data(project_id)


    def init_ui(self):
        # All widgets and layouts will now be added to self.main_layout

        self.main_layout.addWidget(QLabel("<h1>Project Details</h1>"))

        # Display total project estimate, markup, overhead, profit right below the Project Details header
        self.total_direct_cost_label = QLabel("<b>Total Direct Cost: $0.00</b>")
        self.total_overhead_label = QLabel("<b>Total Overhead: $0.00</b>")
        self.total_profit_label = QLabel("<b>Total Profit: $0.00</b>")
        self.total_final_estimate_label = QLabel("<b>Final Project Estimate: $0.00</b>")

        self.total_direct_cost_label.setStyleSheet("font-size: 16px;")
        self.total_overhead_label.setStyleSheet("font-size: 16px;")
        self.total_profit_label.setStyleSheet("font-size: 16px;")
        self.total_final_estimate_label.setStyleSheet("font-size: 20px; color: green;")

        self.main_layout.addWidget(self.total_direct_cost_label)
        self.main_layout.addWidget(self.total_overhead_label)
        self.main_layout.addWidget(self.total_profit_label)
        self.main_layout.addWidget(self.total_final_estimate_label)
        self.main_layout.addSpacing(10) # Add some space

        # --- NEW: Generate PDF Button ---
        pdf_button_layout = QHBoxLayout()
        self.generate_pdf_button = QPushButton("Generate PDF")
        self.generate_pdf_button.clicked.connect(self.generate_project_pdf)
        pdf_button_layout.addStretch(1) # Push button to the right
        pdf_button_layout.addWidget(self.generate_pdf_button)
        pdf_button_layout.addStretch(1) # Center the button
        self.main_layout.addLayout(pdf_button_layout)
        self.main_layout.addSpacing(10)


        self.project_tabs = QTabWidget()
        self.main_layout.addWidget(self.project_tabs) # Add the tab widget to the main layout

        # --- Tab 1: General Project Info ---
        self.general_info_tab = QWidget()
        self.general_info_layout = QVBoxLayout()
        self.general_info_tab.setLayout(self.general_info_layout)
        self.project_tabs.addTab(self.general_info_tab, "General Info")

        self.project_details_form_layout = QFormLayout()
        self.general_info_layout.addLayout(self.project_details_form_layout)

        self.detail_project_id = QLabel("")
        self.detail_project_name = QLineEdit()
        self.detail_client_name = QLineEdit()
        self.detail_client_contact = QLineEdit()
        self.detail_client_phone = QLineEdit()
        self.detail_client_email = QLineEdit()
        self.detail_client_address_street = QLineEdit()
        self.detail_client_address_city = QLineEdit()
        self.detail_client_address_state = QLineEdit()
        self.detail_client_address_zip = QLineEdit()
        self.detail_project_address_street = QLineEdit()
        self.detail_project_address_city = QLineEdit()
        self.detail_project_address_state = QLineEdit()
        self.detail_project_address_zip = QLineEdit()
        self.detail_estimate_date = QDateEdit(calendarPopup=True)
        self.detail_estimate_date.setCalendarPopup(True)
        self.detail_bid_due_date = QDateEdit(calendarPopup=True)
        self.detail_bid_due_date.setCalendarPopup(True)
        self.detail_project_status = QLineEdit()
        self.detail_contract_type = QLineEdit()
        self.detail_scope_of_work = QTextEdit()
        self.detail_project_notes = QTextEdit()

        # Markup, Overhead, Profit fields
        self.detail_markup_percentage = QDoubleSpinBox()
        self.detail_markup_percentage.setRange(0.0, 100.0)
        self.detail_markup_percentage.setSuffix("%")
        self.detail_markup_percentage.setDecimals(2)
        self.detail_markup_percentage.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.detail_markup_percentage.valueChanged.connect(self.recalculate_project_totals)

        self.detail_overhead_percentage = QDoubleSpinBox()
        self.detail_overhead_percentage.setRange(0.0, 100.0)
        self.detail_overhead_percentage.setSuffix("%")
        self.detail_overhead_percentage.setDecimals(2)
        self.detail_overhead_percentage.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.detail_overhead_percentage.valueChanged.connect(self.recalculate_project_totals)

        self.detail_profit_percentage = QDoubleSpinBox()
        self.detail_profit_percentage.setRange(0.0, 100.0)
        self.detail_profit_percentage.setSuffix("%")
        self.detail_profit_percentage.setDecimals(2)
        self.detail_profit_percentage.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.detail_profit_percentage.valueChanged.connect(self.recalculate_project_totals)

        self.project_details_form_layout.addRow("Project ID:", self.detail_project_id)
        self.project_details_form_layout.addRow("Project Name:", self.detail_project_name)
        self.project_details_form_layout.addRow("Client Name:", self.detail_client_name)
        self.project_details_form_layout.addRow("Client Contact:", self.detail_client_contact)
        self.project_details_form_layout.addRow("Client Phone:", self.detail_client_phone)
        self.project_details_form_layout.addRow("Client Email:", self.detail_client_email)
        self.project_details_form_layout.addRow("Client Address Street:", self.detail_client_address_street)
        self.project_details_form_layout.addRow("Client Address City:", self.detail_client_address_city)
        self.project_details_form_layout.addRow("Client Address State:", self.detail_client_address_state)
        self.project_details_form_layout.addRow("Client Address Zip:", self.detail_client_address_zip)
        self.project_details_form_layout.addRow("Project Address Street:", self.detail_project_address_street)
        self.project_details_form_layout.addRow("Project Address City:", self.detail_project_address_city)
        self.project_details_form_layout.addRow("Project Address State:", self.detail_project_address_state)
        self.project_details_form_layout.addRow("Project Address Zip:", self.detail_project_address_zip)
        self.project_details_form_layout.addRow("Estimate Date:", self.detail_estimate_date)
        self.project_details_form_layout.addRow("Bid Due Date:", self.detail_bid_due_date)
        self.project_details_form_layout.addRow("Project Status:", self.detail_project_status)
        self.project_details_form_layout.addRow("Contract Type:", self.detail_contract_type)
        self.project_details_form_layout.addRow("Scope of Work:", self.detail_scope_of_work)
        self.project_details_form_layout.addRow("Project Notes:", self.detail_project_notes)
        self.project_details_form_layout.addRow("Markup Percentage:", self.detail_markup_percentage)
        self.project_details_form_layout.addRow("Overhead Percentage:", self.detail_overhead_percentage)
        self.project_details_form_layout.addRow("Profit Percentage:", self.detail_profit_percentage)

        button_layout = QHBoxLayout()
        self.save_project_button = QPushButton("Save Changes")
        self.save_project_button.clicked.connect(self.save_project_changes)
        button_layout.addWidget(self.save_project_button)

        self.delete_project_button = QPushButton("Delete Project")
        self.delete_project_button.clicked.connect(self.delete_project)
        button_layout.addWidget(self.delete_project_button)
        self.general_info_layout.addLayout(button_layout)
        self.general_info_layout.addStretch(1)


        # --- Tab 2: Estimate Line Items ---
        self.line_items_tab = QWidget()
        self.line_items_layout = QVBoxLayout()
        self.line_items_tab.setLayout(self.line_items_layout)
        self.project_tabs.addTab(self.line_items_tab, "Estimate Line Items")

        # Add/Edit Line Item Form
        line_item_form_group_box = QVBoxLayout()
        self.line_items_layout.addLayout(line_item_form_group_box)

        line_item_form_title = QLabel("<h3>Add/Edit Line Item:</h3>")
        line_item_form_group_box.addWidget(line_item_form_title)

        self.line_item_form_layout = QFormLayout()
        line_item_form_group_box.addLayout(self.line_item_form_layout)

        self.line_item_id_label = QLabel("ID: None")
        self.line_item_form_layout.addRow("Line Item ID:", self.line_item_id_label)

        self.line_item_description_input = QLineEdit()
        self.line_item_form_layout.addRow("Description:", self.line_item_description_input)

        self.line_item_category_input = QComboBox()
        self.line_item_category_input.addItems(["Material", "Labor", "Equipment", "Subcontractor", "Other Direct Cost", "Overhead", "Profit", "Allowance", "Contingency"])
        self.line_item_form_layout.addRow("Category:", self.line_item_category_input)

        self.line_item_uom_input = QLineEdit()
        self.line_item_uom_input.setPlaceholderText("e.g., EA, LF, SF, HR")
        self.line_item_form_layout.addRow("UoM:", self.line_item_uom_input)

        self.line_item_quantity_input = QDoubleSpinBox()
        self.line_item_quantity_input.setRange(0.0, 99999999.0)
        self.line_item_quantity_input.setDecimals(2)
        self.line_item_quantity_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.line_item_quantity_input.valueChanged.connect(self.update_line_item_total_cost) # Connect
        self.line_item_form_layout.addRow("Quantity:", self.line_item_quantity_input)

        self.line_item_unit_cost_input = QDoubleSpinBox()
        self.line_item_unit_cost_input.setRange(0.0, 99999999.0)
        self.line_item_unit_cost_input.setDecimals(2)
        self.line_item_unit_cost_input.setPrefix("$")
        self.line_item_unit_cost_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.line_item_unit_cost_input.valueChanged.connect(self.update_line_item_total_cost) # Connect
        self.line_item_form_layout.addRow("Unit Cost:", self.line_item_unit_cost_input)

        # Line item buttons
        line_item_button_layout = QHBoxLayout()
        self.add_line_item_button = QPushButton("Add New Line Item")
        self.add_line_item_button.clicked.connect(self.add_new_line_item)
        line_item_button_layout.addWidget(self.add_line_item_button)

        self.save_line_item_button = QPushButton("Save Line Item Changes")
        self.save_line_item_button.clicked.connect(self.save_line_item_changes)
        self.save_line_item_button.setEnabled(False)
        line_item_button_layout.addWidget(self.save_line_item_button)

        self.delete_line_item_button = QPushButton("Delete Line Item")
        self.delete_line_item_button.clicked.connect(self.delete_line_item)
        self.delete_line_item_button.setEnabled(False)
        line_item_button_layout.addWidget(self.delete_line_item_button)

        self.clear_line_item_form_button = QPushButton("Clear Form")
        self.clear_line_item_form_button.clicked.connect(self.clear_line_item_inputs)
        line_item_button_layout.addWidget(self.clear_line_item_form_button)

        line_item_form_group_box.addLayout(line_item_button_layout)

        # Line Items Table
        self.line_items_layout.addWidget(QLabel("<h3>Project Line Items:</h3>"))
        self.line_items_table = QTableWidget()
        # Ensure column headers match the database model and display
        self.line_items_table.setColumnCount(7)
        self.line_items_table.setHorizontalHeaderLabels(["ID", "Description", "Category", "UoM", "Qty", "Unit Cost", "Total Direct Cost"])
        self.line_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.line_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Description stretches
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.line_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.line_items_table.itemSelectionChanged.connect(self.display_line_item_details)
        self.line_items_layout.addWidget(self.line_items_table)
        self.line_items_layout.addStretch(1)

        # Set initial state for detail fields (all enabled since it's a dedicated window)
        self.set_line_item_inputs_enabled(True)
        self.update_project_summary_labels(0.0, 0.0, 0.0) # Initialize totals
        self.main_layout.addStretch(1)

    def update_line_item_total_cost(self):
        """Calculates and updates the total cost for the current line item form."""
        quantity = self.line_item_quantity_input.value()
        unit_cost = self.line_item_unit_cost_input.value()
        # total_cost_calculated = quantity * unit_cost
        # You might want to display this on the form if you have a label for it
        # self.line_item_total_cost_label.setText(f"${total_cost_calculated:.2f}")

    def update_project_summary_labels(self, direct_cost: float, overhead: float, profit: float):
        """Updates the labels displaying the project summary totals."""
        final_estimate = direct_cost + overhead + profit
        self.total_direct_cost_label.setText(f"<b>Total Direct Cost: ${direct_cost:,.2f}</b>")
        self.total_overhead_label.setText(f"<b>Total Overhead: ${overhead:,.2f}</b>")
        self.total_profit_label.setText(f"<b>Total Profit: ${profit:,.2f}</b>")
        self.total_final_estimate_label.setText(f"<b>Final Project Estimate: ${final_estimate:,.2f}</b>")

    def recalculate_project_totals(self):
        """Recalculates and updates project totals based on line items and percentages."""
        if self.current_project_id is None:
            self.update_project_summary_labels(0.0, 0.0, 0.0)
            return

        try:
            # Query line items for the current project
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()
            
            # Sum up total_direct_cost from all line items
            # Assuming EstimateLineItem has a 'total_direct_cost' attribute
            total_direct_cost = sum(item.total_direct_cost for item in line_items)
            self.current_project_direct_cost = total_direct_cost # Store for PDF generation

            markup_percentage = self.detail_markup_percentage.value() / 100.0
            overhead_percentage = self.detail_overhead_percentage.value() / 100.0
            profit_percentage = self.detail_profit_percentage.value() / 100.0

            # Calculations based on common construction estimating practices:
            # Markup is applied to direct cost
            subtotal_after_markup = total_direct_cost * (1 + markup_percentage)
            
            # Overhead is applied to the subtotal after markup
            calculated_overhead = subtotal_after_markup * overhead_percentage
            
            # Profit is applied to the subtotal after overhead
            subtotal_after_overhead = subtotal_after_markup + calculated_overhead
            calculated_profit = subtotal_after_overhead * profit_percentage

            self.update_project_summary_labels(total_direct_cost, calculated_overhead, calculated_profit)

        except Exception as e:
            print(f"Error recalculating project totals: {e}")
            self.update_project_summary_labels(0.0, 0.0, 0.0) # Reset on error

    def set_line_item_inputs_enabled(self, enabled: bool):
        """Enables or disables the line item input fields for new/editing."""
        self.line_item_description_input.setEnabled(enabled)
        self.line_item_category_input.setEnabled(enabled)
        self.line_item_uom_input.setEnabled(enabled)
        self.line_item_quantity_input.setEnabled(enabled)
        self.line_item_unit_cost_input.setEnabled(enabled)
        self.add_line_item_button.setEnabled(enabled)
        self.clear_line_item_form_button.setEnabled(enabled)
        # Save and Delete line item buttons are enabled/disabled based on item selection, not global state

    def load_project_data(self, project_id):
        self.current_project_id = project_id
        if project_id is None:
            self.clear_project_details()
            return

        try:
            project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if project:
                self.detail_project_id.setText(str(project.project_id))
                self.detail_project_name.setText(project.project_name or "")
                self.detail_client_name.setText(project.client_name or "")
                
                # Use .get() or hasattr() for optional attributes to prevent AttributeError
                self.detail_client_contact.setText(getattr(project, 'client_contact_person', "") or "")
                self.detail_client_phone.setText(getattr(project, 'client_phone', "") or "")
                self.detail_client_email.setText(getattr(project, 'client_email', "") or "")
                self.detail_client_address_street.setText(getattr(project, 'client_address_street', "") or "")
                self.detail_client_address_city.setText(getattr(project, 'client_address_city', "") or "")
                self.detail_client_address_state.setText(getattr(project, 'client_address_state', "") or "")
                self.detail_client_address_zip.setText(getattr(project, 'client_address_zip', "") or "")
                self.detail_project_address_street.setText(getattr(project, 'project_address_street', "") or "")
                self.detail_project_address_city.setText(getattr(project, 'project_address_city', "") or "")
                self.detail_project_address_state.setText(getattr(project, 'project_address_state', "") or "")
                self.detail_project_address_zip.setText(getattr(project, 'project_address_zip', "") or "")
                
                self.detail_estimate_date.setDate(QDate.fromJulianDay(project.estimate_date.toordinal()) if project.estimate_date else QDate.currentDate())
                self.detail_bid_due_date.setDate(QDate.fromJulianDay(project.bid_due_date.toordinal()) if project.bid_due_date else QDate.currentDate())
                self.detail_project_status.setText(project.project_status or "")
                self.detail_contract_type.setText(project.contract_type or "")
                self.detail_scope_of_work.setText(project.scope_of_work or "")
                self.detail_project_notes.setText(project.project_notes or "")
                self.detail_markup_percentage.setValue(project.markup_percentage if project.markup_percentage is not None else 0.0)
                self.detail_overhead_percentage.setValue(project.overhead_percentage if project.overhead_percentage is not None else 0.0)
                self.detail_profit_percentage.setValue(project.profit_percentage if project.profit_percentage is not None else 0.0)

                self.load_line_items_for_project(self.current_project_id)
                self.recalculate_project_totals() # Recalculate totals after loading
            else:
                QMessageBox.warning(self, "Error", "Project not found in database.")
                self.clear_project_details()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project details: {e}")
            self.clear_project_details()

    def load_line_items_for_project(self, project_id):
        try:
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=project_id).all()
            self.line_items_table.setRowCount(len(line_items))
            for row, item in enumerate(line_items):
                self.line_items_table.setItem(row, 0, QTableWidgetItem(str(item.line_item_id)))
                self.line_items_table.setItem(row, 1, QTableWidgetItem(item.line_item_description or ""))
                self.line_items_table.setItem(row, 2, QTableWidgetItem(item.category or ""))
                self.line_items_table.setItem(row, 3, QTableWidgetItem(item.unit_of_measure_uom or ""))
                self.line_items_table.setItem(row, 4, QTableWidgetItem(f"{item.quantity:.2f}"))
                self.line_items_table.setItem(row, 5, QTableWidgetItem(f"$ {item.unit_cost:.2f}"))
                # Assuming 'total_direct_cost' is the correct field in EstimateLineItem for this purpose
                self.line_items_table.setItem(row, 6, QTableWidgetItem(f"$ {item.total_direct_cost:.2f}"))
            
            # Adjust column width for total_direct_cost column if needed
            self.line_items_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

            self.recalculate_project_totals() # Recalculate totals after loading line items
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load line items: {e}")
            self.line_items_table.setRowCount(0)
            self.recalculate_project_totals() # Ensure totals are reset on error

    def clear_project_details(self):
        self.detail_project_id.setText("")
        self.detail_project_name.clear()
        self.detail_client_name.clear()
        self.detail_client_contact.clear()
        self.detail_client_phone.clear()
        self.detail_client_email.clear()
        self.detail_client_address_street.clear()
        self.detail_client_address_city.clear()
        self.detail_client_address_state.clear()
        self.detail_client_address_zip.clear()
        self.detail_project_address_street.clear()
        self.detail_project_address_city.clear()
        self.detail_project_address_state.clear()
        self.detail_project_address_zip.clear()
        self.detail_estimate_date.setDate(QDate.currentDate())
        self.detail_bid_due_date.setDate(QDate.currentDate())
        self.detail_project_status.clear()
        self.detail_contract_type.clear()
        self.detail_scope_of_work.clear()
        self.detail_project_notes.clear()
        self.detail_markup_percentage.setValue(0.0)
        self.detail_overhead_percentage.setValue(0.0)
        self.detail_profit_percentage.setValue(0.0)
        self.clear_line_item_inputs()
        self.line_items_table.setRowCount(0)
        self.update_project_summary_labels(0.0, 0.0, 0.0) # Reset all totals

    def clear_line_item_inputs(self):
        self.line_item_id_label.setText("ID: None")
        self.line_item_description_input.clear()
        self.line_item_category_input.setCurrentIndex(0)
        self.line_item_uom_input.clear()
        self.line_item_quantity_input.setValue(0.0)
        self.line_item_unit_cost_input.setValue(0.0)
        self.current_line_item_id = None
        self.add_line_item_button.setEnabled(True)
        self.save_line_item_button.setEnabled(False)
        self.delete_line_item_button.setEnabled(False)
        self.line_items_table.clearSelection() # Clear selection in table

    def save_project_changes(self):
        if self.current_project_id is None:
            QMessageBox.warning(self, "No Project Selected", "This window was opened without a project ID. Cannot save.")
            return

        try:
            project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if project:
                project.project_name = self.detail_project_name.text().strip()
                project.client_name = self.detail_client_name.text().strip()
                
                # Safely update new project fields if they exist in the model
                if hasattr(project, 'client_contact_person'): project.client_contact_person = self.detail_client_contact.text().strip()
                if hasattr(project, 'client_phone'): project.client_phone = self.detail_client_phone.text().strip()
                if hasattr(project, 'client_email'): project.client_email = self.detail_client_email.text().strip()
                if hasattr(project, 'client_address_street'): project.client_address_street = self.detail_client_address_street.text().strip()
                if hasattr(project, 'client_address_city'): project.client_address_city = self.detail_client_address_city.text().strip()
                if hasattr(project, 'client_address_state'): project.client_address_state = self.detail_client_address_state.text().strip()
                if hasattr(project, 'client_address_zip'): project.client_address_zip = self.detail_client_address_zip.text().strip()
                if hasattr(project, 'project_address_street'): project.project_address_street = self.detail_project_address_street.text().strip()
                if hasattr(project, 'project_address_city'): project.project_address_city = self.detail_project_address_city.text().strip()
                if hasattr(project, 'project_address_state'): project.project_address_state = self.detail_project_address_state.text().strip()
                if hasattr(project, 'project_address_zip'): project.project_address_zip = self.detail_project_address_zip.text().strip()

                project.estimate_date = self.detail_estimate_date.date().toPython()
                project.bid_due_date = self.detail_bid_due_date.date().toPython()
                project.project_status = self.detail_project_status.text().strip()
                project.contract_type = self.detail_contract_type.text().strip()
                project.scope_of_work = self.detail_scope_of_work.toPlainText().strip()
                project.project_notes = self.detail_project_notes.toPlainText().strip()
                project.markup_percentage = self.detail_markup_percentage.value()
                project.overhead_percentage = self.detail_overhead_percentage.value()
                project.profit_percentage = self.detail_profit_percentage.value()

                self.db_session.commit()
                QMessageBox.information(self, "Success", f"Project '{project.project_name}' updated successfully!")
                self.recalculate_project_totals()
                self.project_updated_signal.emit() # Emit signal to notify main window
            else:
                QMessageBox.warning(self, "Error", "Selected project not found in database.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save changes: {e}")

    def delete_project(self):
        if self.current_project_id is None:
            QMessageBox.warning(self, "No Project Selected", "This window was opened without a project ID. Cannot delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                    f"Are you sure you want to delete Project ID: {self.current_project_id} and all its associated data (line items, expenses, invoices)? This cannot be undone.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
                if project:
                    # SQLAlchemy's cascade="all, delete-orphan" on the relationship
                    # should handle deleting associated line items automatically.
                    # No need for explicit delete query here if cascade is properly set up.
                    self.db_session.delete(project)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Project deleted successfully!")
                    self.project_deleted_signal.emit(self.current_project_id) # Emit signal
                    self.close() # Close the window (QMainWindow doesn't use accept())
                else:
                    QMessageBox.warning(self, "Error", "Selected project not found in database.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete project: {e}")

    def add_new_line_item(self):
        if self.current_project_id is None:
            QMessageBox.warning(self, "No Project Selected", "Please select a project before adding line items.")
            return

        description = self.line_item_description_input.text().strip()
        category = self.line_item_category_input.currentText()
        uom = self.line_item_uom_input.text().strip()
        quantity = self.line_item_quantity_input.value()
        unit_cost = self.line_item_unit_cost_input.value()

        if not description or not category:
            QMessageBox.warning(self, "Input Error", "Description and Category cannot be empty for a line item.")
            return

        # Refine validation for categories that might not need quantity/unit_cost
        if category in ["Overhead", "Profit", "Allowance", "Contingency"]:
            # For these categories, quantity/unit_cost might be 0, or represent a lump sum value
            # Adjust validation based on how you handle these specific line items
            # For simplicity, if total_direct_cost is the value, then quantity=1, unit_cost=value.
            # Or if it's a percentage based line item, it might be handled differently
            pass # Allow 0 for these categories
        elif quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Quantity and Unit Cost must be greater than zero for this category.")
            return

        try:
            total_direct_cost = quantity * unit_cost

            new_line_item = EstimateLineItem(
                project_id=self.current_project_id,
                line_item_description=description,
                category=category,
                unit_of_measure_uom=uom,
                quantity=quantity,
                unit_cost=unit_cost,
                total_direct_cost=total_direct_cost, # Store the calculated value
                # These might be deprecated or unused if the project level calculates markups/profits
                markup_percentage=0.0,
                marked_up_unit_price=unit_cost,
                total_line_item_price=total_direct_cost
            )
            self.db_session.add(new_line_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", f"Line item '{description}' added to project!")

            self.clear_line_item_inputs()
            self.load_line_items_for_project(self.current_project_id) # Reload and recalculate totals
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add line item: {e}")

    def display_line_item_details(self):
        selected_items = self.line_items_table.selectedItems()
        if not selected_items:
            self.clear_line_item_inputs()
            return

        row = selected_items[0].row()
        line_item_id_str = self.line_items_table.item(row, 0).text()
        self.current_line_item_id = int(line_item_id_str)

        try:
            line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=self.current_line_item_id).first()
            if line_item:
                self.line_item_id_label.setText(f"ID: {line_item.line_item_id}")
                self.line_item_description_input.setText(line_item.line_item_description or "")
                index = self.line_item_category_input.findText(line_item.category)
                if index >= 0:
                    self.line_item_category_input.setCurrentIndex(index)
                self.line_item_uom_input.setText(line_item.unit_of_measure_uom or "")
                self.line_item_quantity_input.setValue(line_item.quantity)
                self.line_item_unit_cost_input.setValue(line_item.unit_cost)

                self.save_line_item_button.setEnabled(True)
                self.delete_line_item_button.setEnabled(True)
                self.add_line_item_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load line item details: {e}")
            self.clear_line_item_inputs()

    def save_line_item_changes(self):
        if self.current_line_item_id is None:
            QMessageBox.warning(self, "No Line Item Selected", "Please select a line item to save changes.")
            return

        description = self.line_item_description_input.text().strip()
        category = self.line_item_category_input.currentText()
        uom = self.line_item_uom_input.text().strip()
        quantity = self.line_item_quantity_input.value()
        unit_cost = self.line_item_unit_cost_input.value()

        if not description or not category:
            QMessageBox.warning(self, "Input Error", "Description and Category cannot be empty for a line item.")
            return

        if category in ["Overhead", "Profit", "Allowance", "Contingency"]:
            pass # Allow 0 for these categories
        elif quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Quantity and Unit Cost must be greater than zero for this category.")
            return

        try:
            line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=self.current_line_item_id).first()
            if line_item:
                line_item.line_item_description = description
                line_item.category = category
                line_item.unit_of_measure_uom = uom
                line_item.quantity = quantity
                line_item.unit_cost = unit_cost
                line_item.total_direct_cost = quantity * unit_cost # Update calculated total

                # These might be deprecated or unused if the project level calculates markups/profits
                line_item.markup_percentage = 0.0
                line_item.marked_up_unit_price = line_item.unit_cost
                line_item.total_line_item_price = line_item.total_direct_cost


                self.db_session.commit()
                QMessageBox.information(self, "Success", f"Line item '{description}' updated successfully!")
                self.clear_line_item_inputs()
                self.load_line_items_for_project(self.current_project_id) # Reload and recalculate totals
            else:
                QMessageBox.warning(self, "Error", "Selected line item not found in database.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save line item changes: {e}")

    def delete_line_item(self):
        if self.current_line_item_id is None:
            QMessageBox.warning(self, "No Line Item Selected", "Please select a line item to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                    f"Are you sure you want to delete Line Item ID: {self.current_line_item_id}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=self.current_line_item_id).first()
                if line_item:
                    self.db_session.delete(line_item)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Line item deleted successfully!")
                    self.clear_line_item_inputs()
                    self.load_line_items_for_project(self.current_project_id) # Reload and recalculate totals
                else:
                    QMessageBox.warning(self, "Error", "Selected line item not found in database.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete line item: {e}")

    def generate_project_pdf(self):
        if self.current_project_id is None:
            QMessageBox.warning(self, "No Project Selected", "Please select a project to generate a PDF.")
            return

        try:
            project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if not project:
                QMessageBox.warning(self, "Error", "Project not found for PDF generation.")
                return

            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()

            # Get filename from user
            default_filename = f"Project_Estimate_{project.project_name.replace(' ', '_')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Project Estimate PDF", default_filename, "PDF Files (*.pdf)"
            )

            if not file_path:
                return # User cancelled

            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom style for title and headers
            h1_style = ParagraphStyle(
                'h1',
                parent=styles['h1'],
                fontSize=20,
                leading=24,
                alignment=1, # TA_CENTER
                spaceAfter=12
            )
            h2_style = ParagraphStyle(
                'h2',
                parent=styles['h2'],
                fontSize=14,
                leading=16,
                spaceAfter=8
            )
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.leading = 12

            # Prepare data for PDF
            story = []

            # Project Title
            story.append(Paragraph(f"Project Estimate: {project.project_name}", h1_style))
            story.append(Spacer(1, 0.2 * inch))

            # Client Information
            story.append(Paragraph("<b>Client Information:</b>", h2_style))
            story.append(Paragraph(f"Client Name: {project.client_name}", normal_style))
            story.append(Paragraph(f"Contact Person: {getattr(project, 'client_contact_person', 'N/A')}", normal_style))
            story.append(Paragraph(f"Phone: {getattr(project, 'client_phone', 'N/A')}", normal_style))
            story.append(Paragraph(f"Email: {getattr(project, 'client_email', 'N/A')}", normal_style))
            client_address = f"{getattr(project, 'client_address_street', '')}, {getattr(project, 'client_address_city', '')}, {getattr(project, 'client_address_state', '')} {getattr(project, 'client_address_zip', '')}".strip(', ').strip()
            if client_address:
                story.append(Paragraph(f"Address: {client_address}", normal_style))
            story.append(Spacer(1, 0.1 * inch))

            # Project Information
            story.append(Paragraph("<b>Project Details:</b>", h2_style))
            story.append(Paragraph(f"Project Status: {project.project_status or 'N/A'}", normal_style))
            story.append(Paragraph(f"Contract Type: {project.contract_type or 'N/A'}", normal_style))
            project_address = f"{getattr(project, 'project_address_street', '')}, {getattr(project, 'project_address_city', '')}, {getattr(project, 'project_address_state', '')} {getattr(project, 'project_address_zip', '')}".strip(', ').strip()
            if project_address:
                story.append(Paragraph(f"Project Address: {project_address}", normal_style))
            story.append(Paragraph(f"Estimate Date: {project.estimate_date('%Y-%m-%d') if project.estimate_date else 'N/A'}", normal_style))
            story.append(Paragraph(f"Bid Due Date: {project.bid_due_date('%Y-%m-%d') if project.bid_due_date else 'N/A'}", normal_style))
            story.append(Spacer(1, 0.1 * inch))

            # Scope of Work
            if project.scope_of_work:
                story.append(Paragraph("<b>Scope of Work:</b>", h2_style))
                story.append(Paragraph(project.scope_of_work, normal_style))
                story.append(Spacer(1, 0.1 * inch))

            # Project Notes
            if project.project_notes:
                story.append(Paragraph("<b>Project Notes:</b>", h2_style))
                story.append(Paragraph(project.project_notes, normal_style))
                story.append(Spacer(1, 0.1 * inch))
            
            # Line Items Table
            story.append(Paragraph("<b>Estimate Line Items:</b>", h2_style))
            table_data = [["Description", "Category", "UoM", "Qty", "Unit Cost", "Total Direct Cost"]]
            
            for item in line_items:
                table_data.append([
                    item.line_item_description,
                    item.category,
                    item.unit_of_measure_uom,
                    f"{item.quantity:.2f}",
                    f"$ {item.unit_cost:.2f}",
                    f"$ {item.total_direct_cost:.2f}"
                ])

            # Define table style
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#C0C0C0")), # Header background
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('ALIGN', (3, 0), (-1, -1), 'RIGHT'), # Align Qty, Unit Cost, Total to right
            ])

            # Calculate column widths (approximate)
            col_widths = [2.0*inch, 1.0*inch, 0.7*inch, 0.6*inch, 0.9*inch, 1.2*inch]
            
            line_items_table_pdf = Table(table_data, colWidths=col_widths)
            line_items_table_pdf.setStyle(table_style)
            story.append(line_items_table_pdf)
            story.append(Spacer(1, 0.2 * inch))

            # Summary Totals
            total_data = [
                ["Total Direct Cost:", f"$ {self.current_project_direct_cost:,.2f}"],
                ["Markup Percentage:", f"{project.markup_percentage:.2f}%"],
                ["Total Overhead:", f"$ {self.total_overhead_label.text().split(':')[1].strip().replace('<b>','').replace('</b>','')}"], # Extract from label
                ["Total Profit:", f"$ {self.total_profit_label.text().split(':')[1].strip().replace('<b>','').replace('</b>','')}"], # Extract from label
                ["Final Project Estimate:", f"$ {self.total_final_estimate_label.text().split(':')[1].strip().replace('<b>','').replace('</b>','')}"], # Extract from label
            ]

            summary_table = Table(total_data, colWidths=[3.0*inch, 2.0*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('SPAN', (0,4), (1,4)), # Span for final estimate (if desired, adjust if you want two columns)
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,-1), (-1,-1), 12),
                ('TEXTCOLOR', (0,-1), (-1,-1), colors.green),
            ]))
            story.append(summary_table)

            doc.build(story)
            QMessageBox.information(self, "PDF Generated", f"Project estimate PDF saved to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Failed to generate PDF: {e}")
            print(f"PDF Generation Error: {e}")

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)

