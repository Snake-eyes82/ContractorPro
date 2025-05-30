# src/data_management_window.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QFormLayout, QLineEdit, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QLabel,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal

from src.database import SessionLocal, CommonItem, CostCode # Import models

class DataManagementWindow(QDialog):
    data_updated = Signal() # Signal to notify parent (EstimateLineItemsWindow) of updates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Common Items & Cost Codes")
        self.setGeometry(200, 200, 800, 600)
        self.db_session = SessionLocal()

        self.init_ui()
        self.load_common_items()
        self.load_cost_codes()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Common Items Tab ---
        self.common_items_tab = QWidget()
        self.tab_widget.addTab(self.common_items_tab, "Common Items")
        self.init_common_items_tab()

        # --- Cost Codes Tab ---
        self.cost_codes_tab = QWidget()
        self.tab_widget.addTab(self.cost_codes_tab, "Cost Codes")
        self.init_cost_codes_tab()

        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept) # Use accept() to close modal dialog
        main_layout.addWidget(close_button)

    def init_common_items_tab(self):
        layout = QVBoxLayout(self.common_items_tab)

        # Input Form for Common Items
        form_group = QGroupBox("Common Item Details")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(10, 20, 10, 10)
        form_layout.setSpacing(8)

        self.ci_item_name_input = QLineEdit()
        form_layout.addRow("Item Name:", self.ci_item_name_input)

        self.ci_item_type_combo = QComboBox()
        self.ci_item_type_combo.addItems(["Material", "Labor", "Equipment", "Subcontractor", "Service", "Other"])
        form_layout.addRow("Item Type:", self.ci_item_type_combo)

        self.ci_item_unit_input = QLineEdit()
        form_layout.addRow("Unit (e.g., LF, SF, HR, EA):", self.ci_item_unit_input)

        self.ci_default_cost_spinbox = QDoubleSpinBox()
        self.ci_default_cost_spinbox.setMinimum(0.0)
        self.ci_default_cost_spinbox.setMaximum(999999.99)
        self.ci_default_cost_spinbox.setDecimals(2)
        self.ci_default_cost_spinbox.setSingleStep(0.01)
        form_layout.addRow("Default Cost (Optional):", self.ci_default_cost_spinbox)

        layout.addWidget(form_group)

        # Buttons for Common Items
        buttons_layout = QHBoxLayout()
        self.ci_add_button = QPushButton("Add Common Item")
        self.ci_add_button.clicked.connect(self.add_common_item)
        buttons_layout.addWidget(self.ci_add_button)

        self.ci_update_button = QPushButton("Update Selected Item")
        self.ci_update_button.clicked.connect(self.update_common_item)
        self.ci_update_button.setEnabled(False) # Disabled until selection
        buttons_layout.addWidget(self.ci_update_button)

        self.ci_delete_button = QPushButton("Delete Selected Item")
        self.ci_delete_button.clicked.connect(self.delete_common_item)
        self.ci_delete_button.setEnabled(False) # Disabled until selection
        buttons_layout.addWidget(self.ci_delete_button)

        self.ci_clear_button = QPushButton("Clear Form")
        self.ci_clear_button.clicked.connect(self.clear_common_item_form)
        buttons_layout.addWidget(self.ci_clear_button)
        layout.addLayout(buttons_layout)

        # Table for Common Items
        self.ci_table = QTableWidget()
        self.ci_table.setColumnCount(5) # ID, Name, Type, Unit, Default Cost
        self.ci_table.setHorizontalHeaderLabels(["ID", "Item Name", "Item Type", "Unit", "Default Cost"])
        self.ci_table.setColumnHidden(0, True) # Hide ID column
        self.ci_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ci_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ci_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ci_table.itemSelectionChanged.connect(self.load_selected_common_item)
        layout.addWidget(self.ci_table)

    def init_cost_codes_tab(self):
        layout = QVBoxLayout(self.cost_codes_tab)

        # Input Form for Cost Codes
        form_group = QGroupBox("Cost Code Details")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(10, 20, 10, 10)
        form_layout.setSpacing(8)

        self.cc_code_input = QLineEdit()
        form_layout.addRow("Code (e.g., 03-3000):", self.cc_code_input)

        self.cc_name_input = QLineEdit()
        form_layout.addRow("Name (e.g., Concrete Formwork):", self.cc_name_input)

        self.cc_description_input = QLineEdit()
        form_layout.addRow("Description (Optional):", self.cc_description_input)

        layout.addWidget(form_group)

        # Buttons for Cost Codes
        buttons_layout = QHBoxLayout()
        self.cc_add_button = QPushButton("Add Cost Code")
        self.cc_add_button.clicked.connect(self.add_cost_code)
        buttons_layout.addWidget(self.cc_add_button)

        self.cc_update_button = QPushButton("Update Selected Code")
        self.cc_update_button.clicked.connect(self.update_cost_code)
        self.cc_update_button.setEnabled(False) # Disabled until selection
        buttons_layout.addWidget(self.cc_update_button)

        self.cc_delete_button = QPushButton("Delete Selected Code")
        self.cc_delete_button.clicked.connect(self.delete_cost_code)
        self.cc_delete_button.setEnabled(False) # Disabled until selection
        buttons_layout.addWidget(self.cc_delete_button)

        self.cc_clear_button = QPushButton("Clear Form")
        self.cc_clear_button.clicked.connect(self.clear_cost_code_form)
        buttons_layout.addWidget(self.cc_clear_button)
        layout.addLayout(buttons_layout)

        # Table for Cost Codes
        self.cc_table = QTableWidget()
        self.cc_table.setColumnCount(4) # ID, Code, Name, Description
        self.cc_table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Description"])
        self.cc_table.setColumnHidden(0, True) # Hide ID column
        self.cc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cc_table.setSelectionMode(QTableWidget.SingleSelection)
        self.cc_table.itemSelectionChanged.connect(self.load_selected_cost_code)
        layout.addWidget(self.cc_table)


    # --- Common Item Functions ---
    def load_common_items(self):
        self.ci_table.setRowCount(0)
        try:
            items = self.db_session.query(CommonItem).all()
            for row_idx, item in enumerate(items):
                self.ci_table.insertRow(row_idx)
                self.ci_table.setItem(row_idx, 0, QTableWidgetItem(str(item.item_id)))
                self.ci_table.setItem(row_idx, 1, QTableWidgetItem(item.item_name))
                self.ci_table.setItem(row_idx, 2, QTableWidgetItem(item.item_type))
                self.ci_table.setItem(row_idx, 3, QTableWidgetItem(item.item_unit))
                self.ci_table.setItem(row_idx, 4, QTableWidgetItem(f"{item.default_cost:.2f}" if item.default_cost is not None else ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common items: {e}")

    def add_common_item(self):
        item_name = self.ci_item_name_input.text().strip()
        item_type = self.ci_item_type_combo.currentText()
        item_unit = self.ci_item_unit_input.text().strip()
        default_cost = self.ci_default_cost_spinbox.value() if self.ci_default_cost_spinbox.value() > 0 else None

        if not item_name or not item_type or not item_unit:
            QMessageBox.warning(self, "Input Error", "Item Name, Type, and Unit cannot be empty.")
            return

        try:
            new_item = CommonItem(
                item_name=item_name,
                item_type=item_type,
                item_unit=item_unit,
                default_cost=default_cost
            )
            self.db_session.add(new_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Common item added successfully!")
            self.load_common_items()
            self.clear_common_item_form()
            self.data_updated.emit() # Signal that data has changed
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add common item: {e}")

    def update_common_item(self):
        selected_rows = self.ci_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a common item to update.")
            return

        row = selected_rows[0].row()
        item_id = int(self.ci_table.item(row, 0).text())

        item_name = self.ci_item_name_input.text().strip()
        item_type = self.ci_item_type_combo.currentText()
        item_unit = self.ci_item_unit_input.text().strip()
        default_cost = self.ci_default_cost_spinbox.value() if self.ci_default_cost_spinbox.value() > 0 else None

        if not item_name or not item_type or not item_unit:
            QMessageBox.warning(self, "Input Error", "Item Name, Type, and Unit cannot be empty.")
            return

        try:
            item_to_update = self.db_session.query(CommonItem).filter_by(item_id=item_id).first()
            if item_to_update:
                item_to_update.item_name = item_name
                item_to_update.item_type = item_type
                item_to_update.item_unit = item_unit
                item_to_update.default_cost = default_cost
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Common item updated successfully!")
                self.load_common_items()
                self.clear_common_item_form()
                self.data_updated.emit() # Signal that data has changed
            else:
                QMessageBox.warning(self, "Error", "Common item not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update common item: {e}")

    def delete_common_item(self):
        selected_rows = self.ci_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a common item to delete.")
            return

        row = selected_rows[0].row()
        item_id = int(self.ci_table.item(row, 0).text())
        item_name = self.ci_table.item(row, 1).text()

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete common item '{item_name}' (ID: {item_id})?\n"
                                     "This will NOT remove it from existing line items.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                item_to_delete = self.db_session.query(CommonItem).filter_by(item_id=item_id).first()
                if item_to_delete:
                    self.db_session.delete(item_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Common item deleted successfully!")
                    self.load_common_items()
                    self.clear_common_item_form()
                    self.data_updated.emit() # Signal that data has changed
                else:
                    QMessageBox.warning(self, "Error", "Common item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete common item: {e}")

    def load_selected_common_item(self):
        selected_rows = self.ci_table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            self.ci_item_name_input.setText(self.ci_table.item(row, 1).text())
            self.ci_item_type_combo.setCurrentText(self.ci_table.item(row, 2).text())
            self.ci_item_unit_input.setText(self.ci_table.item(row, 3).text())
            cost_str = self.ci_table.item(row, 4).text()
            self.ci_default_cost_spinbox.setValue(float(cost_str) if cost_str else 0.0)

            self.ci_update_button.setEnabled(True)
            self.ci_delete_button.setEnabled(True)
            self.ci_add_button.setEnabled(False)
        else:
            self.clear_common_item_form()
            self.ci_update_button.setEnabled(False)
            self.ci_delete_button.setEnabled(False)
            self.ci_add_button.setEnabled(True)

    def clear_common_item_form(self):
        self.ci_item_name_input.clear()
        self.ci_item_type_combo.setCurrentIndex(0)
        self.ci_item_unit_input.clear()
        self.ci_default_cost_spinbox.setValue(0.0)
        self.ci_table.clearSelection()
        self.ci_add_button.setEnabled(True)
        self.ci_update_button.setEnabled(False)
        self.ci_delete_button.setEnabled(False)

    # --- Cost Code Functions ---
    def load_cost_codes(self):
        self.cc_table.setRowCount(0)
        try:
            codes = self.db_session.query(CostCode).all()
            for row_idx, code in enumerate(codes):
                self.cc_table.insertRow(row_idx)
                self.cc_table.setItem(row_idx, 0, QTableWidgetItem(str(code.cost_code_id)))
                self.cc_table.setItem(row_idx, 1, QTableWidgetItem(code.code))
                self.cc_table.setItem(row_idx, 2, QTableWidgetItem(code.name))
                self.cc_table.setItem(row_idx, 3, QTableWidgetItem(code.description or ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load cost codes: {e}")

    def add_cost_code(self):
        code = self.cc_code_input.text().strip()
        name = self.cc_name_input.text().strip()
        description = self.cc_description_input.text().strip() or None

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        try:
            new_code = CostCode(
                code=code,
                name=name,
                description=description
            )
            self.db_session.add(new_code)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Cost code added successfully!")
            self.load_cost_codes()
            self.clear_cost_code_form()
            self.data_updated.emit() # Signal that data has changed
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add cost code: {e}")

    def update_cost_code(self):
        selected_rows = self.cc_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a cost code to update.")
            return

        row = selected_rows[0].row()
        cost_code_id = int(self.cc_table.item(row, 0).text())

        code = self.cc_code_input.text().strip()
        name = self.cc_name_input.text().strip()
        description = self.cc_description_input.text().strip() or None

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        try:
            code_to_update = self.db_session.query(CostCode).filter_by(cost_code_id=cost_code_id).first()
            if code_to_update:
                code_to_update.code = code
                code_to_update.name = name
                code_to_update.description = description
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Cost code updated successfully!")
                self.load_cost_codes()
                self.clear_cost_code_form()
                self.data_updated.emit() # Signal that data has changed
            else:
                QMessageBox.warning(self, "Error", "Cost code not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update cost code: {e}")

    def delete_cost_code(self):
        selected_rows = self.cc_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a cost code to delete.")
            return

        row = selected_rows[0].row()
        cost_code_id = int(self.cc_table.item(row, 0).text())
        cost_code_name = self.cc_table.item(row, 2).text()

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete cost code '{cost_code_name}' (ID: {cost_code_id})?\n"
                                     "This will NOT remove it from existing line items.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                code_to_delete = self.db_session.query(CostCode).filter_by(cost_code_id=cost_code_id).first()
                if code_to_delete:
                    self.db_session.delete(code_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Cost code deleted successfully!")
                    self.load_cost_codes()
                    self.clear_cost_code_form()
                    self.data_updated.emit() # Signal that data has changed
                else:
                    QMessageBox.warning(self, "Error", "Cost code not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete cost code: {e}")

    def load_selected_cost_code(self):
        selected_rows = self.cc_table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            self.cc_code_input.setText(self.cc_table.item(row, 1).text())
            self.cc_name_input.setText(self.cc_table.item(row, 2).text())
            self.cc_description_input.setText(self.cc_table.item(row, 3).text())

            self.cc_update_button.setEnabled(True)
            self.cc_delete_button.setEnabled(True)
            self.cc_add_button.setEnabled(False)
        else:
            self.clear_cost_code_form()
            self.cc_update_button.setEnabled(False)
            self.cc_delete_button.setEnabled(False)
            self.cc_add_button.setEnabled(True)

    def clear_cost_code_form(self):
        self.cc_code_input.clear()
        self.cc_name_input.clear()
        self.cc_description_input.clear()
        self.cc_table.clearSelection()
        self.cc_add_button.setEnabled(True)
        self.cc_update_button.setEnabled(False)
        self.cc_delete_button.setEnabled(False)

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)