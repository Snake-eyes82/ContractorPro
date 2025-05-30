# src/general_info_view.py (FINAL REVISION FOR LAYOUT & QCOMBOBOX FIX)
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QDateEdit, QTextEdit, QGridLayout, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QDate, QSize, QObject
from datetime import date

from database import Session, Project

class GeneralInfoWindow(QMainWindow):
    project_updated_signal = Signal(int)

    def __init__(self, project_id=None, parent=None):
        super().__init__(parent)
        self.db_session = Session()
        self.current_project_id = project_id

        self.setWindowTitle("Project General Info")
        # Adjusted default size for more space (increased width and height)
        self.setGeometry(150, 150, 1000, 800)
        # Adjusted minimum size
        self.setMinimumSize(QSize(900, 700))

        self.init_ui()

        if self.current_project_id:
            self.load_project_data(self.current_project_id)
        else:
            self.clear_form_inputs()
            self.save_changes_button.setEnabled(False)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        main_layout.addWidget(QLabel("<h2>Project General Information</h2>", alignment=Qt.AlignCenter))

        # --- Main Grid Layout for Sections ---
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(15, 15, 15, 15)
        grid_layout.setSpacing(15) # Spacing between major sections

        # --- 1. Project Details Section ---
        project_details_group = QGroupBox("Project Details")
        project_details_layout = QFormLayout(project_details_group)
        project_details_layout.setContentsMargins(10, 20, 10, 10)
        project_details_layout.setSpacing(8)

        self.project_id_label = QLabel("N/A (New Project)")
        project_details_layout.addRow("Project ID:", self.project_id_label)
        self.project_name_input = QLineEdit()
        project_details_layout.addRow("Project Name:", self.project_name_input)

        grid_layout.addWidget(project_details_group, 0, 0, 1, 2) # Row 0, spanning 2 columns

        # --- 2. Client Information Section ---
        client_info_group = QGroupBox("Client Information")
        client_info_layout = QFormLayout(client_info_group)
        client_info_layout.setContentsMargins(10, 20, 10, 10)
        client_info_layout.setSpacing(8)

        self.client_name_input = QLineEdit()
        client_info_layout.addRow("Client Name:", self.client_name_input)
        self.client_contact_input = QLineEdit()
        client_info_layout.addRow("Contact Person:", self.client_contact_input)
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("e.g., 555-123-4567")
        client_info_layout.addRow("Phone:", self.client_phone_input)
        self.client_email_input = QLineEdit()
        self.client_email_input.setPlaceholderText("e.g., client@example.com")
        client_info_layout.addRow("Email:", self.client_email_input)

        grid_layout.addWidget(client_info_group, 1, 0) # Row 1, Column 0

        # --- 3. Client Address Section ---
        client_address_group = QGroupBox("Client Address")
        client_address_layout = QFormLayout(client_address_group)
        client_address_layout.setContentsMargins(10, 20, 10, 10)
        client_address_layout.setSpacing(8)

        self.client_address_street_input = QLineEdit()
        client_address_layout.addRow("Street:", self.client_address_street_input)
        self.client_address_city_input = QLineEdit()
        client_address_layout.addRow("City:", self.client_address_city_input)
        self.client_address_state_input = QLineEdit()
        client_address_layout.addRow("State:", self.client_address_state_input)
        self.client_address_zip_input = QLineEdit()
        client_address_layout.addRow("Zip Code:", self.client_address_zip_input)

        grid_layout.addWidget(client_address_group, 1, 1) # Row 1, Column 1

        # --- 4. Project Address Section ---
        project_address_group = QGroupBox("Project Address")
        project_address_layout = QFormLayout(project_address_group)
        project_address_layout.setContentsMargins(10, 20, 10, 10)
        project_address_layout.setSpacing(8)

        self.project_address_street_input = QLineEdit()
        project_address_layout.addRow("Street:", self.project_address_street_input)
        self.project_address_city_input = QLineEdit()
        project_address_layout.addRow("City:", self.project_address_city_input)
        self.project_address_state_input = QLineEdit()
        project_address_layout.addRow("State:", self.project_address_state_input)
        self.project_address_zip_input = QLineEdit()
        project_address_layout.addRow("Zip Code:", self.project_address_zip_input)

        grid_layout.addWidget(project_address_group, 2, 0) # Row 2, Column 0

        # --- 5. Dates, Status & Financial Percentages Section ---
        dates_status_financial_group = QGroupBox("Dates, Status & Percentages")
        dates_status_financial_layout = QFormLayout(dates_status_financial_group)
        dates_status_financial_layout.setContentsMargins(10, 20, 10, 10)
        dates_status_financial_layout.setSpacing(8)

        self.estimate_date_input = QDateEdit(calendarPopup=True)
        self.estimate_date_input.setDate(QDate.currentDate())
        dates_status_financial_layout.addRow("Estimate Date:", self.estimate_date_input)

        self.bid_due_date_input = QDateEdit(calendarPopup=True)
        self.bid_due_date_input.setDate(QDate.currentDate())
        dates_status_financial_layout.addRow("Bid Due Date:", self.bid_due_date_input)

        self.project_status_input = QComboBox()
        self.project_status_input.addItems(["New", "Estimate Sent", "Approved", "Rejected", "Completed", "Archived"])
        dates_status_financial_layout.addRow("Project Status:", self.project_status_input)

        self.contract_type_input = QComboBox()
        self.contract_type_input.addItems(["Fixed Price", "Time & Materials", "Cost-Plus", "Unit Price"])
        dates_status_financial_layout.addRow("Contract Type:", self.contract_type_input)

        # --- Markup, Overhead, Profit fields ---
        self.markup_percentage_input = QLineEdit()
        self.markup_percentage_input.setPlaceholderText("e.g., 10.0")
        dates_status_financial_layout.addRow("Markup %:", self.markup_percentage_input)

        self.overhead_percentage_input = QLineEdit()
        self.overhead_percentage_input.setPlaceholderText("e.g., 5.0")
        dates_status_financial_layout.addRow("Overhead %:", self.overhead_percentage_input)

        self.profit_percentage_input = QLineEdit()
        self.profit_percentage_input.setPlaceholderText("e.g., 15.0")
        dates_status_financial_layout.addRow("Profit %:", self.profit_percentage_input)

        grid_layout.addWidget(dates_status_financial_group, 2, 1) # Row 2, Column 1

        main_layout.addLayout(grid_layout)

        # --- 6. Scope of Work and Project Notes (Full Width) ---
        long_text_container = QWidget()
        long_text_layout = QHBoxLayout(long_text_container)
        long_text_layout.setContentsMargins(0, 0, 0, 0)
        long_text_layout.setSpacing(15)

        scope_group = QGroupBox("Scope of Work")
        scope_layout = QVBoxLayout(scope_group)
        self.scope_of_work_input = QTextEdit()
        self.scope_of_work_input.setPlaceholderText("Enter detailed scope of work here...")
        scope_layout.addWidget(self.scope_of_work_input)
        long_text_layout.addWidget(scope_group)

        notes_group = QGroupBox("Project Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.project_notes_input = QTextEdit()
        self.project_notes_input.setPlaceholderText("Enter any additional project notes here...")
        notes_layout.addWidget(self.project_notes_input)
        long_text_layout.addWidget(notes_group)

        main_layout.addWidget(long_text_container)

        main_layout.addSpacing(20)

        # --- Buttons for Form Actions ---
        form_buttons_layout = QHBoxLayout()
        form_buttons_layout.addStretch(1)

        self.save_changes_button = QPushButton("Save Changes")
        self.save_changes_button.clicked.connect(self.save_project_changes)
        self.save_changes_button.setEnabled(False)
        form_buttons_layout.addWidget(self.save_changes_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_form_inputs)
        form_buttons_layout.addWidget(self.clear_form_button)

        main_layout.addLayout(form_buttons_layout)
        main_layout.addStretch(1)

    def load_project_data(self, project_id: int):
        try:
            self.current_project_id = project_id
            project = self.db_session.query(Project).filter_by(project_id=project_id).first()

            if project:
                self.project_id_label.setText(str(project.project_id))
                self.project_name_input.setText(project.project_name or "")
                self.client_name_input.setText(project.client_name or "")
                self.client_contact_input.setText(project.client_contact or "")
                self.client_phone_input.setText(project.client_phone or "")
                self.client_email_input.setText(project.client_email or "")
                self.client_address_street_input.setText(project.client_address_street or "")
                self.client_address_city_input.setText(project.client_address_city or "")
                self.client_address_state_input.setText(project.client_address_state or "")
                self.client_address_zip_input.setText(project.client_address_zip or "")
                self.project_address_street_input.setText(project.project_address_street or "")
                self.project_address_city_input.setText(project.project_address_city or "")
                self.project_address_state_input.setText(project.project_address_state or "")
                self.project_address_zip_input.setText(project.project_address_zip or "")

                if project.estimate_date:
                    self.estimate_date_input.setDate(QDate(project.estimate_date.year, project.estimate_date.month, project.estimate_date.day))
                else:
                    self.estimate_date_input.setDate(QDate.currentDate())

                if project.bid_due_date:
                    self.bid_due_date_input.setDate(QDate(project.bid_due_date.year, project.bid_due_date.month, project.bid_due_date.day))
                else:
                    self.bid_due_date_input.setDate(QDate.currentDate())

                # CORRECTED: Use setCurrentText for QComboBox
                self.project_status_input.setCurrentText(project.project_status or "New")
                self.contract_type_input.setCurrentText(project.contract_type or "Fixed Price")

                self.markup_percentage_input.setText(str(project.markup_percentage) if project.markup_percentage is not None else "")
                self.overhead_percentage_input.setText(str(project.overhead_percentage) if project.overhead_percentage is not None else "")
                self.profit_percentage_input.setText(str(project.profit_percentage) if project.profit_percentage is not None else "")

                self.scope_of_work_input.setPlainText(project.scope_of_work or "")
                self.project_notes_input.setPlainText(project.project_notes or "")

                self.save_changes_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Load Error", f"Project with ID {project_id} not found in database.")
                self.clear_form_inputs()
                self.save_changes_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load project data: {e}")
            self.clear_form_inputs()
            self.save_changes_button.setEnabled(False)
            self.current_project_id = None

    def clear_form_inputs(self):
        self.project_id_label.setText("N/A (New Project)")
        self.project_name_input.clear()
        self.client_name_input.clear()
        self.client_contact_input.clear()
        self.client_phone_input.clear()
        self.client_email_input.clear()
        self.client_address_street_input.clear()
        self.client_address_city_input.clear()
        self.client_address_state_input.clear()
        self.client_address_zip_input.clear()
        self.project_address_street_input.clear()
        self.project_address_city_input.clear()
        self.project_address_state_input.clear()
        self.project_address_zip_input.clear()
        self.estimate_date_input.setDate(QDate.currentDate())
        self.bid_due_date_input.setDate(QDate.currentDate())
        self.project_status_input.setCurrentIndex(0)
        self.contract_type_input.setCurrentIndex(0)

        self.markup_percentage_input.clear()
        self.overhead_percentage_input.clear()
        self.profit_percentage_input.clear()

        self.scope_of_work_input.clear()
        self.project_notes_input.clear()

        self.save_changes_button.setEnabled(False)
        self.current_project_id = None

    def save_project_changes(self):
        if self.current_project_id is None:
            QMessageBox.warning(self, "Error", "No project selected to save changes.")
            return

        project_name = self.project_name_input.text().strip()
        client_name = self.client_name_input.text().strip()

        if not project_name or not client_name:
            QMessageBox.warning(self, "Input Error", "Project Name and Client Name cannot be empty.")
            return

        try:
            markup_percentage = float(self.markup_percentage_input.text().strip()) if self.markup_percentage_input.text().strip() else None
            overhead_percentage = float(self.overhead_percentage_input.text().strip()) if self.overhead_percentage_input.text().strip() else None
            profit_percentage = float(self.profit_percentage_input.text().strip()) if self.profit_percentage_input.text().strip() else None

            if markup_percentage is not None and (markup_percentage < 0 or markup_percentage > 100):
                QMessageBox.warning(self, "Input Error", "Markup percentage must be between 0 and 100.")
                return
            if overhead_percentage is not None and (overhead_percentage < 0 or overhead_percentage > 100):
                QMessageBox.warning(self, "Input Error", "Overhead percentage must be between 0 and 100.")
                return
            if profit_percentage is not None and (profit_percentage < 0 or profit_percentage > 100):
                QMessageBox.warning(self, "Input Error", "Profit percentage must be between 0 and 100.")
                return

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Markup, Overhead, and Profit percentages must be valid numbers.")
            return

        client_contact = self.client_contact_input.text().strip()
        client_phone = self.client_phone_input.text().strip()
        client_email = self.client_email_input.text().strip()
        client_address_street = self.client_address_street_input.text().strip()
        client_address_city = self.client_address_city_input.text().strip()
        client_address_state = self.client_address_state_input.text().strip()
        client_address_zip = self.client_address_zip_input.text().strip()
        project_address_street = self.project_address_street_input.text().strip()
        project_address_city = self.project_address_city_input.text().strip()
        project_address_state = self.project_address_state_input.text().strip()
        project_address_zip = self.project_address_zip_input.text().strip()
        estimate_date = self.estimate_date_input.date().toPython()
        bid_due_date = self.bid_due_date_input.date().toPython()
        project_status = self.project_status_input.currentText()
        contract_type = self.contract_type_input.currentText()
        scope_of_work = self.scope_of_work_input.toPlainText().strip()
        project_notes = self.project_notes_input.toPlainText().strip()

        if estimate_date > bid_due_date:
            QMessageBox.warning(self, "Input Error", "Estimate Date cannot be after Bid Due Date.")
            return

        try:
            project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
            if project:
                project.project_name = project_name
                project.client_name = client_name
                project.client_contact = client_contact if client_contact else None
                project.client_phone = client_phone if client_phone else None
                project.client_email = client_email if client_email else None
                project.client_address_street = client_address_street if client_address_street else None
                project.client_address_city = client_address_city if client_address_city else None
                project.client_address_state = client_address_state if client_address_state else None
                project.client_address_zip = client_address_zip if client_address_zip else None
                project.project_address_street = project_address_street if project_address_street else None
                project.project_address_city = project_address_city if project_address_city else None
                project.project_address_state = project_address_state if project_address_state else None
                project.project_address_zip = project_address_zip if project_address_zip else None
                project.estimate_date = estimate_date
                project.bid_due_date = bid_due_date
                project.project_status = project_status if project_status else None
                project.contract_type = contract_type if contract_type else None
                project.scope_of_work = scope_of_work if scope_of_work else None
                project.project_notes = project_notes if project_notes else None

                project.markup_percentage = markup_percentage
                project.overhead_percentage = overhead_percentage
                project.profit_percentage = profit_percentage

                self.db_session.commit()
                QMessageBox.information(self, "Success", "Project changes saved successfully!")
                self.project_updated_signal.emit(self.current_project_id)
                self.close()
            else:
                QMessageBox.warning(self, "Error", "Selected project not found in database.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save project changes: {e}")

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)

