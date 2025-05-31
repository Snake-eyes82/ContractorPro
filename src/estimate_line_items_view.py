# src/estimate_line_items_view.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QDoubleSpinBox, QComboBox, QFormLayout, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from sqlalchemy import func
from src.database import Session, Project, LineItem, CommonItem, CostCode, create_db_and_tables

class EstimateLineItemsWindow(QMainWindow):
    # Signal to update total costs in the main dashboard or general info
    project_costs_updated_signal = Signal()

    def __init__(self, project_id, db_session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.current_project_id = project_id

        # CORRECTED: Filter by 'id' not 'project_id' for the Project model
        self.current_project = self.db_session.query(Project).filter_by(id=self.current_project_id).first()

        if not self.current_project:
            QMessageBox.critical(self, "Error", "Project not found!")
            self.close()
            return

        self.setWindowTitle(f"Line Items for Project: {self.current_project.project_name}")
        self.setGeometry(150, 150, 1000, 700)
        self.setMinimumSize(QSize(900, 600))

        self.common_items_data = self.get_common_items()
        self.cost_codes_data = self.get_cost_codes()

        self.init_ui()
        self.load_line_items()
        self.calculate_and_display_totals()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Totals Display
        self.totals_label = QLabel("Total Direct Cost: $0.00 | Final Estimate: $0.00", alignment=Qt.AlignRight)
        main_layout.addWidget(self.totals_label)

        # Line Items Table
        self.line_items_table = QTableWidget()
        self.line_items_table.setColumnCount(8)
        self.line_items_table.setHorizontalHeaderLabels([
            "ID", "Description", "Quantity", "Unit", "Unit Cost", "Markup %", "Total Cost", "Notes"
        ])
        self.line_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.line_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.line_items_table.itemSelectionChanged.connect(self.on_line_item_selection_changed)
        main_layout.addWidget(self.line_items_table)

        # Line Item Input Form
        input_layout = QFormLayout()

        self.description_input = QLineEdit()
        input_layout.addRow("Description:", self.description_input)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 999999999.99)
        self.quantity_input.setDecimals(2)
        input_layout.addRow("Quantity:", self.quantity_input)

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("e.g., EA, LF, SQFT, HR")
        input_layout.addRow("Unit:", self.unit_input)

        self.unit_cost_input = QDoubleSpinBox()
        self.unit_cost_input.setRange(0.01, 999999999.99)
        self.unit_cost_input.setPrefix("$")
        self.unit_cost_input.setDecimals(2)
        input_layout.addRow("Unit Cost:", self.unit_cost_input)

        self.markup_percentage_input = QDoubleSpinBox()
        self.markup_percentage_input.setRange(0.00, 100.00)
        self.markup_percentage_input.setSuffix("%")
        self.markup_percentage_input.setDecimals(2)
        input_layout.addRow("Markup %:", self.markup_percentage_input)

        self.is_common_item_checkbox = QComboBox()
        self.is_common_item_checkbox.addItems(["Custom Item", "Common Item"])
        self.is_common_item_checkbox.currentIndexChanged.connect(self.toggle_common_item_fields)
        input_layout.addRow("Item Type:", self.is_common_item_checkbox)

        self.common_item_combo = QComboBox()
        self.common_item_combo.setPlaceholderText("Select Common Item")
        # Populate with common items
        self.common_item_map = {item.name: item for item in self.common_items_data}
        self.common_item_combo.addItem("-- Select Common Item --")
        self.common_item_combo.addItems(sorted(self.common_item_map.keys()))
        self.common_item_combo.currentIndexChanged.connect(self.load_common_item_data)
        self.common_item_combo.setEnabled(False) # Initially disabled
        input_layout.addRow("Select Common Item:", self.common_item_combo)

        self.cost_code_combo = QComboBox()
        self.cost_code_combo.setPlaceholderText("Select Cost Code")
        # Populate with cost codes
        self.cost_code_map = {f"{code.code} - {code.name}": code for code in self.cost_codes_data}
        self.cost_code_combo.addItem("-- Select Cost Code --")
        self.cost_code_combo.addItems(sorted(self.cost_code_map.keys()))
        input_layout.addRow("Cost Code:", self.cost_code_combo)


        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes for this line item...")
        input_layout.addRow("Notes:", self.notes_input)

        main_layout.addLayout(input_layout)

        # Buttons for Line Item Management
        button_layout = QHBoxLayout()
        self.add_line_item_button = QPushButton("Add Line Item")
        self.add_line_item_button.clicked.connect(self.add_or_update_line_item)
        button_layout.addWidget(self.add_line_item_button)

        self.update_line_item_button = QPushButton("Update Selected")
        self.update_line_item_button.clicked.connect(self.add_or_update_line_item)
        self.update_line_item_button.setEnabled(False)
        button_layout.addWidget(self.update_line_item_button)

        self.delete_line_item_button = QPushButton("Delete Selected")
        self.delete_line_item_button.clicked.connect(self.delete_line_item)
        self.delete_line_item_button.setEnabled(False)
        button_layout.addWidget(self.delete_line_item_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_form_button)

        main_layout.addLayout(button_layout)

    def get_common_items(self):
        return self.db_session.query(CommonItem).order_by(CommonItem.name).all()

    def get_cost_codes(self):
        return self.db_session.query(CostCode).order_by(CostCode.code).all()

    def toggle_common_item_fields(self, index):
        # 0 is Custom Item, 1 is Common Item
        is_common = (index == 1)
        self.common_item_combo.setEnabled(is_common)
        self.description_input.setReadOnly(is_common) # Description becomes read-only if common item
        self.unit_input.setReadOnly(is_common) # Unit becomes read-only if common item
        self.unit_cost_input.setReadOnly(is_common) # Unit Cost becomes read-only if common item

        if not is_common:
            self.common_item_combo.setCurrentIndex(0) # Reset selection
            # Clear fields if switching from common to custom
            # (only if they were populated by a common item previously)
            if self.sender() == self.is_common_item_checkbox: # Only clear if user changed it
                self.description_input.clear()
                self.unit_input.clear()
                self.unit_cost_input.setValue(0.0)

    def load_common_item_data(self, index):
        if index > 0: # Skip "Select Common Item"
            selected_name = self.common_item_combo.currentText()
            item = self.common_item_map.get(selected_name)
            if item:
                self.description_input.setText(item.description or item.name)
                self.unit_input.setText(item.unit or "")
                # Assuming common items have a default unit_cost or it's set by user later
                # For now, we won't populate unit_cost from common item as it varies by project
                # self.unit_cost_input.setValue(item.default_cost) # If you add a default_cost to CommonItem
                
                # Try to pre-select cost code if mf_code exists and matches
                if item.mf_code:
                    for i in range(self.cost_code_combo.count()):
                        if self.cost_code_combo.itemText(i).startswith(item.mf_code.split(" ")[0]): # Match by main division
                            self.cost_code_combo.setCurrentIndex(i)
                            break
        elif index == 0 and self.is_common_item_checkbox.currentIndex() == 1:
             # If "Select Common Item" is chosen while Common Item type is selected, clear fields
            self.description_input.clear()
            self.unit_input.clear()
            self.unit_cost_input.setValue(0.0)

    def load_line_items(self):
        self.line_items_table.setRowCount(0)
        line_items = self.db_session.query(LineItem).filter_by(project_id=self.current_project_id).all()
        self.line_items_table.setRowCount(len(line_items))

        for row_idx, item in enumerate(line_items):
            total_cost = item.quantity * item.unit_cost * (1 + item.markup_percentage / 100)
            self.line_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.id)))
            self.line_items_table.setItem(row_idx, 1, QTableWidgetItem(item.description or ""))
            self.line_items_table.setItem(row_idx, 2, QTableWidgetItem(f"{item.quantity:.2f}"))
            self.line_items_table.setItem(row_idx, 3, QTableWidgetItem(item.unit or ""))
            self.line_items_table.setItem(row_idx, 4, QTableWidgetItem(f"${item.unit_cost:.2f}"))
            self.line_items_table.setItem(row_idx, 5, QTableWidgetItem(f"{item.markup_percentage:.2f}%"))
            self.line_items_table.setItem(row_idx, 6, QTableWidgetItem(f"${total_cost:.2f}"))
            self.line_items_table.setItem(row_idx, 7, QTableWidgetItem(item.notes or ""))
            # Store full LineItem object for easier access on selection
            self.line_items_table.item(row_idx, 0).setData(Qt.UserRole, item)

    def calculate_and_display_totals(self):
        # Recalculate total_direct_cost and final_project_estimate for the project
        total_direct_cost = self.db_session.query(func.sum(LineItem.quantity * LineItem.unit_cost)).filter_by(project_id=self.current_project_id).scalar() or 0.0
        
        # Calculate total cost with markup for all line items
        total_cost_with_markup = self.db_session.query(
            func.sum(LineItem.quantity * LineItem.unit_cost * (1 + LineItem.markup_percentage / 100))
        ).filter_by(project_id=self.current_project_id).scalar() or 0.0

        # Ensure current_project is fresh for percentage calculations
        self.db_session.refresh(self.current_project)

        overhead_percentage = self.current_project.overhead_percentage if self.current_project.overhead_percentage is not None else 0.0
        profit_percentage = self.current_project.profit_percentage if self.current_project.profit_percentage is not None else 0.0

        overhead_amount = total_cost_with_markup * (overhead_percentage / 100)
        profit_amount = total_cost_with_markup * (profit_percentage / 100)

        # Include fixed costs from Project model
        permit_cost = self.current_project.permit_cost if self.current_project.permit_cost is not None else 0.0
        bonding_cost = self.current_project.bonding_cost if self.current_project.bonding_cost is not None else 0.0
        insurance_cost = self.current_project.insurance_cost if self.current_project.insurance_cost is not None else 0.0
        misc_expenses = self.current_project.misc_expenses if self.current_project.misc_expenses is not None else 0.0

        final_project_estimate = (
            total_cost_with_markup + 
            overhead_amount + 
            profit_amount + 
            permit_cost + 
            bonding_cost + 
            insurance_cost + 
            misc_expenses
        )

        # Update project object in DB
        self.current_project.total_direct_cost = total_direct_cost
        self.current_project.final_project_estimate = final_project_estimate
        self.db_session.commit()

        self.totals_label.setText(f"Total Direct Cost: ${total_direct_cost:.2f} | Final Estimate: ${final_project_estimate:.2f}")
        self.project_costs_updated_signal.emit() # Notify dashboard to refresh totals

    def on_line_item_selection_changed(self):
        selected_rows = self.line_items_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            selected_line_item = self.line_items_table.item(row, 0).data(Qt.UserRole)
            if selected_line_item:
                self.description_input.setText(selected_line_item.description or "")
                self.quantity_input.setValue(selected_line_item.quantity)
                self.unit_input.setText(selected_line_item.unit or "")
                self.unit_cost_input.setValue(selected_line_item.unit_cost)
                self.markup_percentage_input.setValue(selected_line_item.markup_percentage)
                self.notes_input.setText(selected_line_item.notes or "")

                # Set common item checkbox and combo
                if selected_line_item.is_common_item == 1 and selected_line_item.common_item:
                    self.is_common_item_checkbox.setCurrentIndex(1) # Common Item
                    common_item_name = selected_line_item.common_item.name
                    index = self.common_item_combo.findText(common_item_name)
                    if index != -1:
                        self.common_item_combo.setCurrentIndex(index)
                    self.description_input.setReadOnly(True)
                    self.unit_input.setReadOnly(True)
                    self.unit_cost_input.setReadOnly(True)
                else:
                    self.is_common_item_checkbox.setCurrentIndex(0) # Custom Item
                    self.common_item_combo.setCurrentIndex(0) # Reset combo
                    self.description_input.setReadOnly(False)
                    self.unit_input.setReadOnly(False)
                    self.unit_cost_input.setReadOnly(False)
                
                # Set cost code combo
                if selected_line_item.cost_code:
                    cost_code_text = f"{selected_line_item.cost_code.code} - {selected_line_item.cost_code.name}"
                    index = self.cost_code_combo.findText(cost_code_text)
                    if index != -1:
                        self.cost_code_combo.setCurrentIndex(index)
                    else:
                        self.cost_code_combo.setCurrentIndex(0) # Reset if not found
                else:
                    self.cost_code_combo.setCurrentIndex(0)


                self.add_line_item_button.setEnabled(False)
                self.update_line_item_button.setEnabled(True)
                self.delete_line_item_button.setEnabled(True)
        else:
            self.clear_form()
            self.add_line_item_button.setEnabled(True)
            self.update_line_item_button.setEnabled(False)
            self.delete_line_item_button.setEnabled(False)

    def add_or_update_line_item(self):
        description = self.description_input.text().strip()
        quantity = self.quantity_input.value()
        unit = self.unit_input.text().strip()
        unit_cost = self.unit_cost_input.value()
        markup_percentage = self.markup_percentage_input.value()
        notes = self.notes_input.toPlainText().strip()
        is_common = self.is_common_item_checkbox.currentIndex() == 1 # 1 means Common Item
        
        selected_common_item = None
        if is_common:
            common_item_name = self.common_item_combo.currentText()
            if common_item_name == "-- Select Common Item --":
                QMessageBox.warning(self, "Input Error", "Please select a Common Item or switch to Custom Item.")
                return
            selected_common_item = self.common_item_map.get(common_item_name)
            if not selected_common_item:
                QMessageBox.critical(self, "Error", "Selected Common Item not found.")
                return
            # If it's a common item, use its description/name, unit. Unit cost is user-defined for line item.
            description = selected_common_item.description or selected_common_item.name
            unit = selected_common_item.unit or ""
        
        selected_cost_code = None
        cost_code_text = self.cost_code_combo.currentText()
        if cost_code_text != "-- Select Cost Code --":
            selected_cost_code = self.cost_code_map.get(cost_code_text)
            if not selected_cost_code:
                QMessageBox.critical(self, "Error", "Selected Cost Code not found.")
                return

        if not description or quantity <= 0 or unit_cost <= 0:
            QMessageBox.warning(self, "Input Error", "Description, Quantity, and Unit Cost are required and must be positive.")
            return

        try:
            line_item_id = None
            selected_rows = self.line_items_table.selectionModel().selectedRows()
            if selected_rows and self.update_line_item_button.isEnabled(): # Check if update mode
                row = selected_rows[0].row()
                line_item_id = int(self.line_items_table.item(row, 0).text())
                item_to_update = self.db_session.query(LineItem).filter_by(id=line_item_id).first()
                if item_to_update:
                    item_to_update.description = description
                    item_to_update.quantity = quantity
                    item_to_update.unit = unit
                    item_to_update.unit_cost = unit_cost
                    item_to_update.markup_percentage = markup_percentage
                    item_to_update.notes = notes
                    item_to_update.is_common_item = 1 if is_common else 0
                    item_to_update.common_item_id = selected_common_item.id if selected_common_item else None
                    item_to_update.cost_code_id = selected_cost_code.id if selected_cost_code else None
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Line item updated.")
                else:
                    QMessageBox.critical(self, "Error", "Line item not found for update.")
            else: # Add new
                new_line_item = LineItem(
                    project_id=self.current_project_id,
                    description=description,
                    quantity=quantity,
                    unit=unit,
                    unit_cost=unit_cost,
                    markup_percentage=markup_percentage,
                    notes=notes,
                    is_common_item=1 if is_common else 0,
                    common_item_id=selected_common_item.id if selected_common_item else None,
                    cost_code_id=selected_cost_code.id if selected_cost_code else None
                )
                self.db_session.add(new_line_item)
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Line item added.")

            self.load_line_items()
            self.calculate_and_display_totals()
            self.clear_form() # Clear form after add/update

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save line item: {e}")
            print(f"DEBUG: Error saving line item: {e}")

    def delete_line_item(self):
        selected_rows = self.line_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a line item to delete.")
            return

        row = selected_rows[0].row()
        line_item_id = int(self.line_items_table.item(row, 0).text())

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete line item ID {line_item_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                item_to_delete = self.db_session.query(LineItem).filter_by(id=line_item_id).first()
                if item_to_delete:
                    self.db_session.delete(item_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", f"Line item ID {line_item_id} deleted.")
                    self.load_line_items()
                    self.calculate_and_display_totals()
                    self.clear_form()
                else:
                    QMessageBox.warning(self, "Error", "Selected line item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete line item: {e}")
                print(f"DEBUG: Error deleting line item: {e}")

    def clear_form(self):
        self.description_input.clear()
        self.quantity_input.setValue(0.0)
        self.unit_input.clear()
        self.unit_cost_input.setValue(0.0)
        self.markup_percentage_input.setValue(0.0)
        self.notes_input.clear()
        self.is_common_item_checkbox.setCurrentIndex(0) # Reset to Custom Item
        self.common_item_combo.setCurrentIndex(0)
        self.cost_code_combo.setCurrentIndex(0)
        self.description_input.setReadOnly(False) # Ensure editable
        self.unit_input.setReadOnly(False)
        self.unit_cost_input.setReadOnly(False)
        
        self.line_items_table.clearSelection()
        self.add_line_item_button.setEnabled(True)
        self.update_line_item_button.setEnabled(False)
        self.delete_line_item_button.setEnabled(False)

    def closeEvent(self, event):
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    create_db_and_tables()
    session = Session()
    
    # For testing, you need a project ID to open this window.
    # Let's try to get the first project from the database.
    test_project = session.query(Project).first()
    
    if test_project:
        window = EstimateLineItemsWindow(project_id=test_project.id, db_session=session)
        window.show()
    else:
        QMessageBox.critical(None, "No Project", "Please create a project in main_app.py first to test line items.")
        sys.exit(1) # Exit if no project to display
    
    sys.exit(app.exec())