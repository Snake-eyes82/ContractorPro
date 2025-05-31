# src/general_info_view.py

import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDoubleSpinBox, QSpinBox, QPushButton, QHBoxLayout,
    QMessageBox, QDateEdit, QComboBox
)
from PySide6.QtCore import Signal, QDate, Qt
from src.database import Session, Project, create_db_and_tables

class GeneralInfoWindow(QDialog):
    project_updated_signal = Signal() # Signal to notify the dashboard to refresh

    def __init__(self, project_id, db_session, parent_dashboard=None):
        super().__init__(parent_dashboard)
        self.db_session = db_session
        self.project_id = project_id
        self.parent_dashboard = parent_dashboard # Reference to the main dashboard

        self.current_project = None
        if self.project_id:
            # Corrected: Filter by 'id' for the Project model
            self.current_project = self.db_session.query(Project).filter_by(id=self.project_id).first()

        self.setWindowTitle("Project General Information")
        self.setGeometry(200, 200, 800, 700) # Adjusted size for more fields

        self.init_ui()
        self.load_project_data() # No arguments needed here, uses self.current_project

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Project Details
        self.project_id_label = QLineEdit("ID: N/A (New Project)")
        self.project_id_label.setReadOnly(True)
        form_layout.addRow("Project ID:", self.project_id_label)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter Project Name (e.g., 'Smith Residence Renovation')")
        form_layout.addRow("Project Name:", self.project_name_input)

        # Client Information
        self.client_name_input = QLineEdit()
        form_layout.addRow("Client Name:", self.client_name_input)

        self.client_contact_person_input = QLineEdit()
        form_layout.addRow("Contact Person:", self.client_contact_person_input)

        self.client_phone_input = QLineEdit()
        form_layout.addRow("Phone:", self.client_phone_input)

        self.client_email_input = QLineEdit()
        form_layout.addRow("Email:", self.client_email_input)

        # Client Address
        self.client_address_street_input = QLineEdit()
        form_layout.addRow("Client Street:", self.client_address_street_input)
        self.client_address_city_input = QLineEdit()
        form_layout.addRow("Client City:", self.client_address_city_input)
        self.client_address_state_input = QLineEdit()
        form_layout.addRow("Client State:", self.client_address_state_input)
        self.client_address_zip_input = QLineEdit()
        form_layout.addRow("Client Zip Code:", self.client_address_zip_input)

        # Project Address
        self.project_address_input = QLineEdit()
        form_layout.addRow("Project Street:", self.project_address_input)
        self.project_city_input = QLineEdit()
        form_layout.addRow("Project City:", self.project_city_input)
        self.project_state_input = QLineEdit()
        form_layout.addRow("Project State:", self.project_state_input)
        self.project_zip_input = QLineEdit()
        form_layout.addRow("Project Zip Code:", self.project_zip_input)

        # Date Fields
        self.estimate_date_input = QDateEdit(calendarPopup=True)
        #self.estimate_date_input.setCalendarWidgetResizable(True)
        self.estimate_date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Estimate Date:", self.estimate_date_input)

        self.bid_due_date_input = QDateEdit(calendarPopup=True)
        #self.bid_due_date_input.setCalendarWidgetResizable(True)
        self.bid_due_date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Bid Due Date:", self.bid_due_date_input)

        self.project_start_date_input = QDateEdit(calendarPopup=True)
        #self.project_start_date_input.setCalendarWidgetResizable(True)
        self.project_start_date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Project Start Date:", self.project_start_date_input)

        self.completion_date_input = QDateEdit(calendarPopup=True)
        #self.completion_date_input.setCalendarWidgetResizable(True)
        self.completion_date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Completion Date:", self.completion_date_input)

        # Status and Type
        self.project_status_combo = QComboBox()
        self.project_status_combo.addItems(["Planned", "Active", "On Hold", "Completed", "Cancelled"])
        form_layout.addRow("Project Status:", self.project_status_combo)

        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems(["Fixed Price", "Time & Material", "Cost Plus", "Unit Price"])
        form_layout.addRow("Contract Type:", self.contract_type_combo)

        # Financial Percentages
        self.markup_percentage_spin = QDoubleSpinBox()
        self.markup_percentage_spin.setRange(0.00, 100.00)
        self.markup_percentage_spin.setSuffix("%")
        self.markup_percentage_spin.setDecimals(2)
        form_layout.addRow("Markup %:", self.markup_percentage_spin)

        self.overhead_percentage_spin = QDoubleSpinBox()
        self.overhead_percentage_spin.setRange(0.00, 100.00)
        self.overhead_percentage_spin.setSuffix("%")
        self.overhead_percentage_spin.setDecimals(2)
        form_layout.addRow("Overhead %:", self.overhead_percentage_spin)

        self.profit_percentage_spin = QDoubleSpinBox()
        self.profit_percentage_spin.setRange(0.00, 100.00)
        self.profit_percentage_spin.setSuffix("%")
        self.profit_percentage_spin.setDecimals(2)
        form_layout.addRow("Profit %:", self.profit_percentage_spin)

        # Text Areas
        self.scope_of_work_input = QTextEdit()
        form_layout.addRow("Scope of Work:", self.scope_of_work_input)

        self.notes_input = QTextEdit()
        form_layout.addRow("Project Notes:", self.notes_input)

        main_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_project_data)
        button_layout.addWidget(self.save_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_form_button)

        main_layout.addLayout(button_layout)

    def load_project_data(self):
        # This method uses self.current_project, which is already set in __init__
        if self.current_project:
            self.project_id_label.setText(f"ID: {self.current_project.id}")
            self.project_name_input.setText(self.current_project.project_name or "")
            self.client_name_input.setText(self.current_project.client_name or "")
            self.client_contact_person_input.setText(self.current_project.client_contact_person or "")
            self.client_phone_input.setText(self.current_project.client_phone or "")
            self.client_email_input.setText(self.current_project.client_email or "")

            self.client_address_street_input.setText(self.current_project.client_address_street or "")
            self.client_address_city_input.setText(self.current_project.client_address_city or "")
            self.client_address_state_input.setText(self.current_project.client_address_state or "")
            self.client_address_zip_input.setText(self.current_project.client_address_zip or "")

            self.project_address_input.setText(self.current_project.project_address or "")
            self.project_city_input.setText(self.current_project.project_city or "")
            self.project_state_input.setText(self.current_project.project_state or "")
            self.project_zip_input.setText(self.current_project.project_zip or "")

            # Set date fields from string
            if self.current_project.estimate_date:
                self.estimate_date_input.setDate(QDate.fromString(self.current_project.estimate_date, "yyyy-MM-dd"))
            if self.current_project.bid_due_date:
                self.bid_due_date_input.setDate(QDate.fromString(self.current_project.bid_due_date, "yyyy-MM-dd"))
            if self.current_project.project_start_date:
                self.project_start_date_input.setDate(QDate.fromString(self.current_project.project_start_date, "yyyy-MM-dd"))
            if self.current_project.completion_date:
                self.completion_date_input.setDate(QDate.fromString(self.current_project.completion_date, "yyyy-MM-dd"))

            self.project_status_combo.setCurrentText(self.current_project.project_status or "")
            self.contract_type_combo.setCurrentText(self.current_project.contract_type or "")

            self.markup_percentage_spin.setValue(self.current_project.markup_percentage if self.current_project.markup_percentage is not None else 0.0)
            self.overhead_percentage_spin.setValue(self.current_project.overhead_percentage if self.current_project.overhead_percentage is not None else 0.0)
            self.profit_percentage_spin.setValue(self.current_project.profit_percentage if self.current_project.profit_percentage is not None else 0.0)

            self.scope_of_work_input.setText(self.current_project.scope_of_work or "")
            self.notes_input.setText(self.current_project.notes or "")
        else:
            # Set default dates for new projects to today
            today = QDate.currentDate()
            self.estimate_date_input.setDate(today)
            self.bid_due_date_input.setDate(today)
            self.project_start_date_input.setDate(today)
            self.completion_date_input.setDate(today.addMonths(6)) # Default 6 months from now

    def save_project_data(self):
        project_name = self.project_name_input.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Input Error", "Project Name cannot be empty.")
            return

        try:
            if self.current_project:
                # Update existing project
                self.current_project.project_name = project_name
                self.current_project.client_name = self.client_name_input.text().strip() or None
                self.current_project.client_contact_person = self.client_contact_person_input.text().strip() or None
                self.current_project.client_phone = self.client_phone_input.text().strip() or None
                self.current_project.client_email = self.client_email_input.text().strip() or None

                self.current_project.client_address_street = self.client_address_street_input.text().strip() or None
                self.current_project.client_address_city = self.client_address_city_input.text().strip() or None
                self.current_project.client_address_state = self.client_address_state_input.text().strip() or None
                self.current_project.client_address_zip = self.client_address_zip_input.text().strip() or None

                self.current_project.project_address = self.project_address_input.text().strip() or None
                self.current_project.project_city = self.project_city_input.text().strip() or None
                self.current_project.project_state = self.project_state_input.text().strip() or None
                self.current_project.project_zip = self.project_zip_input.text().strip() or None

                # Convert QDate to string for saving
                self.current_project.estimate_date = self.estimate_date_input.date().toString("yyyy-MM-dd")
                self.current_project.bid_due_date = self.bid_due_date_input.date().toString("yyyy-MM-dd")
                self.current_project.project_start_date = self.project_start_date_input.date().toString("yyyy-MM-dd")
                self.current_project.completion_date = self.completion_date_input.date().toString("yyyy-MM-dd")

                self.current_project.project_status = self.project_status_combo.currentText() or None
                self.current_project.contract_type = self.contract_type_combo.currentText() or None

                self.current_project.markup_percentage = self.markup_percentage_spin.value()
                self.current_project.overhead_percentage = self.overhead_percentage_spin.value()
                self.current_project.profit_percentage = self.profit_percentage_spin.value()

                self.current_project.scope_of_work = self.scope_of_work_input.toPlainText().strip() or None
                self.current_project.notes = self.notes_input.toPlainText().strip() or None

                self.db_session.commit()
                QMessageBox.information(self, "Success", f"Project '{project_name}' updated successfully.")
            else:
                # Create new project
                new_project = Project(
                    project_name=project_name,
                    client_name=self.client_name_input.text().strip() or None,
                    client_contact_person=self.client_contact_person_input.text().strip() or None,
                    client_phone=self.client_phone_input.text().strip() or None,
                    client_email=self.client_email_input.text().strip() or None,

                    client_address_street=self.client_address_street_input.text().strip() or None,
                    client_address_city=self.client_address_city_input.text().strip() or None,
                    client_address_state=self.client_address_state_input.text().strip() or None,
                    client_address_zip=self.client_address_zip_input.text().strip() or None,

                    project_address=self.project_address_input.text().strip() or None,
                    project_city=self.project_city_input.text().strip() or None,
                    project_state=self.project_state_input.text().strip() or None,
                    project_zip=self.project_zip_input.text().strip() or None,

                    estimate_date=self.estimate_date_input.date().toString("yyyy-MM-dd"),
                    bid_due_date=self.bid_due_date_input.date().toString("yyyy-MM-dd"),
                    project_start_date=self.project_start_date_input.date().toString("yyyy-MM-dd"),
                    completion_date=self.completion_date_input.date().toString("yyyy-MM-dd"),

                    project_status=self.project_status_combo.currentText() or None,
                    contract_type=self.contract_type_combo.currentText() or None,

                    markup_percentage=self.markup_percentage_spin.value(),
                    overhead_percentage=self.overhead_percentage_spin.value(),
                    profit_percentage=self.profit_percentage_spin.value(),

                    scope_of_work=self.scope_of_work_input.toPlainText().strip() or None,
                    notes=self.notes_input.toPlainText().strip() or None,

                    # Initialize other financial fields as 0.0 or None as appropriate for new projects
                    contract_date=None,
                    project_description=None,
                    contract_amount=0.0,
                    payment_terms=None,
                    change_orders_total=0.0,
                    current_contract_amount=0.0,
                    tax_rate=0.0,
                    permit_cost=0.0,
                    bonding_cost=0.0,
                    insurance_cost=0.0,
                    misc_expenses=0.0,
                    estimated_total_cost=0.0,
                    final_total_cost=0.0,
                    total_direct_cost=0.0,
                    final_project_estimate=0.0
                )
                self.db_session.add(new_project)
                self.db_session.commit()
                self.project_id = new_project.id # Set the ID for the newly created project
                self.current_project = new_project
                self.project_id_label.setText(f"ID: {self.current_project.id}")
                QMessageBox.information(self, "Success", f"New Project '{project_name}' created successfully.")

            self.project_updated_signal.emit() # Emit signal to refresh dashboard
            self.accept() # Close the dialog

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save project: {e}\nCheck console for details.")
            print(f"DEBUG: Error saving project: {e}")

    def clear_form(self):
        self.project_name_input.clear()
        self.client_name_input.clear()
        self.client_contact_person_input.clear()
        self.client_phone_input.clear()
        self.client_email_input.clear()
        self.client_address_street_input.clear()
        self.client_address_city_input.clear()
        self.client_address_state_input.clear()
        self.client_address_zip_input.clear()
        self.project_address_input.clear()
        self.project_city_input.clear()
        self.project_state_input.clear()
        self.project_zip_input.clear()
        
        today = QDate.currentDate()
        self.estimate_date_input.setDate(today)
        self.bid_due_date_input.setDate(today)
        self.project_start_date_input.setDate(today)
        self.completion_date_input.setDate(today.addMonths(6))

        self.project_status_combo.setCurrentIndex(0)
        self.contract_type_combo.setCurrentIndex(0)

        self.markup_percentage_spin.setValue(0.0)
        self.overhead_percentage_spin.setValue(0.0)
        self.profit_percentage_spin.setValue(0.0)

        self.scope_of_work_input.clear()
        self.notes_input.clear()

        self.project_id = None
        self.current_project = None
        self.project_id_label.setText("ID: N/A (New Project)")

    def reject(self):
        # Override reject to ensure session is closed if dialog is closed without saving
        if self.db_session:
            self.db_session.close()
        super().reject()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    create_db_and_tables() # Ensure DB is ready
    session = Session()
    # Example usage for testing: open an existing project or a new one
    # To open an existing project (e.g., ID 1):
    # window = GeneralInfoWindow(project_id=1, db_session=session)
    # To open a new project:
    window = GeneralInfoWindow(project_id=None, db_session=session)
    window.show()
    sys.exit(app.exec())