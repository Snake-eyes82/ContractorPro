# src/manage_common_data_view.py

import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QHBoxLayout, QFormLayout, QLineEdit, QTextEdit, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from src.database import Session, CommonItem, CostCode, MFGroup, create_db_and_tables

class ManageCommonDataWindow(QDialog):
    data_updated_signal = Signal() # Signal to notify the dashboard or other windows to refresh

    def __init__(self, db_session, parent=None): # Corrected: db_session is a positional argument
        super().__init__(parent)
        self.db_session = db_session
        self.setWindowTitle("Manage Common Items & Cost Codes")
        self.setGeometry(250, 250, 900, 600)

        self.init_ui()
        self.load_common_items()
        self.load_cost_codes()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Common Items Tab
        self.common_items_tab = QWidget()
        self.tab_widget.addTab(self.common_items_tab, "Common Items (Materials, Labor, Services)")
        self.init_common_items_tab()

        # Cost Codes Tab
        self.cost_codes_tab = QWidget()
        self.tab_widget.addTab(self.cost_codes_tab, "Cost Codes")
        self.init_cost_codes_tab()

        # Buttons at the bottom (optional, but good for common dialogs)
        # close_button_layout = QHBoxLayout()
        # close_button = QPushButton("Close")
        # close_button.clicked.connect(self.accept)
        # close_button_layout.addStretch()
        # close_button_layout.addWidget(close_button)
        # main_layout.addLayout(close_button_layout)

    def init_common_items_tab(self):
        layout = QVBoxLayout(self.common_items_tab)
        form_layout = QFormLayout()

        self.common_item_name_input = QLineEdit()
        form_layout.addRow("Name:", self.common_item_name_input)
        self.common_item_description_input = QTextEdit()
        form_layout.addRow("Description:", self.common_item_description_input)
        self.common_item_unit_input = QLineEdit()
        form_layout.addRow("Unit (e.g., EA, LF, HR):", self.common_item_unit_input)
        self.common_item_type_combo = QComboBox()
        self.common_item_type_combo.addItems(["Material", "Labor", "Service", "Equipment", "Other"])
        form_layout.addRow("Type:", self.common_item_type_combo)
        self.common_item_mf_code_input = QLineEdit() # Optional: For linking to specific MF Code
        form_layout.addRow("MasterFormat Code:", self.common_item_mf_code_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_common_item_btn = QPushButton("Add Item")
        self.add_common_item_btn.clicked.connect(self.add_common_item)
        button_layout.addWidget(self.add_common_item_btn)

        self.update_common_item_btn = QPushButton("Update Selected Item")
        self.update_common_item_btn.clicked.connect(self.update_common_item)
        self.update_common_item_btn.setEnabled(False)
        button_layout.addWidget(self.update_common_item_btn)

        self.delete_common_item_btn = QPushButton("Delete Selected Item")
        self.delete_common_item_btn.clicked.connect(self.delete_common_item)
        self.delete_common_item_btn.setEnabled(False)
        button_layout.addWidget(self.delete_common_item_btn)

        self.clear_common_item_form_btn = QPushButton("Clear Form")
        self.clear_common_item_form_btn.clicked.connect(self.clear_common_item_form)
        button_layout.addWidget(self.clear_common_item_form_btn)
        
        layout.addLayout(button_layout)

        self.common_items_table = QTableWidget()
        self.common_items_table.setColumnCount(6)
        self.common_items_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit", "Type", "MF Code"])
        self.common_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.common_items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.common_items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.common_items_table.itemSelectionChanged.connect(self.on_common_item_selection_changed)
        layout.addWidget(self.common_items_table)

    def init_cost_codes_tab(self):
        layout = QVBoxLayout(self.cost_codes_tab)
        form_layout = QFormLayout()

        self.cost_code_code_input = QLineEdit()
        form_layout.addRow("Code (e.g., 03 30 00):", self.cost_code_code_input)
        self.cost_code_name_input = QLineEdit()
        form_layout.addRow("Name:", self.cost_code_name_input)
        self.cost_code_description_input = QTextEdit()
        form_layout.addRow("Description (Optional):", self.cost_code_description_input)

        # Dropdown for MF Division (parent MFGroup)
        self.mf_group_combo = QComboBox()
        self.mf_groups_map = {f"{g.code} - {g.name}": g for g in self.db_session.query(MFGroup).filter(MFGroup.level <= 1).order_by(MFGroup.code).all()}
        self.mf_group_combo.addItem("-- Select MF Division --")
        self.mf_group_combo.addItems(sorted(self.mf_groups_map.keys()))
        form_layout.addRow("MF Division:", self.mf_group_combo)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_cost_code_btn = QPushButton("Add Code")
        self.add_cost_code_btn.clicked.connect(self.add_cost_code)
        button_layout.addWidget(self.add_cost_code_btn)

        self.update_cost_code_btn = QPushButton("Update Selected Code")
        self.update_cost_code_btn.clicked.connect(self.update_cost_code)
        self.update_cost_code_btn.setEnabled(False)
        button_layout.addWidget(self.update_cost_code_btn)

        self.delete_cost_code_btn = QPushButton("Delete Selected Code")
        self.delete_cost_code_btn.clicked.connect(self.delete_cost_code)
        self.delete_cost_code_btn.setEnabled(False)
        button_layout.addWidget(self.delete_cost_code_btn)

        self.clear_cost_code_form_btn = QPushButton("Clear Form")
        self.clear_cost_code_form_btn.clicked.connect(self.clear_cost_code_form)
        button_layout.addWidget(self.clear_cost_code_form_btn)

        layout.addLayout(button_layout)

        self.cost_codes_table = QTableWidget()
        self.cost_codes_table.setColumnCount(5)
        self.cost_codes_table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Description", "MF Division"])
        self.cost_codes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cost_codes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cost_codes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.cost_codes_table.itemSelectionChanged.connect(self.on_cost_code_selection_changed)
        layout.addWidget(self.cost_codes_table)


    # --- Common Items Methods ---
    def load_common_items(self):
        self.common_items_table.setRowCount(0)
        items = self.db_session.query(CommonItem).order_by(CommonItem.name).all()
        self.common_items_table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.common_items_table.setItem(row_idx, 0, QTableWidgetItem(str(item.id)))
            self.common_items_table.setItem(row_idx, 1, QTableWidgetItem(item.name or ""))
            self.common_items_table.setItem(row_idx, 2, QTableWidgetItem(item.description or ""))
            self.common_items_table.setItem(row_idx, 3, QTableWidgetItem(item.unit or ""))
            self.common_items_table.setItem(row_idx, 4, QTableWidgetItem(item.type or ""))
            self.common_items_table.setItem(row_idx, 5, QTableWidgetItem(item.mf_code or ""))
            self.common_items_table.item(row_idx, 0).setData(Qt.UserRole, item) # Store full object

    def on_common_item_selection_changed(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            selected_item = self.common_items_table.item(row, 0).data(Qt.UserRole)
            if selected_item:
                self.common_item_name_input.setText(selected_item.name or "")
                self.common_item_description_input.setText(selected_item.description or "")
                self.common_item_unit_input.setText(selected_item.unit or "")
                self.common_item_type_combo.setCurrentText(selected_item.type or "")
                self.common_item_mf_code_input.setText(selected_item.mf_code or "")
                self.add_common_item_btn.setEnabled(False)
                self.update_common_item_btn.setEnabled(True)
                self.delete_common_item_btn.setEnabled(True)
        else:
            self.clear_common_item_form()
            self.add_common_item_btn.setEnabled(True)
            self.update_common_item_btn.setEnabled(False)
            self.delete_common_item_btn.setEnabled(False)

    def add_common_item(self):
        name = self.common_item_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Common Item Name cannot be empty.")
            return
        
        try:
            existing_item = self.db_session.query(CommonItem).filter(CommonItem.name == name).first()
            if existing_item:
                QMessageBox.warning(self, "Duplicate Entry", f"A common item named '{name}' already exists.")
                return

            new_item = CommonItem(
                name=name,
                description=self.common_item_description_input.toPlainText().strip() or None,
                unit=self.common_item_unit_input.text().strip() or None,
                type=self.common_item_type_combo.currentText() or None,
                mf_code=self.common_item_mf_code_input.text().strip() or None
            )
            self.db_session.add(new_item)
            self.db_session.commit()
            QMessageBox.information(self, "Success", f"Common item '{name}' added.")
            self.load_common_items()
            self.clear_common_item_form()
            self.data_updated_signal.emit()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add common item: {e}")
            print(f"DEBUG: Error adding common item: {e}")

    def update_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select an item to update.")
            return
        
        row = selected_rows[0].row()
        item_id = int(self.common_items_table.item(row, 0).text())
        name = self.common_item_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Common Item Name cannot be empty.")
            return

        try:
            item_to_update = self.db_session.query(CommonItem).filter_by(id=item_id).first()
            if item_to_update:
                # Check for duplicate name if changed
                if item_to_update.name != name:
                    existing_item = self.db_session.query(CommonItem).filter(CommonItem.name == name).first()
                    if existing_item and existing_item.id != item_id:
                        QMessageBox.warning(self, "Duplicate Entry", f"A common item named '{name}' already exists.")
                        return

                item_to_update.name = name
                item_to_update.description = self.common_item_description_input.toPlainText().strip() or None
                item_to_update.unit = self.common_item_unit_input.text().strip() or None
                item_to_update.type = self.common_item_type_combo.currentText() or None
                item_to_update.mf_code = self.common_item_mf_code_input.text().strip() or None
                self.db_session.commit()
                QMessageBox.information(self, "Success", f"Common item '{name}' updated.")
                self.load_common_items()
                self.clear_common_item_form()
                self.data_updated_signal.emit()
            else:
                QMessageBox.warning(self, "Error", "Selected common item not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update common item: {e}")
            print(f"DEBUG: Error updating common item: {e}")

    def delete_common_item(self):
        selected_rows = self.common_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select an item to delete.")
            return
        
        row = selected_rows[0].row()
        item_id = int(self.common_items_table.item(row, 0).text())
        item_name = self.common_items_table.item(row, 1).text()

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete common item '{item_name}' (ID: {item_id})? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                item_to_delete = self.db_session.query(CommonItem).filter_by(id=item_id).first()
                if item_to_delete:
                    self.db_session.delete(item_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", f"Common item '{item_name}' deleted.")
                    self.load_common_items()
                    self.clear_common_item_form()
                    self.data_updated_signal.emit()
                else:
                    QMessageBox.warning(self, "Error", "Selected common item not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete common item: {e}")
                print(f"DEBUG: Error deleting common item: {e}")

    def clear_common_item_form(self):
        self.common_item_name_input.clear()
        self.common_item_description_input.clear()
        self.common_item_unit_input.clear()
        self.common_item_type_combo.setCurrentIndex(0)
        self.common_item_mf_code_input.clear()
        self.common_items_table.clearSelection()
        self.add_common_item_btn.setEnabled(True)
        self.update_common_item_btn.setEnabled(False)
        self.delete_common_item_btn.setEnabled(False)

    # --- Cost Codes Methods ---
    def load_cost_codes(self):
        self.cost_codes_table.setRowCount(0)
        codes = self.db_session.query(CostCode).order_by(CostCode.code).all()
        self.cost_codes_table.setRowCount(len(codes))
        for row_idx, code in enumerate(codes):
            mf_division_name = code.mf_group.name if code.mf_group else "N/A"
            self.cost_codes_table.setItem(row_idx, 0, QTableWidgetItem(str(code.id)))
            self.cost_codes_table.setItem(row_idx, 1, QTableWidgetItem(code.code or ""))
            self.cost_codes_table.setItem(row_idx, 2, QTableWidgetItem(code.name or ""))
            self.cost_codes_table.setItem(row_idx, 3, QTableWidgetItem(code.description or ""))
            self.cost_codes_table.setItem(row_idx, 4, QTableWidgetItem(mf_division_name))
            self.cost_codes_table.item(row_idx, 0).setData(Qt.UserRole, code) # Store full object

    def on_cost_code_selection_changed(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            selected_code = self.cost_codes_table.item(row, 0).data(Qt.UserRole)
            if selected_code:
                self.cost_code_code_input.setText(selected_code.code or "")
                self.cost_code_name_input.setText(selected_code.name or "")
                self.cost_code_description_input.setText(selected_code.description or "")
                if selected_code.mf_group:
                    mf_group_text = f"{selected_code.mf_group.code} - {selected_code.mf_group.name}"
                    index = self.mf_group_combo.findText(mf_group_text)
                    if index != -1:
                        self.mf_group_combo.setCurrentIndex(index)
                    else:
                        self.mf_group_combo.setCurrentIndex(0) # Not found, reset
                else:
                    self.mf_group_combo.setCurrentIndex(0)

                self.add_cost_code_btn.setEnabled(False)
                self.update_cost_code_btn.setEnabled(True)
                self.delete_cost_code_btn.setEnabled(True)
        else:
            self.clear_cost_code_form()
            self.add_cost_code_btn.setEnabled(True)
            self.update_cost_code_btn.setEnabled(False)
            self.delete_cost_code_btn.setEnabled(False)

    def add_cost_code(self):
        code = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        try:
            existing_code = self.db_session.query(CostCode).filter(CostCode.code == code).first()
            if existing_code:
                QMessageBox.warning(self, "Duplicate Entry", f"A cost code '{code}' already exists.")
                return

            selected_mf_group = None
            mf_group_text = self.mf_group_combo.currentText()
            if mf_group_text != "-- Select MF Division --":
                selected_mf_group = self.mf_groups_map.get(mf_group_text)
                if not selected_mf_group:
                    QMessageBox.critical(self, "Error", "Selected MasterFormat Division not found.")
                    return

            new_code = CostCode(
                code=code,
                name=name,
                description=self.cost_code_description_input.toPlainText().strip() or None,
                mf_group=selected_mf_group
            )
            self.db_session.add(new_code)
            self.db_session.commit()
            QMessageBox.information(self, "Success", f"Cost code '{code}' added.")
            self.load_cost_codes()
            self.clear_cost_code_form()
            self.data_updated_signal.emit()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add cost code: {e}")
            print(f"DEBUG: Error adding cost code: {e}")

    def update_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a cost code to update.")
            return
        
        row = selected_rows[0].row()
        code_id = int(self.cost_codes_table.item(row, 0).text())
        code_str = self.cost_code_code_input.text().strip()
        name = self.cost_code_name_input.text().strip()
        if not code_str or not name:
            QMessageBox.warning(self, "Input Error", "Code and Name cannot be empty.")
            return

        try:
            code_to_update = self.db_session.query(CostCode).filter_by(id=code_id).first()
            if code_to_update:
                # Check for duplicate code if changed
                if code_to_update.code != code_str:
                    existing_code = self.db_session.query(CostCode).filter(CostCode.code == code_str).first()
                    if existing_code and existing_code.id != code_id:
                        QMessageBox.warning(self, "Duplicate Entry", f"A cost code '{code_str}' already exists.")
                        return

                selected_mf_group = None
                mf_group_text = self.mf_group_combo.currentText()
                if mf_group_text != "-- Select MF Division --":
                    selected_mf_group = self.mf_groups_map.get(mf_group_text)
                    if not selected_mf_group:
                        QMessageBox.critical(self, "Error", "Selected MasterFormat Division not found.")
                        return

                code_to_update.code = code_str
                code_to_update.name = name
                code_to_update.description = self.cost_code_description_input.toPlainText().strip() or None
                code_to_update.mf_group = selected_mf_group
                self.db_session.commit()
                QMessageBox.information(self, "Success", f"Cost code '{code_str}' updated.")
                self.load_cost_codes()
                self.clear_cost_code_form()
                self.data_updated_signal.emit()
            else:
                QMessageBox.warning(self, "Error", "Selected cost code not found.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to update cost code: {e}")
            print(f"DEBUG: Error updating cost code: {e}")

    def delete_cost_code(self):
        selected_rows = self.cost_codes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a cost code to delete.")
            return
        
        row = selected_rows[0].row()
        code_id = int(self.cost_codes_table.item(row, 0).text())
        code_str = self.cost_codes_table.item(row, 1).text()

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete cost code '{code_str}' (ID: {code_id})? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                code_to_delete = self.db_session.query(CostCode).filter_by(id=code_id).first()
                if code_to_delete:
                    self.db_session.delete(code_to_delete)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", f"Cost code '{code_str}' deleted.")
                    self.load_cost_codes()
                    self.clear_cost_code_form()
                    self.data_updated_signal.emit()
                else:
                    QMessageBox.warning(self, "Error", "Selected cost code not found.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete cost code: {e}")
                print(f"DEBUG: Error deleting cost code: {e}")

    def clear_cost_code_form(self):
        self.cost_code_code_input.clear()
        self.cost_code_name_input.clear()
        self.cost_code_description_input.clear()
        self.mf_group_combo.setCurrentIndex(0)
        self.cost_codes_table.clearSelection()
        self.add_cost_code_btn.setEnabled(True)
        self.update_cost_code_btn.setEnabled(False)
        self.delete_cost_code_btn.setEnabled(False)

    def closeEvent(self, event):
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    create_db_and_tables()
    session = Session()
    window = ManageCommonDataWindow(db_session=session)
    window.show()
    sys.exit(app.exec())