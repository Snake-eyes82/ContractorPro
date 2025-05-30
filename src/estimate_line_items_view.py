# src/estimate_line_items_views.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QDoubleSpinBox, QGridLayout, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QSize

# Import your models from the updated database.py
from src.database import Session, Project, EstimateLineItem, CommonItem, CostCode
import os # Just in case for path handling, but database.py handles it

class EstimateLineItemsWindow(QMainWindow):
    # Signal emitted when line items are updated for a project (e.g., to refresh dashboard)
    project_line_items_updated_signal = Signal(int)

    def __init__(self, project_id: int, db_session=None, parent=None): # Added db_session=None
        super().__init__(parent)
        self.db_session = db_session if db_session is not None else Session()  # Initialize database session
        self.current_project_id = project_id
        self.parent = parent

        # Fetch project to get its name and financial percentages
        self.current_project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
        if not self.current_project:
            QMessageBox.critical(self, "Error", f"Project with ID {project_id} not found.")
            self.close()  # Close window if project doesn't exist
            return

        self.setWindowTitle(f"Estimate Line Items for Project ID: {self.current_project_id}")
        self.setGeometry(100, 100, 1200, 900)  # Adjusted size for better layout
        self.setMinimumSize(QSize(1000, 800))

        self.init_ui()
        self.load_common_items_and_cost_codes()  # Populate dropdowns BEFORE loading line items
        self.load_line_items()  # Load existing line items for the project
        self.update_financial_summary()  # Initial financial summary calculation

        # Connect signals for input changes to enable/disable save or trigger calculations
        self.quantity_input.valueChanged.connect(self.calculate_total_item_cost)
        self.unit_cost_input.valueChanged.connect(self.calculate_total_item_cost)
        self.common_item_combo.currentIndexChanged.connect(self.on_common_item_selected)
        self.cost_code_combo.currentIndexChanged.connect(self.on_cost_code_selected)


    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        main_layout.addWidget(QLabel(f"<h2>Estimate Line Items</h2>", alignment=Qt.AlignCenter))
        main_layout.addWidget(QLabel(f"<b>Project Name:</b> {self.current_project.project_name} | <b>Project ID:</b> {self.current_project_id}", alignment=Qt.AlignCenter))
        main_layout.addSpacing(10)

        # --- Line Item Details Group ---
        line_item_details_group = QGroupBox("Line Item Details")
        line_item_details_layout = QFormLayout(line_item_details_group)
        line_item_details_layout.setContentsMargins(10, 20, 10, 10)
        line_item_details_layout.setSpacing(8)

        # Common Item and Cost Code dropdowns
        self.common_item_combo = QComboBox()
        self.common_item_combo.addItem("-- Select Common Item --", None)
        line_item_details_layout.addRow("Common Item:", self.common_item_combo)

        self.cost_code_combo = QComboBox()
        self.cost_code_combo.addItem("-- Select Cost Code --", None)
        line_item_details_layout.addRow("Cost Code:", self.cost_code_combo)

        manage_buttons_layout = QHBoxLayout()
        self.manage_common_button = QPushButton("Manage Common Items & Cost Codes")
        self.manage_common_button.clicked.connect(self.open_manage_common_items)
        manage_buttons_layout.addStretch()
        manage_buttons_layout.addWidget(self.manage_common_button)
        manage_buttons_layout.addStretch()
        line_item_details_layout.addRow(manage_buttons_layout)

        self.description_input = QLineEdit()
        line_item_details_layout.addRow("Description:", self.description_input)

        self.category_input = QLineEdit()
        line_item_details_layout.addRow("Category:", self.category_input)

        self.uom_input = QLineEdit() # This corresponds to 'unit_of_measure_uom' in DB
        line_item_details_layout.addRow("Unit of Measure (UOM):", self.uom_input)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0.0)
        self.quantity_input.setMaximum(9999999.99)
        self.quantity_input.setSingleStep(0.01)
        self.quantity_input.setDecimals(2)
        line_item_details_layout.addRow("Quantity:", self.quantity_input)

        self.unit_cost_input = QDoubleSpinBox()
        self.unit_cost_input.setMinimum(0.0)
        self.unit_cost_input.setMaximum(9999999.99)
        self.unit_cost_input.setSingleStep(0.01)
        self.unit_cost_input.setDecimals(2)
        line_item_details_layout.addRow("Unit Cost:", self.unit_cost_input)

        self.total_item_cost_label = QLabel("$0.00")
        line_item_details_layout.addRow("Total Item Cost:", self.total_item_cost_label)

        main_layout.addWidget(line_item_details_group)

        # --- Action Buttons ---
        line_item_buttons_layout = QHBoxLayout()
        self.add_line_item_button = QPushButton("Add Line Item")
        self.add_line_item_button.clicked.connect(self.add_line_item)
        line_item_buttons_layout.addWidget(self.add_line_item_button)

        self.update_line_item_button = QPushButton("Update Line Item")
        self.update_line_item_button.clicked.connect(self.update_line_item)
        self.update_line_item_button.setEnabled(False) # Disabled until an item is selected
        line_item_buttons_layout.addWidget(self.update_line_item_button)

        self.delete_line_item_button = QPushButton("Delete Line Item")
        self.delete_line_item_button.clicked.connect(self.delete_line_item)
        self.delete_line_item_button.setEnabled(False) # Disabled until an item is selected
        line_item_buttons_layout.addWidget(self.delete_line_item_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_line_item_form)
        line_item_buttons_layout.addWidget(self.clear_form_button)

        main_layout.addLayout(line_item_buttons_layout)
        main_layout.addSpacing(10)

        # --- Line Items Table ---
        self.line_items_table = QTableWidget()
        self.line_items_table.setColumnCount(7) # ID, Description, Category, UOM, Quantity, Unit Cost, Total
        self.line_items_table.setHorizontalHeaderLabels([
            "ID", "Description", "Category", "UOM", "Quantity", "Unit Cost", "Total"
        ])
        self.line_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.line_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.line_items_table.itemSelectionChanged.connect(self.on_line_item_selected)
        main_layout.addWidget(self.line_items_table)
        main_layout.addSpacing(15)

        # --- Financial Summary Group ---
        financial_summary_group = QGroupBox("Financial Summary")
        financial_summary_layout = QFormLayout(financial_summary_group)
        financial_summary_layout.setContentsMargins(10, 20, 10, 10)
        financial_summary_layout.setSpacing(8)

        # Labels will display values from the project object, which are updated by update_financial_summary
        self.markup_percentage_label = QLabel(f"{self.current_project.markup_percentage if self.current_project and self.current_project.markup_percentage is not None else 0.0:.2f}%")
        financial_summary_layout.addRow("Markup Percentage:", self.markup_percentage_label)

        self.overhead_percentage_label = QLabel(f"{self.current_project.overhead_percentage if self.current_project and self.current_project.overhead_percentage is not None else 0.0:.2f}%")
        financial_summary_layout.addRow("Overhead Percentage:", self.overhead_percentage_label)

        self.profit_percentage_label = QLabel(f"{self.current_project.profit_percentage if self.current_project and self.current_project.profit_percentage is not None else 0.0:.2f}%")
        financial_summary_layout.addRow("Profit Percentage:", self.profit_percentage_label)

        financial_summary_layout.addRow(QLabel("<hr>")) # Separator

        self.total_direct_cost_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Direct Cost:", self.total_direct_cost_label)

        self.total_overhead_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Overhead:", self.total_overhead_label)

        self.total_profit_label = QLabel("$0.00")
        financial_summary_layout.addRow("Total Profit:", self.total_profit_label)

        self.final_project_estimate_label = QLabel("<b>$0.00</b>") # Make it bold
        financial_summary_layout.addRow("Final Project Estimate:", self.final_project_estimate_label)

        main_layout.addWidget(financial_summary_group)
        main_layout.addSpacing(15)

        # --- PDF Button ---
        pdf_button_layout = QHBoxLayout()
        pdf_button_layout.addStretch()
        self.generate_pdf_button = QPushButton("Generate PDF Estimate")
        self.generate_pdf_button.clicked.connect(self.generate_pdf_estimate)
        pdf_button_layout.addWidget(self.generate_pdf_button)
        pdf_button_layout.addStretch()
        main_layout.addLayout(pdf_button_layout)

        main_layout.addStretch(1) # Pushes everything to the top

    def load_common_items_and_cost_codes(self):
        print("DEBUG: Entering load_common_items_and_cost_codes function.")
        """Populates the Common Item and Cost Code dropdowns."""
        self.common_item_combo.clear()
        self.common_item_combo.addItem("-- Select Common Item --", None)
        try:
            common_items = self.db_session.query(CommonItem).order_by(CommonItem.name).all()
            print(f"DEBUG: Fetched {len(common_items)} common items inside function.")
            for item in common_items:
                self.common_item_combo.addItem(item.name, item) # Store the object as user data
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common items: {e}")
            print(f"DEBUG: Error loading common items in function: {e}")

        self.cost_code_combo.clear()
        self.cost_code_combo.addItem("-- Select Cost Code --", None)
        try:
            cost_codes = self.db_session.query(CostCode).order_by(CostCode.code).all()
            print(f"DEBUG: Fetched {len(cost_codes)} cost codes inside function.")
            for code in cost_codes:
                self.cost_code_combo.addItem(f"{code.code} - {code.name}", code) # Store the object as user data
        except Exception as e:
            print(f"DEBUG: Error loading cost codes in function: {e}")
            print("DEBUG: Exiting load_common_items_and_cost_codes function.")
            QMessageBox.critical(self, "Database Error", f"Failed to load cost codes: {e}")

    def on_common_item_selected(self, index):
        """Populates Description, Category, UOM based on selected Common Item."""
        if index > 0: # Skip "-- Select Common Item --"
            selected_item = self.common_item_combo.itemData(index)
            if selected_item:
                self.description_input.setText(selected_item.name)
                self.category_input.setText(selected_item.type) # Using 'type' as category
                self.uom_input.setText(selected_item.unit)
        else:
            # Clear if "Select Common Item" is chosen
            self.description_input.clear()
            self.category_input.clear()
            self.uom_input.clear()

    def on_cost_code_selected(self, index):
        """Populates Description or provides hint based on selected Cost Code."""
        if index > 0: # Skip "-- Select Cost Code --"
            selected_code = self.cost_code_combo.itemData(index)
            if selected_code:
                # You might choose to set description, or just use it internally
                if not self.description_input.text(): # Only set if description is empty
                    self.description_input.setText(selected_code.name)
        # else: no action needed if user selects "-- Select Cost Code --"

    def calculate_total_item_cost(self):
        """Calculates and displays the total cost for the current line item input."""
        try:
            quantity = self.quantity_input.value()
            unit_cost = self.unit_cost_input.value()
            total = quantity * unit_cost
            self.total_item_cost_label.setText(f"${total:.2f}")
        except Exception:
            self.total_item_cost_label.setText("$0.00")

    def load_line_items(self):
        """Loads line items from the database for the current project and populates the table."""
        self.line_items_table.setRowCount(0) # Clear existing rows
        try:
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()
            self.line_items_table.setRowCount(len(line_items))

            for row_idx, item in enumerate(line_items):
                self.line_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.line_item_id))) # Use line_item_id
                self.line_items_table.setItem(row_idx, 1, QTableWidgetItem(item.description))
                self.line_items_table.setItem(row_idx, 2, QTableWidgetItem(item.category or ""))
                self.line_items_table.setItem(row_idx, 3, QTableWidgetItem(item.unit_of_measure_uom or "")) # Use unit_of_measure_uom
                self.line_items_table.setItem(row_idx, 4, QTableWidgetItem(f"{item.quantity:.2f}"))
                self.line_items_table.setItem(row_idx, 5, QTableWidgetItem(f"${item.unit_cost:.2f}"))
                self.line_items_table.setItem(row_idx, 6, QTableWidgetItem(f"${item.total_cost:.2f}"))
            self.update_financial_summary() # Update UI summary after loading line items
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load line items: {e}")

    def clear_line_item_form(self):
        """Clears the input fields for line item details."""
        self.common_item_combo.setCurrentIndex(0)
        self.cost_code_combo.setCurrentIndex(0)
        self.description_input.clear()
        self.category_input.clear()
        self.uom_input.clear()
        self.quantity_input.setValue(0.00)
        self.unit_cost_input.setValue(0.00)
        self.total_item_cost_label.setText("$0.00")
        self.update_line_item_button.setEnabled(False)
        self.delete_line_item_button.setEnabled(False)
        self.add_line_item_button.setEnabled(True)
        self.line_items_table.clearSelection() # Clear selection in table

    def add_line_item(self):
        """Adds a new line item to the database."""
        description = self.description_input.text().strip()
        category = self.category_input.text().strip()
        uom = self.uom_input.text().strip()
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()

        if not description or quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Description, Quantity, and Unit Cost are required and must be greater than zero.")
            return

        total_cost = quantity * unit_cost
        common_item_name = self.common_item_combo.currentText() if self.common_item_combo.currentIndex() > 0 else None
        cost_code_obj = self.cost_code_combo.itemData(self.cost_code_combo.currentIndex())
        cost_code_str = cost_code_obj.code if cost_code_obj else None # Get the 'code' attribute

        try:
            new_line_item = EstimateLineItem( # Changed to EstimateLineItem
                project_id=self.current_project_id,
                description=description,
                category=category if category else None,
                unit_of_measure_uom=uom if uom else None, # Changed column name
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total_cost,
                common_item_name=common_item_name,
                cost_code=cost_code_str # Store the string code
            )
            self.db_session.add(new_line_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Line item added successfully!")
            self.clear_line_item_form()
            self.load_line_items() # Reload table to show new item
            self.update_financial_summary(save_to_project=True) # Recalculate and save to project
            self.project_line_items_updated_signal.emit(self.current_project_id) # Notify dashboard
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add line item: {e}")

    def on_line_item_selected(self):
        """When a line item in the table is selected, populate the input fields."""
        selected_rows = self.line_items_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            line_item_id = int(self.line_items_table.item(row, 0).text())
            line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=line_item_id).first() # Use line_item_id

            if line_item:
                # Populate inputs
                self.description_input.setText(line_item.description)
                self.category_input.setText(line_item.category or "")
                self.uom_input.setText(line_item.unit_of_measure_uom or "") # Changed column name
                self.quantity_input.setValue(line_item.quantity)
                self.unit_cost_input.setValue(line_item.unit_cost)
                self.total_item_cost_label.setText(f"${line_item.total_cost:.2f}")

                # Set common item combo box
                if line_item.common_item_name:
                    idx = self.common_item_combo.findText(line_item.common_item_name)
                    if idx != -1:
                        self.common_item_combo.setCurrentIndex(idx)
                    else:
                        self.common_item_combo.setCurrentIndex(0) # Not found, reset
                else:
                    self.common_item_combo.setCurrentIndex(0)

                # Set cost code combo box
                if line_item.cost_code:
                    # Find by cost code string (e.g., "03 30 00"). Iterate to find data.
                    found_idx = -1
                    for i in range(self.cost_code_combo.count()):
                        item_data = self.cost_code_combo.itemData(i)
                        if item_data and item_data.code == line_item.cost_code:
                            found_idx = i
                            break
                    self.cost_code_combo.setCurrentIndex(found_idx if found_idx != -1 else 0)
                else:
                    self.cost_code_combo.setCurrentIndex(0)

                # Enable update/delete buttons
                self.update_line_item_button.setEnabled(True)
                self.delete_line_item_button.setEnabled(True)
                self.add_line_item_button.setEnabled(False) # Disable add while updating
        else:
            self.clear_line_item_form() # Clear if selection is removed

    def update_line_item(self):
        """Updates an existing line item in the database."""
        selected_rows = self.line_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a line item to update.")
            return

        row = selected_rows[0].row()
        line_item_id = int(self.line_items_table.item(row, 0).text())

        description = self.description_input.text().strip()
        category = self.category_input.text().strip()
        uom = self.uom_input.text().strip()
        quantity = self.quantity_input.value()
        unit_cost = self.unit_cost_input.value()

        if not description or quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Description, Quantity, and Unit Cost are required and must be greater than zero.")
            return

        total_cost = quantity * unit_cost
        common_item_name = self.common_item_combo.currentText() if self.common_item_combo.currentIndex() > 0 else None
        cost_code_obj = self.cost_code_combo.itemData(self.cost_code_combo.currentIndex())
        cost_code_str = cost_code_obj.code if cost_code_obj else None


        try:
            line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=line_item_id, project_id=self.current_project_id).first() # Use line_item_id
            if line_item:
                line_item.description = description
                line_item.category = category if category else None
                line_item.unit_of_measure_uom = uom if uom else None # Changed column name
                line_item.quantity = quantity
                line_item.unit_cost = unit_cost
                line_item.total_cost = total_cost
                line_item.common_item_name = common_item_name
                line_item.cost_code = cost_code_str
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Line item updated successfully!")
                self.clear_line_item_form()
                self.load_line_items() # Reload table
                self.update_financial_summary(save_to_project=True) # Recalculate and save to project
                self.project_line_items_updated_signal.emit(self.current_project_id) # Notify dashboard
            else:
                QMessageBox.warning(self, "Error", "Selected line item not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update line item: {e}")

    def delete_line_item(self):
        """Deletes a selected line item from the database."""
        selected_rows = self.line_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a line item to delete.")
            return

        row = selected_rows[0].row()
        line_item_id = int(self.line_items_table.item(row, 0).text())

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete line item ID {line_item_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                line_item = self.db_session.query(EstimateLineItem).filter_by(line_item_id=line_item_id, project_id=self.current_project_id).first() # Use line_item_id
                if line_item:
                    self.db_session.delete(line_item)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Line item deleted successfully!")
                    self.clear_line_item_form()
                    self.load_line_items() # Reload table
                    self.update_financial_summary(save_to_project=True) # Recalculate and save to project
                    self.project_line_items_updated_signal.emit(self.current_project_id) # Notify dashboard
                else:
                    QMessageBox.warning(self, "Error", "Selected line item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete line item: {e}")

    def update_financial_summary(self, save_to_project=False):
        """
        Calculates and updates the financial summary based on line items and project percentages.
        Optionally saves these calculated totals back to the Project object in the database.
        """
        total_direct_cost = 0.0
        try:
            line_items = self.db_session.query(EstimateLineItem).filter_by(project_id=self.current_project_id).all()
            for item in line_items:
                total_direct_cost += item.total_cost
        except Exception as e:
            print(f"Error calculating total direct cost: {e}") # Log error, but don't stop UI

        # Fetch latest project percentages (in case they were changed in General Info)
        # Re-querying self.current_project to ensure latest percentages are used
        self.current_project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
        if not self.current_project:
            QMessageBox.critical(self, "Error", "Project not found for financial summary calculation.")
            return

        markup_percentage = self.current_project.markup_percentage if self.current_project.markup_percentage is not None else 0.0
        overhead_percentage = self.current_project.overhead_percentage if self.current_project.overhead_percentage is not None else 0.0
        profit_percentage = self.current_project.profit_percentage if self.current_project.profit_percentage is not None else 0.0

        total_overhead = total_direct_cost * (overhead_percentage / 100.0)
        cost_plus_overhead = total_direct_cost + total_overhead
        total_profit = cost_plus_overhead * (profit_percentage / 100.0)
        final_estimate = cost_plus_overhead + total_profit

        # Update labels in UI
        self.markup_percentage_label.setText(f"{markup_percentage:.2f}%")
        self.overhead_percentage_label.setText(f"{overhead_percentage:.2f}%")
        self.profit_percentage_label.setText(f"{profit_percentage:.2f}%")
        self.total_direct_cost_label.setText(f"${total_direct_cost:.2f}")
        self.total_overhead_label.setText(f"${total_overhead:.2f}")
        self.total_profit_label.setText(f"${total_profit:.2f}")
        self.final_project_estimate_label.setText(f"<b>${final_estimate:.2f}</b>")

        # Optionally save calculated totals back to the Project table
        if save_to_project:
            try:
                self.current_project.total_direct_cost = total_direct_cost
                self.current_project.total_overhead = total_overhead
                self.current_project.total_profit = total_profit
                self.current_project.final_project_estimate = final_estimate
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                print(f"Error saving financial summary to project: {e}")

    def open_manage_common_items(self):
        """Opens the Manage Common Items & Cost Codes window."""
        try:
            from src.manage_common_data_view import ManageCommonDataWindow
            self.manage_data_window = ManageCommonDataWindow(parent=self)
            # Connect signal to reload common items/cost codes in this window
            self.manage_data_window.data_updated_signal.connect(self.load_common_items_and_cost_codes)
            self.manage_data_window.show()
        except ImportError:
            QMessageBox.critical(self, "Error", "ManageCommonDataWindow class not found. Please ensure 'manage_common_data_view.py' exists and is correctly defined.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Common Items/Cost Codes: {e}")

    def generate_pdf_estimate(self):
        """Placeholder for generating PDF estimate."""
        QMessageBox.information(self, "Under Construction", "PDF generation feature is not yet implemented.")

    def closeEvent(self, event):
        """Clean up database session when the window is closed."""
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)

