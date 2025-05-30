import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QComboBox, QLabel, QMessageBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
# Ensure this import is correct based on your database.py structure
from src.database import SessionLocal, CommonItem, CostCode, get_all_common_items, get_all_cost_codes, MASTER_FORMAT_DIVISIONS_2024

class DataManagementWindow(QDialog):
    data_updated = Signal() # Signal to notify other parts of the app when data changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Common Items & Cost Codes")
        self.setGeometry(100, 100, 1000, 700) # Adjust size as needed

        self.db_session = SessionLocal() # Get a new session for this window directly

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Common Items Tab
        self.common_items_tab = QWidget()
        self.tab_widget.addTab(self.common_items_tab, "Common Items (Materials, Labor, Services)")
        self.setup_common_items_tab()

        # Cost Codes Tab
        self.cost_codes_tab = QWidget()
        self.tab_widget.addTab(self.cost_codes_tab, "Cost Codes")
        self.setup_cost_codes_tab()

        # Connect tab changes to refresh data
        self.tab_widget.currentChanged.connect(self.refresh_current_tab_data)

    def closeEvent(self, event):
        # Close the database session when the window is closed
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def setup_common_items_tab(self):
        layout = QVBoxLayout()
        self.common_items_tab.setLayout(layout)

        # Input fields for Common Items
        form_layout = QHBoxLayout()
        self.common_item_name_input = QLineEdit()
        self.common_item_name_input.setPlaceholderText("Item Name (e.g., 2x4x8' Stud)")
        self.common_item_description_input = QLineEdit()
        self.common_item_description_input.setPlaceholderText("Description")
        self.common_item_unit_input = QLineEdit()
        self.common_item_unit_input.setPlaceholderText("Unit (e.g., EA, LF, HR)")
        self.common_item_type_combo = QComboBox()
        self.common_item_type_combo.addItems(["Material", "Labor", "Service"])
        self.common_item_mf_code_input = QLineEdit() # MasterFormat Code for the item itself (e.g., "06 10 00")
        self.common_item_mf_code_input.setPlaceholderText("MasterFormat Code (Optional)")

        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.common_item_name_input)
        form_layout.addWidget(QLabel("Desc:"))
        form_layout.addWidget(self.common_item_description_input)
        form_layout.addWidget(QLabel("Unit:"))
        form_layout.addWidget(self.common_item_unit_input)
        form_layout.addWidget(QLabel("Type:"))
        form_layout.addWidget(self.common_item_type_combo)
        form_layout.addWidget(QLabel("MF Code (Optional):"))
        form_layout.addWidget(self.common_item_mf_code_input)

        layout.addLayout(form_layout)

        # Buttons for Common Items
        button_layout = QHBoxLayout()
        self.add_common_item_btn = QPushButton("Add Item")
        self.add_common_item_btn.clicked.connect(self.add_common_item)
        self.update_common_item_btn = QPushButton("Update Selected Item")
        self.update_common_item_btn.clicked.connect(self.update_common_item)
        self.delete_common_item_btn = QPushButton("Delete Selected Item")
        self.delete_common_item_btn.clicked.connect(self.delete_common_item)
        button_layout.addWidget(self.add_common_item_btn)
        button_layout.addWidget(self.update_common_item_btn)
        button_layout.addWidget(self.delete_common_item_btn)
        layout.addLayout(button_layout)

        # Table for Common Items
        self.common_items_table = QTableWidget()
        self.common_items_table.setColumnCount(6)
        self.common_items_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit", "Type", "MF Code"])
        self.common_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.common_items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.common_items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.common_items_table.itemSelectionChanged.connect(self.load_common_item_into_form)
        layout.addWidget(self.common_items_table)

        self.load_common_items()

    def load_common_items(self):
        self.common_items_table.setRowCount(0)
        try:
            items = get_all_common_items(self.db_session) # Pass the existing session
            self.common_items_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.common_items_table.setItem(row, 0, QTableWidgetItem(str(item.item_id)))
                self.common_items_table.setItem(row, 1, QTableWidgetItem(item.item_name))
                self.common_items_table.setItem(row, 2, QTableWidgetItem(item.item_description))
                self.common_items_table.setItem(row, 3, QTableWidgetItem(item.item_unit))
                self.common_items_table.setItem(row, 4, QTableWidgetItem(item.item_type))
                self.common_items_table.setItem(row, 5, QTableWidgetItem(item.master_format_code or ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common items: {e}")

    def add_common_item(self):
        name = self.common_item_name_input.text().strip()
        description = self.common_item_description_input.text().strip()
        unit = self.common_item_unit_input.text().strip()
        item_type = self.common_item_type_combo.currentText()
        mf_code = self.common_item_mf_code_input.text().strip()
        mf_code = mf_code if mf_code else None

        if not name or not unit:
            QMessageBox.warning(self, "Input Error", "Item Name and Unit cannot be empty.")
            return

        db = self.db_session # Use the existing session
        try:
            existing_item = db.query(CommonItem).filter(CommonItem.item_name == name).first()
            if existing_item:
                QMessageBox.warning(self, "Duplicate Item", f"An item with the name '{name}' already exists.")
                return

            new_item = CommonItem(
                item_name=name,
                item_description=description,
                item_unit=unit,
                item_type=item_type,
                master_format_code=mf_code
            )
            db.add(new_item)
            db.commit()
            self.load_common_items()
            self.clear_common_item_form()
            self.data_updated.emit()
            QMessageBox.information(self, "Success", "Common item added.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to add item: {e}")

    def update_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select an item to update.")
            return

        item_id = int(self.common_items_table.item(selected_rows[0].row(), 0).text())
        name = self.common_item_name_input.text().strip()
        description = self.common_item_description_input.text().strip()
        unit = self.common_item_unit_input.text().strip()
        item_type = self.common_item_type_combo.currentText()
        mf_code = self.common_item_mf_code_input.text().strip()
        mf_code = mf_code if mf_code else None

        if not name or not unit:
            QMessageBox.warning(self, "Input Error", "Item Name and Unit cannot be empty.")
            return

        db = self.db_session # Use the existing session
        try:
            item_to_update = db.query(CommonItem).filter(CommonItem.item_id == item_id).first()
            if not item_to_update:
                QMessageBox.warning(self, "Error", "Selected item not found in database.")
                return

            if item_to_update.item_name != name:
                existing_item = db.query(CommonItem).filter(CommonItem.item_name == name).first()
                if existing_item and existing_item.item_id != item_id:
                    QMessageBox.warning(self, "Duplicate Item", f"An item with the name '{name}' already exists.")
                    return

            item_to_update.item_name = name
            item_to_update.item_description = description
            item_to_update.item_unit = unit
            item_to_update.item_type = item_type
            item_to_update.master_format_code = mf_code
            db.commit()
            self.load_common_items()
            self.clear_common_item_form()
            self.data_updated.emit()
            QMessageBox.information(self, "Success", "Common item updated.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update item: {e}")

    def delete_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this item? This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        item_id = int(self.common_items_table.item(selected_rows[0].row(), 0).text())
        db = self.db_session # Use the existing session
        try:
            item_to_delete = db.query(CommonItem).filter(CommonItem.item_id == item_id).first()
            if item_to_delete:
                db.delete(item_to_delete)
                db.commit()
                self.load_common_items()
                self.clear_common_item_form()
                self.data_updated.emit()
                QMessageBox.information(self, "Success", "Common item deleted.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to delete item: {e}")

    def load_common_item_into_form(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.common_item_name_input.setText(self.common_items_table.item(row, 1).text())
            self.common_item_description_input.setText(self.common_items_table.item(row, 2).text())
            self.common_item_unit_input.setText(self.common_items_table.item(row, 3).text())
            self.common_item_type_combo.setCurrentText(self.common_items_table.item(row, 4).text())
            self.common_item_mf_code_input.setText(self.common_items_table.item(row, 5).text())
        else:
            self.clear_common_item_form()

    def clear_common_item_form(self):
        self.common_item_name_input.clear()
        self.common_item_description_input.clear()
        self.common_item_unit_input.clear()
        self.common_item_type_combo.setCurrentIndex(0) # Default to Material
        self.common_item_mf_code_input.clear()


    def setup_cost_codes_tab(self):
        layout = QVBoxLayout()
        self.cost_codes_tab.setLayout(layout)

        # Input fields for Cost Codes
        form_layout = QHBoxLayout()
        self.cost_code_code_input = QLineEdit()
        self.cost_code_code_input.setPlaceholderText("Code (e.g., 03 30 00, EL-01)")
        self.cost_code_name_input = QLineEdit()
        self.cost_code_name_input.setPlaceholderText("Name (e.g., Cast-in-Place Concrete)")
        self.cost_code_description_input = QLineEdit()
        self.cost_code_description_input.setPlaceholderText("Description (Optional)")
        self.cost_code_mf_division_combo = QComboBox()
        self.cost_code_mf_division_combo.addItems([""] + MASTER_FORMAT_DIVISIONS_2024) # Allow empty selection

        form_layout.addWidget(QLabel("Code:"))
        form_layout.addWidget(self.cost_code_code_input)
        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.cost_code_name_input)
        form_layout.addWidget(QLabel("Desc:"))
        form_layout.addWidget(self.cost_code_description_input)
        form_layout.addWidget(QLabel("MF Division:"))
        form_layout.addWidget(self.cost_code_mf_division_combo)

        layout.addLayout(form_layout)

        # Buttons for Cost Codes
        button_layout = QHBoxLayout()
        self.add_cost_code_btn = QPushButton("Add Code")
        self.add_cost_code_btn.clicked.connect(self.add_cost_code)
        self.update_cost_code_btn = QPushButton("Update Selected Code")
        self.update_cost_code_btn.clicked.connect(self.update_cost_code)
        self.delete_cost_code_btn = QPushButton("Delete Selected Code")
        self.delete_cost_code_btn.clicked.connect(self.delete_cost_code)
        button_layout.addWidget(self.add_cost_code_btn)
        button_layout.addWidget(self.update_cost_code_btn)
        button_layout.addWidget(self.delete_cost_code_btn)
        layout.addLayout(button_layout)

        # Table for Cost Codes
        self.cost_codes_table = QTableWidget()
        self.cost_codes_table.setColumnCount(5)
        self.cost_codes_table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Description", "MF Division"])
        self.cost_codes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cost_codes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cost_codes_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cost_codes_table.itemSelectionChanged.connect(self.load_cost_code_into_form)
        layout.addWidget(self.cost_codes_table)

        self.load_cost_codes()

    def load_cost_codes(self):
        self.cost_codes_table.setRowCount(0)
        try:
            codes = get_all_cost_codes(self.db_session) # Pass the existing session
            self.cost_codes_table.setRowCount(len(codes))
            for row, code in enumerate(codes):
                self.cost_codes_table.setItem(row, 0, QTableWidgetItem(str(code.cost_code_id)))
                self.cost_codes_table.setItem(row, 1, QTableWidgetItem(code.code))
                self.cost_codes_table.setItem(row, 2, QTableWidgetItem(code.name))
                self.cost_codes_table.setItem(row, 3, QTableWidgetItem(code.description or ""))
                self.cost_codes_table.setItem(row, 4, QTableWidgetItem(code.master_format_division or ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load cost codes: {e}")

    def add_cost_code(self):
        code = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        description = self.cost_code_description_input.text().strip()
        mf_division = self.cost_code_mf_division_combo.currentText()
        mf_division = mf_division if mf_division else None

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        db = self.db_session # Use the existing session
        try:
            existing_code = db.query(CostCode).filter(CostCode.code == code).first()
            if existing_code:
                QMessageBox.warning(self, "Duplicate Code", f"A cost code with the code '{code}' already exists.")
                return

            new_code = CostCode(
                code=code,
                name=name,
                description=description,
                master_format_division=mf_division
            )
            db.add(new_code)
            db.commit()
            self.load_cost_codes()
            self.clear_cost_code_form()
            self.data_updated.emit()
            QMessageBox.information(self, "Success", "Cost code added.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to add cost code: {e}")

    def update_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a cost code to update.")
            return

        code_id = int(self.cost_codes_table.item(selected_rows[0].row(), 0).text())
        code = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        description = self.cost_code_description_input.text().strip()
        mf_division = self.cost_code_mf_division_combo.currentText()
        mf_division = mf_division if mf_division else None

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        db = self.db_session # Use the existing session
        try:
            code_to_update = db.query(CostCode).filter(CostCode.cost_code_id == code_id).first()
            if not code_to_update:
                QMessageBox.warning(self, "Error", "Selected cost code not found in database.")
                return

            if code_to_update.code != code:
                existing_code = db.query(CostCode).filter(CostCode.code == code).first()
                if existing_code and existing_code.cost_code_id != code_id:
                    QMessageBox.warning(self, "Duplicate Code", f"A cost code with the code '{code}' already exists.")
                    return

            code_to_update.code = code
            code_to_update.name = name
            code_to_update.description = description
            code_to_update.master_format_division = mf_division
            db.commit()
            self.load_cost_codes()
            self.clear_cost_code_form()
            self.data_updated.emit()
            QMessageBox.information(self, "Success", "Cost code updated.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update cost code: {e}")

    def delete_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a cost code to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this cost code? This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        code_id = int(self.cost_codes_table.item(selected_rows[0].row(), 0).text())
        db = self.db_session # Use the existing session
        try:
            code_to_delete = db.query(CostCode).filter(CostCode.cost_code_id == code_id).first()
            if code_to_delete:
                db.delete(code_to_delete)
                db.commit()
                self.load_cost_codes()
                self.clear_cost_code_form()
                self.data_updated.emit()
                QMessageBox.information(self, "Success", "Cost code deleted.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to delete cost code: {e}")

    def load_cost_code_into_form(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.cost_code_code_input.setText(self.cost_codes_table.item(row, 1).text())
            self.cost_code_name_input.setText(self.cost_codes_table.item(row, 2).text())
            self.cost_code_description_input.setText(self.cost_codes_table.item(row, 3).text())
            mf_division = self.cost_codes_table.item(row, 4).text()
            index = self.cost_code_mf_division_combo.findText(mf_division)
            if index != -1:
                self.cost_code_mf_division_combo.setCurrentIndex(index)
            else:
                self.cost_code_mf_division_combo.setCurrentIndex(0) # Select empty if not found
        else:
            self.clear_cost_code_form()

    def clear_cost_code_form(self):
        self.cost_code_code_input.clear()
        self.cost_code_name_input.clear()
        self.cost_code_description_input.clear()
        self.cost_code_mf_division_combo.setCurrentIndex(0) # Default to empty

    def refresh_current_tab_data(self, index):
        if index == 0: # Common Items tab
            self.load_common_items()
        elif index == 1: # Cost Codes tab
            self.load_cost_codes()


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    # Import and run database initialization to ensure tables/data are ready
    from src.database import create_db_and_tables # Import create_db_and_tables
    create_db_and_tables() # Call it here

    app = QApplication(sys.argv)
    window = DataManagementWindow()
    window.show()
    sys.exit(app.exec())