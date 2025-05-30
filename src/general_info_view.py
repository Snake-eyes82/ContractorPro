# src/general_info_view.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QFormLayout,
    QDateEdit, QTextEdit, QGridLayout, QGroupBox, QComboBox,
    QDoubleSpinBox # IMPORTANT: Add QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QDate, QSize # QObject is not strictly needed for this class
from datetime import date # Keep datetime.date for toPython() conversion

from src.database import Session, Project # Assuming Session and Project are imported correctly

class GeneralInfoWindow(QMainWindow):
    project_updated_signal = Signal() # Removed (int) as we just need to signal a refresh, not pass ID back

    def __init__(self, project_id=None, db_session=None, parent_dashboard=None): # Added db_session and parent_dashboard
        super().__init__()
        self.db_session = db_session if db_session is not None else Session() # Use provided session or create new
        self.parent_dashboard = parent_dashboard # Store reference to the main dashboard

        self.current_project_id = project_id # None for new project, ID for existing

        self.setWindowTitle("Project General Info")
        self.setGeometry(150, 150, 1000, 800)
        self.setMinimumSize(QSize(900, 700))

        self.init_ui() # Set up UI elements first

        # Initialize form for new or existing project
        if self.current_project_id is not None:
            self.project_id_label.setText(f"ID: {self.current_project_id}") # Update label if ID is provided
            self.load_project_data(self.current_project_id)
            self.save_changes_button.setEnabled(True) # Enable for existing project
        else:
            # For a new project, display "N/A (New Project)" and clear form
            self.project_id_label.setText("ID: N/A (New Project)")
            self.clear_form_inputs()
            self.save_changes_button.setEnabled(True) # ALWAYS ENABLE FOR NEW PROJECT TO ALLOW SAVING

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

        self.project_start_date_input = QDateEdit(calendarPopup=True)
        self.project_start_date_input.setDate(QDate.currentDate()) # Default to current date
        dates_status_financial_layout.addRow("Project Start Date:", self.project_start_date_input)

        self.expected_completion_date_input = QDateEdit(calendarPopup=True)
        self.expected_completion_date_input.setDate(QDate.currentDate().addYears(1)) # Default to 1 year from now, or adjust as needed
        dates_status_financial_layout.addRow("Expected Completion Date:", self.expected_completion_date_input)

        self.project_status_input = QComboBox()
        self.project_status_input.addItems(["New", "Estimate Sent", "Approved", "Rejected", "Completed", "Archived"])
        dates_status_financial_layout.addRow("Project Status:", self.project_status_input)

        self.contract_type_input = QComboBox()
        self.contract_type_input.addItems(["Fixed Price", "Time & Materials", "Cost-Plus", "Unit Price"])
        dates_status_financial_layout.addRow("Contract Type:", self.contract_type_input)

        # --- Markup, Overhead, Profit fields (Now QDoubleSpinBox) ---
        self.markup_percentage_input = QDoubleSpinBox() # Changed to QDoubleSpinBox
        self.markup_percentage_input.setSuffix("%")
        self.markup_percentage_input.setRange(0.0, 100.0) # Set range 0-100%
        self.markup_percentage_input.setSingleStep(0.1)
        dates_status_financial_layout.addRow("Markup %:", self.markup_percentage_input)

        self.overhead_percentage_input = QDoubleSpinBox() # Changed to QDoubleSpinBox
        self.overhead_percentage_input.setSuffix("%")
        self.overhead_percentage_input.setRange(0.0, 100.0)
        self.overhead_percentage_input.setSingleStep(0.1)
        dates_status_financial_layout.addRow("Overhead %:", self.overhead_percentage_input)

        self.profit_percentage_input = QDoubleSpinBox() # Changed to QDoubleSpinBox
        self.profit_percentage_input.setSuffix("%")
        self.profit_percentage_input.setRange(0.0, 100.0)
        self.profit_percentage_input.setSingleStep(0.1)
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
        # self.save_changes_button.setEnabled() is now handled in __init__
        form_buttons_layout.addWidget(self.save_changes_button)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_form_inputs)
        form_buttons_layout.addWidget(self.clear_form_button)

        main_layout.addLayout(form_buttons_layout)
        main_layout.addStretch(1)

    def load_project_data(self, project_id: int):
        try:
            # current_project_id is already set in __init__
            project = self.db_session.query(Project).filter_by(project_id=project_id).first()

            if project:
                self.project_id_label.setText(f"ID: {project.project_id}") # Display actual ID
                self.project_name_input.setText(project.project_name or "")
                self.client_name_input.setText(project.client_name or "")
                self.client_contact_input.setText(project.client_contact_person or "")
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

                # Set dates, handling potential None
                self.estimate_date_input.setDate(QDate(project.estimate_date) if project.estimate_date else QDate.currentDate())
                self.bid_due_date_input.setDate(QDate(project.bid_due_date) if project.bid_due_date else QDate.currentDate())
                self.project_start_date_input.setDate(QDate(project.project_start_date) if project.project_start_date else QDate.currentDate())
                self.expected_completion_date_input.setDate(QDate(project.expected_completion_date) if project.expected_completion_date else QDate.currentDate().addYears(1))

                # Use setCurrentText for QComboBox
                self.project_status_input.setCurrentText(project.project_status or "New")
                self.contract_type_input.setCurrentText(project.contract_type or "Fixed Price")

                # Set QDoubleSpinBox values
                self.markup_percentage_input.setValue(project.markup_percentage if project.markup_percentage is not None else 0.0)
                self.overhead_percentage_input.setValue(project.overhead_percentage if project.overhead_percentage is not None else 0.0)
                self.profit_percentage_input.setValue(project.profit_percentage if project.profit_percentage is not None else 0.0)

                self.scope_of_work_input.setPlainText(project.scope_of_work or "")
                self.project_notes_input.setPlainText(project.project_notes or "")

                # No need to setEnabled(True) here, it's already done in __init__ for existing projects
            else:
                QMessageBox.warning(self, "Load Error", f"Project with ID {project_id} not found in database.")
                self.clear_form_inputs() # If not found, revert to new project state
                self.save_changes_button.setEnabled(True) # Re-enable for new project entry
                self.current_project_id = None # Crucial: Indicate it's now a new project
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load project data: {e}")
            self.clear_form_inputs()
            self.save_changes_button.setEnabled(True) # Re-enable for new project entry
            self.current_project_id = None # Crucial: Indicate it's now a new project

    def clear_form_inputs(self):
        self.project_id_label.setText("ID: N/A (New Project)") # Set label for new project
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
        self.project_start_date_input.setDate(QDate.currentDate())
        self.expected_completion_date_input.setDate(QDate.currentDate().addYears(1))

        self.project_status_input.setCurrentIndex(0) # Reset to first item
        self.contract_type_input.setCurrentIndex(0) # Reset to first item

        self.markup_percentage_input.setValue(0.0) # Reset QDoubleSpinBox to 0.0
        self.overhead_percentage_input.setValue(0.0)
        self.profit_percentage_input.setValue(0.0)

        self.scope_of_work_input.clear()
        self.project_notes_input.clear()

        # Crucial: Reset current_project_id to None when clearing, preparing for a new project
        self.current_project_id = None
        # Ensure save button is enabled to allow adding a new project
        self.save_changes_button.setEnabled(True)


    def save_project_changes(self):
        project_name = self.project_name_input.text().strip()
        client_name = self.client_name_input.text().strip()

        if not project_name or not client_name:
            QMessageBox.warning(self, "Input Error", "Project Name and Client Name cannot be empty.")
            return

        # Retrieve values from QDoubleSpinBox directly
        markup_percentage = self.markup_percentage_input.value()
        overhead_percentage = self.overhead_percentage_input.value()
        profit_percentage = self.profit_percentage_input.value()

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
        estimate_date = self.estimate_date_input.date().toPython() # toPyDate() for datetime.date object
        bid_due_date = self.bid_due_date_input.date().toPython()
        project_start_date = self.project_start_date_input.date().toPython()
        expected_completion_date = self.expected_completion_date_input.date().toPython()
        project_status = self.project_status_input.currentText()
        contract_type = self.contract_type_input.currentText()
        scope_of_work = self.scope_of_work_input.toPlainText().strip()
        project_notes = self.project_notes_input.toPlainText().strip()

        if estimate_date > bid_due_date:
            QMessageBox.warning(self, "Input Error", "Estimate Date cannot be after Bid Due Date.")
            return

        try:
            if self.current_project_id is None:
                # Add NEW project
                new_project = Project(
                    project_name=project_name,
                    client_name=client_name,
                    client_contact_person=client_contact if client_contact else None,
                    client_phone=client_phone if client_phone else None,
                    client_email=client_email if client_email else None,
                    client_address_street=client_address_street if client_address_street else None,
                    client_address_city=client_address_city if client_address_city else None,
                    client_address_state=client_address_state if client_address_state else None,
                    client_address_zip=client_address_zip if client_address_zip else None,
                    project_address_street=project_address_street if project_address_street else None,
                    project_address_city=project_address_city if project_address_city else None,
                    project_address_state=project_address_state if project_address_state else None,
                    project_address_zip=project_address_zip if project_address_zip else None,
                    estimate_date=estimate_date,
                    bid_due_date=bid_due_date,
                    project_start_date=project_start_date,
                    expected_completion_date=expected_completion_date,
                    project_status=project_status,
                    contract_type=contract_type,
                    markup_percentage=markup_percentage,
                    overhead_percentage=overhead_percentage,
                    profit_percentage=profit_percentage,
                    scope_of_work=scope_of_work if scope_of_work else None,
                    project_notes=project_notes if project_notes else None
                )
                self.db_session.add(new_project)
                self.db_session.commit()
                self.current_project_id = new_project.project_id # CRITICAL: Update current_project_id with the new ID
                QMessageBox.information(self, "Success", f"Project '{project_name}' added successfully! ID: {self.current_project_id}")
                self.project_id_label.setText(f"ID: {self.current_project_id}") # Update the label on the form

            else:
                # Update EXISTING project
                project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
                if project:
                    project.project_name = project_name
                    project.client_name = client_name
                    project.client_contact_person = client_contact if client_contact else None
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
                    project.project_start_date = project_start_date
                    project.expected_completion_date = expected_completion_date
                    project.project_status = project_status if project_status else None
                    project.contract_type = contract_type if contract_type else None
                    project.markup_percentage = markup_percentage
                    project.overhead_percentage = overhead_percentage
                    project.profit_percentage = profit_percentage
                    project.scope_of_work = scope_of_work if scope_of_work else None
                    project.project_notes = project_notes if project_notes else None

                    self.db_session.commit()
                    QMessageBox.information(self, "Success", f"Project '{project_name}' updated successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Project not found for update. It might have been deleted.")

            self.project_updated_signal.emit() # Emit signal to notify dashboard to refresh
            # It's generally better to let the calling window (dashboard) handle closing,
            # but if you always want it to close after saving, keep this line:
            # self.close()

        except Exception as e:
            self.db_session.rollback() # Rollback in case of error
            QMessageBox.critical(self, "Database Error", f"Failed to save project: {e}\nCheck console for details.")
            print(f"DEBUG: Database Error: {e}") # For more detailed debugging

    def closeEvent(self, event):
        # Close the database session when the window is closed
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)