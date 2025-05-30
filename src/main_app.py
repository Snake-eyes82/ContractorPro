# src/main_app.py

import sys
import os
from datetime import date # Make sure 'date' is imported for date.today()

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Add the 'src' directory (or the directory containing your modules) to the Python path
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout,
    QLabel, QLineEdit, QFormLayout # Added QLineEdit and QFormLayout for the "Add New Project" section
)
from PySide6.QtCore import Qt, Signal, QSize, QObject

from database import Session, Project, create_db_and_tables, EstimateLineItem
from general_info_view import GeneralInfoWindow
from estimate_line_items_view import EstimateLineItemsWindow

# project_options_dialog is no longer explicitly needed if you have direct buttons
# from project_options_dialog import ProjectOptionsDialog # <-- REMOVE THIS if you're not using it for the new flow

class ContractorProApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_session = Session()
        self.setWindowTitle("ContractorPro Estimator - Main Dashboard") # Set window title from screenshot
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(QSize(800, 600))

        self.open_general_info_windows = {} # To track open GeneralInfoWindow instances by project_id
        self.open_estimate_line_items_windows = {} # To track open EstimateLineItemsView instances by project_id

        self.init_ui()
        self.load_projects() # Load projects into the dashboard table

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- "Add New Project" Section (matching the top of the dashboard image) ---
        add_project_group_box = QWidget()
        add_project_layout = QFormLayout(add_project_group_box)
        add_project_layout.setContentsMargins(10, 10, 10, 10) # Add padding
        add_project_layout.setSpacing(8)

        add_project_layout.addRow(QLabel("<h3>Add New Project:</h3>"))

        self.new_project_name_input = QLineEdit()
        add_project_layout.addRow("Project Name:", self.new_project_name_input)

        self.new_client_name_input = QLineEdit()
        add_project_layout.addRow("Client Name:", self.new_client_name_input)

        self.new_client_phone_input = QLineEdit()
        add_project_layout.addRow("Client Phone:", self.new_client_phone_input)

        self.new_project_address_input = QLineEdit() # Simplified for the dashboard form
        add_project_layout.addRow("Project Address:", self.new_project_address_input)

        self.add_new_project_button = QPushButton("Add New Project")
        self.add_new_project_button.clicked.connect(self._add_new_project_from_form) # New method name
        add_project_layout.addRow(self.add_new_project_button)

        main_layout.addWidget(add_project_group_box)
        main_layout.addSpacing(20) # Space between add section and table

        # --- "Existing Projects" Table ---
        main_layout.addWidget(QLabel("<h3>Existing Projects:</h3>"))
        self.projects_table = QTableWidget()
        # Columns based on the screenshot: ID, Project Name, Client Name, Est. Date
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels(["ID", "Project Name", "Client Name", "Est. Date"])
        self.projects_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.projects_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.projects_table.setSelectionMode(QTableWidget.SingleSelection) # Allow only single selection
        self.projects_table.setEditTriggers(QTableWidget.NoEditTriggers) # Make table read-only
        main_layout.addWidget(self.projects_table)
        main_layout.addSpacing(20) # Space between table and buttons

        # --- Action Buttons (matching the bottom of the dashboard image) ---
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch(1) # Push buttons to the right

        self.open_general_info_button = QPushButton("Open General Info")
        self.open_general_info_button.clicked.connect(self._open_general_info_for_selected_project)
        self.open_general_info_button.setEnabled(False) # Disabled until project selected
        action_buttons_layout.addWidget(self.open_general_info_button)

        self.open_line_items_button = QPushButton("Open Line Items")
        self.open_line_items_button.clicked.connect(self._open_line_items_for_selected_project)
        self.open_line_items_button.setEnabled(False) # Disabled until project selected
        action_buttons_layout.addWidget(self.open_line_items_button)
        
        # Add Delete Button as it's common on dashboards
        self.delete_project_button = QPushButton("Delete Project")
        self.delete_project_button.clicked.connect(self._delete_selected_project)
        self.delete_project_button.setEnabled(False) # Disabled until project selected
        action_buttons_layout.addWidget(self.delete_project_button)


        main_layout.addLayout(action_buttons_layout)
        main_layout.addStretch(1) # Pushes content up

        # Connect selection signal to enable/disable buttons
        self.projects_table.itemSelectionChanged.connect(self._toggle_action_buttons)

    def _toggle_action_buttons(self):
        selected_items = self.projects_table.selectedItems()
        enable_buttons = bool(selected_items)
        self.open_general_info_button.setEnabled(enable_buttons)
        self.open_line_items_button.setEnabled(enable_buttons)
        self.delete_project_button.setEnabled(enable_buttons)

    def _add_new_project_from_form(self):
        """Adds a new project using the form fields on the dashboard."""
        project_name = self.new_project_name_input.text().strip()
        client_name = self.new_client_name_input.text().strip()
        client_phone = self.new_client_phone_input.text().strip()
        project_address_street = self.new_project_address_input.text().strip() # Using simplified address

        if not project_name or not client_name:
            QMessageBox.warning(self, "Input Error", "Project Name and Client Name are required to add a new project.")
            return

        try:
            new_project = Project(
                project_name=project_name,
                client_name=client_name,
                client_phone=client_phone if client_phone else None,
                project_address_street=project_address_street if project_address_street else None,
                estimate_date=date.today(), # Default for new projects
                bid_due_date=date.today(), # Default for new projects
                project_status="New", # Default status
                markup_percentage=0.0, # Default percentages
                overhead_percentage=0.0,
                profit_percentage=0.0
            )
            self.db_session.add(new_project)
            self.db_session.commit()
            QMessageBox.information(self, "Success", "New project added successfully!")
            
            # Clear the new project form fields
            self.new_project_name_input.clear()
            self.new_client_name_input.clear()
            self.new_client_phone_input.clear()
            self.new_project_address_input.clear()

            self.load_projects() # Refresh the dashboard table
            # Optionally, auto-select the new project or open its general info window
            # self._open_general_info_window(new_project.project_id)

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to add new project: {e}")

    def _get_selected_project_id(self):
        """Helper to get the project_id from the selected row in the table."""
        selected_items = self.projects_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a project first.")
            return None
        return int(self.projects_table.item(selected_items[0].row(), 0).text())

    def _open_general_info_for_selected_project(self):
        """Opens or brings to front the GeneralInfoWindow for the selected project."""
        project_id = self._get_selected_project_id()
        if project_id is None:
            return

        if project_id in self.open_general_info_windows and self.open_general_info_windows[project_id].isVisible():
            self.open_general_info_windows[project_id].raise_()
            self.open_general_info_windows[project_id].activateWindow()
        else:
            general_info_window = GeneralInfoWindow(project_id=project_id, parent=self)
            general_info_window.project_updated_signal.connect(self.load_projects) # Refresh dashboard after save
            general_info_window.show()
            self.open_general_info_windows[project_id] = general_info_window

    def _open_line_items_for_selected_project(self):
        """Opens or brings to front the EstimateLineItemsView for the selected project."""
        project_id = self._get_selected_project_id()
        if project_id is None:
            return

        if project_id in self.open_estimate_line_items_windows and self.open_estimate_line_items_windows[project_id].isVisible():
            self.open_estimate_line_items_windows[project_id].raise_()
            self.open_estimate_line_items_windows[project_id].activateWindow()
        else:
            line_items_window = EstimateLineItemsWindow(project_id=project_id, parent=self)
            line_items_window.project_updated_signal.connect(self.load_projects) # Refresh dashboard after save/update
            line_items_window.show()
            self.open_estimate_line_items_windows[project_id] = line_items_window

    def _delete_selected_project(self):
        """Deletes the selected project and its associated data."""
        project_id = self._get_selected_project_id()
        if project_id is None:
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete project ID: {project_id}? This will also delete all associated line items.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                project = self.db_session.query(Project).filter_by(project_id=project_id).first()
                if project:
                    self.db_session.delete(project)
                    self.db_session.commit()
                    QMessageBox.information(self, "Success", "Project deleted successfully!")
                    self.load_projects() # Refresh the dashboard table

                    # Close any open windows for this project
                    if project_id in self.open_general_info_windows:
                        self.open_general_info_windows[project_id].close()
                        del self.open_general_info_windows[project_id]
                    if project_id in self.open_estimate_line_items_windows:
                        self.open_estimate_line_items_windows[project_id].close()
                        del self.open_estimate_line_items_windows[project_id]
                else:
                    QMessageBox.warning(self, "Error", "Selected project not found in database.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete project: {e}")

    def load_projects(self):
        """Loads project data into the main dashboard table."""
        self.projects_table.setRowCount(0)
        try:
            projects = self.db_session.query(Project).all()
            self.projects_table.setRowCount(len(projects))
            for row_idx, project in enumerate(projects):
                self.projects_table.setItem(row_idx, 0, QTableWidgetItem(str(project.project_id)))
                self.projects_table.setItem(row_idx, 1, QTableWidgetItem(project.project_name))
                self.projects_table.setItem(row_idx, 2, QTableWidgetItem(project.client_name))
                # For Est. Date, format it as YYYY-MM-DD
                est_date_str = project.estimate_date.strftime('%Y-%m-%d') if project.estimate_date else "N/A"
                self.projects_table.setItem(row_idx, 3, QTableWidgetItem(est_date_str))
            self.projects_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load projects: {e}")

    def closeEvent(self, event):
        """Handles the main window close event."""
        # Close all managed child windows before closing the main app
        for window_dict in [self.open_general_info_windows, self.open_estimate_line_items_windows]:
            for window in list(window_dict.values()): # Use list() to iterate over a copy
                if window.isVisible():
                    window.close()
        self.db_session.close()
        super().closeEvent(event)

if __name__ == "__main__":
    create_db_and_tables() # Ensure DB is set up
    app = QApplication(sys.argv)
    main_app = ContractorProApp()
    main_app.show()
    sys.exit(app.exec())