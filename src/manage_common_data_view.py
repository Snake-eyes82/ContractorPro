# src/manage_common_data_view.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize
# Import your models from the updated database.py
from src.database import Session, CommonItem, CostCode

class ManageCommonDataWindow(QMainWindow):
    # Signal emitted when common items or cost codes are updated
    data_updated_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = Session()
        self.setWindowTitle("Manage Common Items & Cost Codes")
        self.setGeometry(200, 200, 900, 700) # Adjusted size
        self.setMinimumSize(QSize(800, 600))
        self.init_ui()
        self.load_common_items()
        self.load_cost_codes()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Common Items Tab ---
        self.common_items_tab = QWidget()
        self.tab_widget.addTab(self.common_items_tab, "Common Items (Materials, Labor, Services)")
        self.common_items_layout = QVBoxLayout(self.common_items_tab)

        # Common Item Input Form
        common_item_group = QGroupBox("Common Item Details")
        common_item_form_layout = QFormLayout(common_item_group)
        self.common_item_name_input = QLineEdit()
        common_item_form_layout.addRow("Name:", self.common_item_name_input)
        self.common_item_description_input = QLineEdit()
        common_item_form_layout.addRow("Description:", self.common_item_description_input)
        self.common_item_unit_input = QLineEdit()
        self.common_item_unit_input.setPlaceholderText("e.g., EA, LF, HR")
        common_item_form_layout.addRow("Unit:", self.common_item_unit_input)
        self.common_item_type_combo = QComboBox()
        self.common_item_type_combo.addItems(["Material", "Labor", "Service"]) # Ensure these match CommonItem.type in DB
        common_item_form_layout.addRow("Type:", self.common_item_type_combo)
        self.common_item_mf_code_input = QLineEdit()
        common_item_form_layout.addRow("MF Code (Optional):", self.common_item_mf_code_input)

        common_item_buttons_layout = QHBoxLayout()
        self.add_common_item_button = QPushButton("Add Item")
        self.add_common_item_button.clicked.connect(self.add_common_item)
        self.update_common_item_button = QPushButton("Update Selected Item")
        self.update_common_item_button.clicked.connect(self.update_common_item)
        self.update_common_item_button.setEnabled(False)
        self.delete_common_item_button = QPushButton("Delete Selected Item")
        self.delete_common_item_button.clicked.connect(self.delete_common_item)
        self.delete_common_item_button.setEnabled(False)
        common_item_buttons_layout.addWidget(self.add_common_item_button)
        common_item_buttons_layout.addWidget(self.update_common_item_button)
        common_item_buttons_layout.addWidget(self.delete_common_item_button)
        common_item_form_layout.addRow(common_item_buttons_layout)
        self.common_items_layout.addWidget(common_item_group)

        # Common Items Table
        self.common_items_table = QTableWidget()
        self.common_items_table.setColumnCount(6) # ID, Name, Description, Unit, Type, MF Code
        self.common_items_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit", "Type", "MF Code"])
        self.common_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.common_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.common_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.common_items_table.itemSelectionChanged.connect(self.on_common_item_table_selected)
        self.common_items_layout.addWidget(self.common_items_table)

        # --- Cost Codes Tab ---
        self.cost_codes_tab = QWidget()
        self.tab_widget.addTab(self.cost_codes_tab, "Cost Codes")
        self.cost_codes_layout = QVBoxLayout(self.cost_codes_tab)

        # Cost Code Input Form
        cost_code_group = QGroupBox("Cost Code Details")
        cost_code_form_layout = QFormLayout(cost_code_group)
        self.cost_code_code_input = QLineEdit()
        self.cost_code_code_input.setPlaceholderText("e.g., 03 30 00")
        cost_code_form_layout.addRow("Code:", self.cost_code_code_input)
        self.cost_code_name_input = QLineEdit()
        cost_code_form_layout.addRow("Name:", self.cost_code_name_input)
        self.cost_code_description_input = QLineEdit()
        cost_code_form_layout.addRow("Description (Optional):", self.cost_code_description_input)
        self.cost_code_mf_division_input = QLineEdit()
        cost_code_form_layout.addRow("MF Division:", self.cost_code_mf_division_input)

        cost_code_buttons_layout = QHBoxLayout()
        self.add_cost_code_button = QPushButton("Add Code")
        self.add_cost_code_button.clicked.connect(self.add_cost_code)
        self.update_cost_code_button = QPushButton("Update Selected Code")
        self.update_cost_code_button.clicked.connect(self.update_cost_code)
        self.update_cost_code_button.setEnabled(False)
        self.delete_cost_code_button = QPushButton("Delete Selected Code")
        self.delete_cost_code_button.clicked.connect(self.delete_cost_code)
        self.delete_cost_code_button.setEnabled(False)
        cost_code_buttons_layout.addWidget(self.add_cost_code_button)
        cost_code_buttons_layout.addWidget(self.update_cost_code_button)
        cost_code_buttons_layout.addWidget(self.delete_cost_code_button)
        cost_code_form_layout.addRow(cost_code_buttons_layout)
        self.cost_codes_layout.addWidget(cost_code_group)

        # Cost Codes Table
        self.cost_codes_table = QTableWidget()
        self.cost_codes_table.setColumnCount(5) # ID, Code, Name, Description, MF Division
        self.cost_codes_table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Description", "MF Division"])
        self.cost_codes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cost_codes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cost_codes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.cost_codes_table.itemSelectionChanged.connect(self.on_cost_code_table_selected)
        self.cost_codes_layout.addWidget(self.cost_codes_table)


    # --- Common Items Methods ---
    def load_common_items(self):
        self.common_items_table.setRowCount(0)
        try:
            items = self.db_session.query(CommonItem).all()
            self.common_items_table.setRowCount(len(items))
            for row_idx, item in enumerate(items):
                self.common_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.id)))
                self.common_items_table.setItem(row_idx, 1, QTableWidgetItem(item.name))
                self.common_items_table.setItem(row_idx, 2, QTableWidgetItem(item.description or ""))
                self.common_items_table.setItem(row_idx, 3, QTableWidgetItem(item.unit or ""))
                self.common_items_table.setItem(row_idx, 4, QTableWidgetItem(item.type or ""))
                self.common_items_table.setItem(row_idx, 5, QTableWidgetItem(item.mf_code or ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load common items: {e}")

    def clear_common_item_form(self):
        self.common_item_name_input.clear()
        self.common_item_description_input.clear()
        self.common_item_unit_input.clear()
        self.common_item_type_combo.setCurrentIndex(0)
        self.common_item_mf_code_input.clear()
        self.update_common_item_button.setEnabled(False)
        self.delete_common_item_button.setEnabled(False)
        self.add_common_item_button.setEnabled(True)
        self.common_items_table.clearSelection()

    def add_common_item(self):
        name = self.common_item_name_input.text().strip()
        description = self.common_item_description_input.text().strip()
        unit = self.common_item_unit_input.text().strip()
        item_type = self.common_item_type_combo.currentText()
        mf_code = self.common_item_mf_code_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Common Item Name cannot be empty.")
            return

        try:
            new_item = CommonItem(
                name=name,
                description=description if description else None,
                unit=unit if unit else None,
                type=item_type,
                mf_code=mf_code if mf_code else None
            )
            self.db_session.add(new_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Common item added successfully!")
            self.clear_common_item_form()
            self.load_common_items()
            self.data_updated_signal.emit() # Notify other windows (like Line Items)
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add common item: {e}")

    def on_common_item_table_selected(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            item_id = int(self.common_items_table.item(row, 0).text())
            item = self.db_session.query(CommonItem).filter_by(id=item_id).first()
            if item:
                self.common_item_name_input.setText(item.name)
                self.common_item_description_input.setText(item.description or "")
                self.common_item_unit_input.setText(item.unit or "")
                self.common_item_type_combo.setCurrentText(item.type or "Material")
                self.common_item_mf_code_input.setText(item.mf_code or "")
                self.update_common_item_button.setEnabled(True)
                self.delete_common_item_button.setEnabled(True)
                self.add_common_item_button.setEnabled(False)
        else:
            self.clear_common_item_form()

    def update_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a common item to update.")
            return

        row = selected_rows[0].row()
        item_id = int(self.common_items_table.item(row, 0).text())

        name = self.common_item_name_input.text().strip()
        description = self.common_item_description_input.text().strip()
        unit = self.common_item_unit_input.text().strip()
        item_type = self.common_item_type_combo.currentText()
        mf_code = self.common_item_mf_code_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Common Item Name cannot be empty.")
            return

        try:
            item = self.db_session.query(CommonItem).filter_by(id=item_id).first()
            if item:
                item.name = name
                item.description = description if description else None
                item.unit = unit if unit else None
                item.type = item_type
                item.mf_code = mf_code if mf_code else None
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Common item updated successfully!")
                self.clear_common_item_form()
                self.load_common_items()
                self.data_updated_signal.emit()
            else:
                QMessageBox.warning(self, "Error", "Selected common item not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update common item: {e}")

    def delete_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a common item to delete.")
            return

        row = selected_rows[0].row()
        item_id = int(self.common_items_table.item(row, 0).text())

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete common item ID {item_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                item = self.db_session.query(CommonItem).filter_by(id=item_id).first()
                if item:
                    self.db_session.delete(item)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Common item deleted successfully!")
                    self.clear_common_item_form()
                    self.load_common_items()
                    self.data_updated_signal.emit()
                else:
                    QMessageBox.warning(self, "Error", "Selected common item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete common item: {e}")


    # --- Cost Codes Methods ---
    def load_cost_codes(self):
        self.cost_codes_table.setRowCount(0)
        try:
            codes = self.db_session.query(CostCode).all()
            self.cost_codes_table.setRowCount(len(codes))
            for row_idx, code in enumerate(codes):
                self.cost_codes_table.setItem(row_idx, 0, QTableWidgetItem(str(code.id)))
                self.cost_codes_table.setItem(row_idx, 1, QTableWidgetItem(code.code))
                self.cost_codes_table.setItem(row_idx, 2, QTableWidgetItem(code.name))
                self.cost_codes_table.setItem(row_idx, 3, QTableWidgetItem(code.description or ""))
                self.cost_codes_table.setItem(row_idx, 4, QTableWidgetItem(code.mf_division or ""))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load cost codes: {e}")

    def clear_cost_code_form(self):
        self.cost_code_code_input.clear()
        self.cost_code_name_input.clear()
        self.cost_code_description_input.clear()
        self.cost_code_mf_division_input.clear()
        self.update_cost_code_button.setEnabled(False)
        self.delete_cost_code_button.setEnabled(False)
        self.add_cost_code_button.setEnabled(True)
        self.cost_codes_table.clearSelection()

    def add_cost_code(self):
        code = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        description = self.cost_code_description_input.text().strip()
        mf_division = self.cost_code_mf_division_input.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Cost Code and Name cannot be empty.")
            return

        try:
            new_code = CostCode(
                code=code,
                name=name,
                description=description if description else None,
                mf_division=mf_division if mf_division else None
            )
            self.db_session.add(new_code)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "Cost code added successfully!")
            self.clear_cost_code_form()
            self.load_cost_codes()
            self.data_updated_signal.emit()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add cost code: {e}")

    def on_cost_code_table_selected(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            code_id = int(self.cost_codes_table.item(row, 0).text())
            code_obj = self.db_session.query(CostCode).filter_by(id=code_id).first()
            if code_obj:
                self.cost_code_code_input.setText(code_obj.code)
                self.cost_code_name_input.setText(code_obj.name)
                self.cost_code_description_input.setText(code_obj.description or "")
                self.cost_code_mf_division_input.setText(code_obj.mf_division or "")
                self.update_cost_code_button.setEnabled(True)
                self.delete_cost_code_button.setEnabled(True)
                self.add_cost_code_button.setEnabled(False)
        else:
            self.clear_cost_code_form()

    def update_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a cost code to update.")
            return

        row = selected_rows[0].row()
        code_id = int(self.cost_codes_table.item(row, 0).text())

        code = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        description = self.cost_code_description_input.text().strip()
        mf_division = self.cost_code_mf_division_input.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Cost Code and Name cannot be empty.")
            return

        try:
            code_obj = self.db_session.query(CostCode).filter_by(id=code_id).first()
            if code_obj:
                code_obj.code = code
                code_obj.name = name
                code_obj.description = description if description else None
                code_obj.mf_division = mf_division if mf_division else None
                self.db_session.commit()
                QMessageBox.information(self, "Success", "Cost code updated successfully!")
                self.clear_cost_code_form()
                self.load_cost_codes()
                self.data_updated_signal.emit()
            else:
                QMessageBox.warning(self, "Error", "Selected cost code not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update cost code: {e}")

    def delete_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a cost code to delete.")
            return

        row = selected_rows[0].row()
        code_id = int(self.cost_codes_table.item(row, 0).text())

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete cost code ID {code_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                code_obj = self.db_session.query(CostCode).filter_by(id=code_id).first()
                if code_obj:
                    self.db_session.delete(code_obj)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Cost code deleted successfully!")
                    self.clear_cost_code_form()
                    self.load_cost_codes()
                    self.data_updated_signal.emit()
                else:
                    QMessageBox.warning(self, "Error", "Selected cost code not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete cost code: {e}")

    def closeEvent(self, event):
        """Clean up database session when the window is closed."""
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)
