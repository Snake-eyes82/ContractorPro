# src/estimate_line_items_view.py (Comprehensive Update)
import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QComboBox, QGridLayout, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize

# Import new components for common items and cost codes
from src.database import SessionLocal, Project, EstimateLineItem, CommonItem, CostCode, get_all_common_items, get_all_cost_codes
from src.data_management_window import DataManagementWindow # Import the new window

# Import for PDF generation
from src.pdf_generator import generate_project_estimate_pdf # Ensure this import path is correct

class EstimateLineItemsWindow(QMainWindow):
    project_updated_signal = Signal() # Declare the signal here

    def __init__(self, project_id: int, parent=None):
        super().__init__(parent)
        self.db_session = SessionLocal() # Use SessionLocal for consistency
        self.current_project_id = project_id
        self.project = None # To store the loaded Project object
        self.load_project_data() # Load project details including percentages

        self.setWindowTitle(f"Estimate Line Items for Project ID: {self.current_project_id}")
        self.setGeometry(100, 100, 1200, 800) # Increased size for better layout
        self.setMinimumSize(QSize(1000, 700))

        self.init_ui()
        self.load_line_items()
        self.calculate_financial_summary() # Initial calculation after loading line items
        self.populate_common_items_combo() # Populate on startup
        self.populate_cost_codes_combo()   # Populate on startup

    def load_project_data(self):
        """Loads the associated Project details, including percentages."""
        try:
            self.project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if not self.project:
                QMessageBox.critical(self, "Error", f"Project with ID {self.current_project_id} not found.")
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

        # Common Item Dropdown
        self.common_item_combo = QComboBox()
        self.common_item_combo.setPlaceholderText("Select a Common Item or type below")
        self.common_item_combo.setEditable(False) # Not editable for selection, but can type in description directly
        self.common_item_combo.currentIndexChanged.connect(self.load_common_item_details)
        input_form_layout.addRow("Common Item:", self.common_item_combo)

        # Cost Code Dropdown
        self.cost_code_combo = QComboBox()
        self.cost_code_combo.setPlaceholderText("Select a Cost Code or type below")
        self.cost_code_combo.setEditable(False) # Not editable for selection
        input_form_layout.addRow("Cost Code:", self.cost_code_combo)

        # Button to open Data Management Window
        self.manage_data_button = QPushButton("Manage Common Items & Cost Codes")
        self.manage_data_button.clicked.connect(self.open_data_management_window)
        input_form_layout.addRow("", self.manage_data_button) # Empty label to place button across form

        self.description_input = QLineEdit()
        input_form_layout.addRow("Description:", self.description_input)

        self.category_input = QLineEdit() # This will be auto-filled by CommonItem's 'type'
        self.category_input.setReadOnly(True) # Make it read-only
        input_form_layout.addRow("Category:", self.category_input)

        self.uom_input = QLineEdit() # Unit of Measure, auto-filled by CommonItem
        self.uom_input.setReadOnly(True) # Make it read-only
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
        # Updated columns to include CommonItem ID and CostCode ID
        self.line_items_table.setColumnCount(9) # ID, Desc, CommonItemID, CostCodeID, Category, UOM, Qty, Unit Cost, Total
        self.line_items_table.setHorizontalHeaderLabels([
            "ID", "Description", "CommonItem ID", "CostCode ID", "Category", "UOM", "Quantity", "Unit Cost", "Total"
        ])
        # Hide the ID columns for CommonItem ID and CostCode ID from user view
        self.line_items_table.setColumnHidden(2, True) # CommonItem ID
        self.line_items_table.setColumnHidden(3, True) # CostCode ID

        self.line_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Set specific resize mode for description
        self.line_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Description
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.line_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.line_items_table.itemSelectionChanged.connect(self.load_selected_line_item)
        main_layout.addWidget(self.line_items_table)

        # --- Financial Summary Section ---
        financial_summary_group = QGroupBox("Financial Summary")
        financial_summary_layout = QFormLayout(financial_summary_group)
        financial_summary_layout.setContentsMargins(10, 20, 10, 10)
        financial_summary_layout.setSpacing(8)

        self.markup_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Markup Percentage:", self.markup_percentage_label)

        self.overhead_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Overhead Percentage:", self.overhead_percentage_label)

        self.profit_percentage_label = QLabel("0.00%")
        financial_summary_layout.addRow("Profit Percentage:", self.profit_percentage_label)

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

    def populate_common_items_combo(self):
        """Populates the Common Item QComboBox."""
        self.common_item_combo.clear()
        self.common_item_combo.addItem("--- Select Common Item ---", userData=None) # Add a default "empty" option
        try:
            items = get_all_common_items(self.db_session)
            for item in items:
                self.common_item_combo.addItem(f"{item.item_name} ({item.item_type})", userData=item.item_id)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common items for dropdown: {e}")

    def populate_cost_codes_combo(self):
        """Populates the Cost Code QComboBox."""
        self.cost_code_combo.clear()
        self.cost_code_combo.addItem("--- Select Cost Code ---", userData=None) # Add a default "empty" option
        try:
            codes = get_all_cost_codes(self.db_session)
            for code in codes:
                self.cost_code_combo.addItem(f"{code.code} - {code.name}", userData=code.cost_code_id)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load cost codes for dropdown: {e}")

    def load_common_item_details(self, index):
        """
        Loads details of the selected Common Item into the form fields.
        Connected to common_item_combo's currentIndexChanged signal.
        """
        item_id = self.common_item_combo.itemData(index)
        if item_id is None: # "--- Select Common Item ---" option
            self.description_input.clear()
            self.category_input.clear()
            self.uom_input.clear()
            # Don't clear quantity or unit cost
            return

        try:
            item = self.db_session.query(CommonItem).filter(CommonItem.item_id == item_id).first()
            if item:
                self.description_input.setText(item.item_name) # Common item name becomes description
                self.category_input.setText(item.item_type)    # Common item type becomes category
                self.uom_input.setText(item.item_unit)         # Common item unit becomes UOM
                # You might want to pre-fill a default unit cost here if CommonItem had one.
                # For now, leaving unit_cost_input as is.
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common item details: {e}")

    def open_data_management_window(self):
        """Opens the DataManagementWindow."""
        self.data_management_win = DataManagementWindow(self)
        self.data_management_win.data_updated.connect(self.handle_data_management_update)
        self.data_management_win.exec() # Use exec() for modal dialog

    def handle_data_management_update(self):
        """Refreshes common item and cost code dropdowns after data management window closes."""
        self.populate_common_items_combo()
        self.populate_cost_codes_combo()
        self.clear_form_inputs() # Clear form after updates

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
            # Eager load CommonItem and CostCode if they exist for display
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()
            for row_idx, item in enumerate(line_items):
                self.line_items_table.insertRow(row_idx)
                self.line_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.line_item_id)))
                self.line_items_table.setItem(row_idx, 1, QTableWidgetItem(item.description))

                # Store CommonItem ID and CostCode ID in hidden columns
                self.line_items_table.setItem(row_idx, 2, QTableWidgetItem(str(item.common_item_id) if item.common_item_id else ""))
                self.line_items_table.setItem(row_idx, 3, QTableWidgetItem(str(item.cost_code_id) if item.cost_code_id else ""))

                self.line_items_table.setItem(row_idx, 4, QTableWidgetItem(item.category or "")) # Handle None
                self.line_items_table.setItem(row_idx, 5, QTableWidgetItem(item.unit_of_measure_uom or "")) # Handle None
                self.line_items_table.setItem(row_idx, 6, QTableWidgetItem(f"{item.quantity:.2f}"))
                self.line_items_table.setItem(row_idx, 7, QTableWidgetItem(f"${item.unit_cost:.2f}"))
                self.line_items_table.setItem(row_idx, 8, QTableWidgetItem(f"${item.total_cost:.2f}"))
            self.calculate_financial_summary() # Recalculate after loading
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load line items: {e}")

    def add_line_item(self):
        description = self.description_input.text().strip()
        # Category and UOM are now pulled from the read-only fields
        category = self.category_input.text().strip()
        uom = self.uom_input.text().strip()
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()
        total_cost = quantity * unit_cost

        # Get selected common_item_id and cost_code_id
        selected_common_item_id = self.common_item_combo.currentData()
        selected_cost_code_id = self.cost_code_combo.currentData()

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
                total_cost=total_cost,
                common_item_id=selected_common_item_id, # Save the ID
                cost_code_id=selected_cost_code_id      # Save the ID
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

        selected_common_item_id = self.common_item_combo.currentData()
        selected_cost_code_id = self.cost_code_combo.currentData()

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
                item_to_update.common_item_id = selected_common_item_id # Update the ID
                item_to_update.cost_code_id = selected_cost_code_id      # Update the ID
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
        """Loads data from the selected table row into the input fields, including Common Item and Cost Code."""
        selected_rows = self.line_items_table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            self.description_input.setText(self.line_items_table.item(row, 1).text())
            
            # Load Common Item and Cost Code from hidden columns and set combo boxes
            common_item_id_str = self.line_items_table.item(row, 2).text()
            cost_code_id_str = self.line_items_table.item(row, 3).text()

            # Find and set Common Item combo box
            common_item_found = False
            if common_item_id_str:
                common_item_id = int(common_item_id_str)
                for i in range(self.common_item_combo.count()):
                    if self.common_item_combo.itemData(i) == common_item_id:
                        self.common_item_combo.setCurrentIndex(i)
                        common_item_found = True
                        break
            if not common_item_found:
                self.common_item_combo.setCurrentIndex(0) # Select "--- Select Common Item ---"

            # Find and set Cost Code combo box
            cost_code_found = False
            if cost_code_id_str:
                cost_code_id = int(cost_code_id_str)
                for i in range(self.cost_code_combo.count()):
                    if self.cost_code_combo.itemData(i) == cost_code_id:
                        self.cost_code_combo.setCurrentIndex(i)
                        cost_code_found = True
                        break
            if not cost_code_found:
                self.cost_code_combo.setCurrentIndex(0) # Select "--- Select Cost Code ---"

            self.category_input.setText(self.line_items_table.item(row, 4).text())
            self.uom_input.setText(self.line_items_table.item(row, 5).text())
            self.quantity_input.setValue(float(self.line_items_table.item(row, 6).text()))
            self.unit_cost_input.setValue(float(self.line_items_table.item(row, 7).text().replace('$', ''))) # Remove $
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
        self.common_item_combo.setCurrentIndex(0) # Reset common item combo
        self.cost_code_combo.setCurrentIndex(0)   # Reset cost code combo
        self.description_input.clear()
        self.category_input.clear() # Auto-filled, clear it
        self.uom_input.clear()      # Auto-filled, clear it
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
        for row in range(self.line_items_table.rowCount()):
            # Use the correct column for total_cost based on updated column count
            item_total_str = self.line_items_table.item(row, 8).text().replace('$', '')
            try:
                total_direct_cost += float(item_total_str)
            except ValueError:
                pass

        self.total_direct_cost_label.setText(f"${total_direct_cost:.2f}")

        markup_percent = self.project.markup_percentage if self.project and self.project.markup_percentage is not None else 0.0
        overhead_percent = self.project.overhead_percentage if self.project and self.project.overhead_percentage is not None else 0.0
        profit_percent = self.project.profit_percentage if self.project and self.project.profit_percentage is not None else 0.0

        self.markup_percentage_label.setText(f"{markup_percent:.2f}%")
        self.overhead_percentage_label.setText(f"{overhead_percent:.2f}%")
        self.profit_percentage_label.setText(f"{profit_percent:.2f}%")

        total_overhead = total_direct_cost * (overhead_percent / 100.0)
        total_profit = (total_direct_cost + total_overhead) * (profit_percent / 100.0)

        self.total_overhead_label.setText(f"${total_overhead:.2f}")
        self.total_profit_label.setText(f"${total_profit:.2f}")

        final_project_estimate_internal = total_direct_cost + total_overhead + total_profit
        self.final_project_estimate_label.setText(f"<font color='blue' size='5'>${final_project_estimate_internal:.2f}</font>")

    def generate_estimate_pdf(self):
        """Generates a PDF estimate based on current project data and line items."""
        if not self.project:
            QMessageBox.warning(self, "Error", "No project data available to generate PDF.")
            return

        project_data = {
            "project_name": self.project.project_name,
            "project_id": self.project.project_id,
            "client_name": self.project.client_name,
            "client_contact": self.project.client_contact,
            "client_phone": self.project.client_phone,
            "client_email": self.project.client_email,
            "client_address_street": self.project.client_address_street,
            "client_address_city": self.project.client_address_city,
            "client_address_state": self.project.client_address_state,
            "client_address_zip": self.project.client_address_zip,
            "project_address_street": self.project.project_address_street,
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
            # Ensure correct column indices for data extraction
            line_items_data.append({
                "line_item_id": int(self.line_items_table.item(row, 0).text()),
                "description": self.line_items_table.item(row, 1).text(),
                "common_item_id": int(self.line_items_table.item(row, 2).text()) if self.line_items_table.item(row, 2).text() else None,
                "cost_code_id": int(self.line_items_table.item(row, 3).text()) if self.line_items_table.item(row, 3).text() else None,
                "category": self.line_items_table.item(row, 4).text(),
                "unit_of_measure_uom": self.line_items_table.item(row, 5).text(),
                "quantity": float(self.line_items_table.item(row, 6).text()),
                "unit_cost": float(self.line_items_table.item(row, 7).text().replace('$', '')),
                "total_cost": float(self.line_items_table.item(row, 8).text().replace('$', ''))
            })

        project_name_safe = "".join([c if c.isalnum() or c in (' ', '_', '-') else '' for c in project_data["project_name"]]).strip()
        default_filename = f"Estimate_{project_name_safe.replace(' ', '_')}_{project_data['project_id']}.pdf"

        output_filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project Estimate PDF",
            default_filename,
            "PDF Files (*.pdf);;All Files (*)"
        )

        logo_path = None # Set to None for now, or provide a test logo path if you have one.

        if output_filename: # Only proceed if user selected a filename
            try:
                success = generate_project_estimate_pdf(
                    project_data,
                    line_items_data,
                    output_filename,
                    logo_path
                )

                if success:
                    QMessageBox.information(self, "PDF Generated", f"Project Estimate PDF saved as:\n{output_filename}")
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