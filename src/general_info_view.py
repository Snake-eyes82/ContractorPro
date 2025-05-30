# src/general_info_view.py

import sys, os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QMessageBox, QFormLayout, QLineEdit, QLabel, QDateEdit, QComboBox,
    QTextEdit, QHBoxLayout, QDoubleSpinBox, QGroupBox # QDoubleSpinBox still imported but not used in UI
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QDoubleValidator

from src.database import SessionLocal, Project
from datetime import date

class GeneralInfoWindow(QMainWindow):
    project_updated_signal = Signal() # Signal to notify the main app

    def __init__(self, project_id: int | None, parent=None):
        super().__init__(parent)
        self.db_session = SessionLocal()
        self.current_project_id = project_id
        self.project = None # To hold the project object

        self.setWindowTitle("Project General Info") # Generic title initially
        # Adjusted size again, as we're removing financial section
        self.setGeometry(200, 200, 850, 850) # Reduced height slightly
        self.setMinimumSize(700, 900) # Reduced min height

        self.init_ui()
        self.load_project_data() # Load data or initialize new project
        self.populate_form()     # Populate form fields after loading/initializing

    def load_project_data(self):
        """
        Loads project details if self.current_project_id is not None.
        Otherwise, initializes a new empty Project object for creation.
        """
        if self.current_project_id is not None:
            try:
                self.project = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
                if not self.project:
                    QMessageBox.critical(self, "Error", f"Project with ID {self.current_project_id} not found.")
                    self.close()
                    return
                self.setWindowTitle(f"Project General Info - {self.project.project_name}")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to load project details: {e}")
                self.close()
        else:
            # Initialize a new, empty Project object for the form
            self.project = Project(
                project_name="", client_name="",
                estimate_date=date.today(), bid_due_date=date.today(),
                project_status="New", contract_type="Fixed Price",
                # Initialize financial percentages to 0.0 by default for new projects
                markup_percentage=0.0, overhead_percentage=0.0, profit_percentage=0.0
                # Other fields will default to None/empty strings from the model
            )
            self.setWindowTitle("Project General Info - New Project")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(QLabel("<h2>Project General Information</h2>", alignment=Qt.AlignCenter))

        # --- General Info Group (Includes Project Name & Client Name) ---
        general_info_group = QGroupBox("General Info")
        general_info_layout = QFormLayout(general_info_group)
        general_info_layout.setContentsMargins(10, 20, 10, 10)
        general_info_layout.setSpacing(8)

        self.project_id_label = QLabel("Project ID: New (Will be assigned)")
        general_info_layout.addRow("Project ID:", self.project_id_label)

        self.project_name_input = QLineEdit()
        general_info_layout.addRow("Project Name:", self.project_name_input)

        self.client_name_input = QLineEdit()
        general_info_layout.addRow("Client Name:", self.client_name_input)

        self.client_contact_input = QLineEdit()
        general_info_layout.addRow("Client Contact:", self.client_contact_input)

        self.client_phone_input = QLineEdit()
        general_info_layout.addRow("Client Phone:", self.client_phone_input)

        self.client_email_input = QLineEdit()
        general_info_layout.addRow("Client Email:", self.client_email_input)

        main_layout.addWidget(general_info_group)
        main_layout.addSpacing(15)

        # --- Project Address Group ---
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
        project_address_layout.addRow("ZIP:", self.project_address_zip_input)

        main_layout.addWidget(project_address_group)
        main_layout.addSpacing(15)

        # --- Schedule & Status Group ---
        schedule_status_group = QGroupBox("Schedule & Status")
        schedule_status_layout = QFormLayout(schedule_status_group)
        schedule_status_layout.setContentsMargins(10, 20, 10, 10)
        schedule_status_layout.setSpacing(8)

        self.estimate_date_input = QDateEdit(calendarPopup=True)
        self.estimate_date_input.setDate(QDate.currentDate())
        schedule_status_layout.addRow("Estimate Date:", self.estimate_date_input)

        self.bid_due_date_input = QDateEdit(calendarPopup=True)
        self.bid_due_date_input.setDate(QDate.currentDate())
        schedule_status_layout.addRow("Bid Due Date:", self.bid_due_date_input)

        self.project_status_combo = QComboBox()
        self.project_status_combo.addItems(["New", "Bidding", "Active", "On Hold", "Completed", "Canceled"])
        schedule_status_layout.addRow("Project Status:", self.project_status_combo)

        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems(["Fixed Price", "Time & Materials", "Cost Plus", "Unit Price"])
        schedule_status_layout.addRow("Contract Type:", self.contract_type_combo)

        main_layout.addWidget(schedule_status_group)
        main_layout.addSpacing(15)

        # --- Scope of Work & Notes Group ---
        scope_notes_group = QGroupBox("Scope & Notes")
        scope_notes_layout = QVBoxLayout(scope_notes_group)
        scope_notes_layout.setContentsMargins(10, 20, 10, 10)
        scope_notes_layout.setSpacing(8)

        scope_notes_layout.addWidget(QLabel("Scope of Work:"))
        self.scope_of_work_input = QTextEdit()
        self.scope_of_work_input.setFixedHeight(70) # Compact height
        scope_notes_layout.addWidget(self.scope_of_work_input)

        scope_notes_layout.addWidget(QLabel("Project Notes:"))
        self.project_notes_input = QTextEdit()
        self.project_notes_input.setFixedHeight(70) # Compact height
        scope_notes_layout.addWidget(self.project_notes_input)

        main_layout.addWidget(scope_notes_group)
        main_layout.addStretch(1) # Pushes content up

        # --- Save Button ---
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch(1)
        self.save_button = QPushButton("Save Project Details")
        self.save_button.clicked.connect(self.save_project_data)
        save_button_layout.addWidget(self.save_button)
        save_button_layout.addStretch(1)
        main_layout.addLayout(save_button_layout)


    def populate_form(self):
        """Populates the form fields with current project data."""
        if self.project:
            if self.project.project_id:
                self.project_id_label.setText(f"Project ID: {self.project.project_id}")
                self.setWindowTitle(f"Project General Info - {self.project.project_name}")
            else:
                self.project_id_label.setText("Project ID: New (Will be assigned)")
                self.setWindowTitle("Project General Info - New Project")

            self.project_name_input.setText(self.project.project_name or "")
            self.client_name_input.setText(self.project.client_name or "")
            self.client_contact_input.setText(self.project.client_contact or "")
            self.client_phone_input.setText(self.project.client_phone or "")
            self.client_email_input.setText(self.project.client_email or "")

            self.project_address_street_input.setText(self.project.project_address_street or "")
            self.project_address_city_input.setText(self.project.project_address_city or "")
            self.project_address_state_input.setText(self.project.project_address_state or "")
            self.project_address_zip_input.setText(self.project.project_address_zip or "")

            if self.project.estimate_date:
                self.estimate_date_input.setDate(QDate(self.project.estimate_date))
            else:
                self.estimate_date_input.setDate(QDate.currentDate())

            if self.project.bid_due_date:
                self.bid_due_date_input.setDate(QDate(self.project.bid_due_date))
            else:
                self.bid_due_date_input.setDate(QDate.currentDate())

            self.project_status_combo.setCurrentText(self.project.project_status or "New")
            self.contract_type_combo.setCurrentText(self.project.contract_type or "Fixed Price")

            self.scope_of_work_input.setText(self.project.scope_of_work or "")
            self.project_notes_input.setText(self.project.project_notes or "")

            # REMOVED: Financial percentage inputs
            # self.markup_percentage_input.setValue(self.project.markup_percentage if self.project.markup_percentage is not None else 0.0)
            # self.overhead_percentage_input.setValue(self.project.overhead_percentage if self.project.overhead_percentage is not None else 0.0)
            # self.profit_percentage_input.setValue(self.project.profit_percentage if self.project.profit_percentage is not None else 0.0)


    def save_project_data(self):
        """Saves current form data to the database, either updating an existing project or creating a new one."""
        project_name = self.project_name_input.text().strip()
        client_name = self.client_name_input.text().strip()

        if not project_name or not client_name:
            QMessageBox.warning(self, "Input Error", "Project Name and Client Name are required.")
            return

        try:
            if self.project.project_id is None: # This is a new project
                new_project = Project(
                    project_name=project_name,
                    client_name=client_name,
                    client_contact=self.client_contact_input.text().strip() or None,
                    client_phone=self.client_phone_input.text().strip() or None,
                    client_email=self.client_email_input.text().strip() or None,
                    # Client address fields are intentionally not in this UI
                    client_address_street=None,
                    client_address_city=None,
                    client_address_state=None,
                    client_address_zip=None,
                    # Project address fields are included
                    project_address_street=self.project_address_street_input.text().strip() or None,
                    project_address_city=self.project_address_city_input.text().strip() or None,
                    project_address_state=self.project_address_state_input.text().strip() or None,
                    project_address_zip=self.project_address_zip_input.text().strip() or None,
                    estimate_date=self.estimate_date_input.date().toPython(),
                    bid_due_date=self.bid_due_date_input.date().toPython(),
                    project_status=self.project_status_combo.currentText(),
                    contract_type=self.contract_type_combo.currentText(),
                    scope_of_work=self.scope_of_work_input.toPlainText().strip() or None,
                    project_notes=self.project_notes_input.toPlainText().strip() or None,
                    # Initialize financial percentages to 0.0 for new projects if not provided by UI
                    markup_percentage=0.0,
                    overhead_percentage=0.0,
                    profit_percentage=0.0
                )
                self.db_session.add(new_project)
                self.db_session.commit()
                self.current_project_id = new_project.project_id # Update current_project_id
                self.project = new_project # Update the internal project object
                QMessageBox.information(self, "Success", "New project created successfully!")
                self.populate_form() # Refresh form to show new ID etc.

            else: # Updating an existing project
                self.project.project_name = project_name
                self.project.client_name = client_name
                self.project.client_contact = self.client_contact_input.text().strip() or None
                self.project.client_phone = self.client_phone_input.text().strip() or None
                self.project.client_email = self.client_email_input.text().strip() or None
                # Client address fields are not in UI, their existing values in DB will remain.
                # Project address fields are updated
                self.project.project_address_street = self.project_address_street_input.text().strip() or None
                self.project.project_address_city = self.project_address_city_input.text().strip() or None
                self.project.project_address_state = self.project_address_state_input.text().strip() or None
                self.project.project_address_zip = self.project_address_zip_input.text().strip() or None
                self.project.estimate_date = self.estimate_date_input.date().toPython()
                self.project.bid_due_date = self.bid_due_date_input.date().toPython()
                self.project.project_status = self.project_status_combo.currentText()
                self.project.contract_type = self.contract_type_combo.currentText()
                self.project.scope_of_work = self.scope_of_work_input.toPlainText().strip() or None
                self.project.project_notes = self.project_notes_input.toPlainText().strip() or None
                # REMOVED: Financial percentages are not updated from this UI, their existing values persist.
                # self.project.markup_percentage = self.markup_percentage_input.value()
                # self.project.overhead_percentage = self.overhead_percentage_input.value()
                # self.project.profit_percentage = self.profit_percentage_input.value()

                self.db_session.commit()
                QMessageBox.information(self, "Success", "Project updated successfully!")

            self.project_updated_signal.emit() # Notify main window to refresh
            self.close() # Close after saving/updating for cleaner workflow

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save project: {e}")

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)