# -----------------------------------------------------------------------------
# Standalone testing block
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    from database import create_db_and_tables, Project, Session
    create_db_and_tables()

    session = Session()
    test_project = session.query(Project).first()
    if not test_project:
        new_project = Project(
            project_name="Sample Project for General Info Test",
            client_name="Test Client Co.",
            client_contact="Jane Doe",
            client_phone="111-222-3333",
            client_email="jane.doe@example.com",
            client_address_street="100 Main St",
            client_address_city="Anytown",
            client_address_state="FL",
            client_address_zip="12345",
            project_address_street="200 Work Rd",
            project_address_city="Workville",
            project_address_state="FL",
            project_address_zip="67890",
            estimate_date=date(2023, 1, 1),
            bid_due_date=date(2023, 1, 15),
            project_status="New",
            contract_type="Fixed Price",
            scope_of_work="Basic landscaping and patio installation.",
            project_notes="Phase 1: Excavation and concrete slab. Phase 2: Planting.",
            markup_percentage=10.0,
            overhead_percentage=5.0,
            profit_percentage=15.0
        )
        session.add(new_project)
        session.commit()
        test_project_id = new_project.project_id
    else:
        test_project_id = test_project.project_id
    session.close()

    window = GeneralInfoWindow(project_id=test_project_id)
    window.show()
    sys.exit(app.exec())