# src/main_app.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QSize
# Import the updated database functions and models
from src.database import Session, Project, create_db_and_tables
from src.general_info_view import GeneralInfoWindow
from src.estimate_line_items_view import EstimateLineItemsWindow # NEW import
from src.manage_common_data_view import ManageCommonDataWindow # Ensure this is imported for direct access

class ContractorProEstimator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_session = Session()
        self.setWindowTitle("ContractorPro Estimator Dashboard")
        self.setGeometry(100, 100, 1200, 700) # Increased width to accommodate new columns
        self.setMinimumSize(QSize(1100, 600))
        self.current_project_id = None # To keep track of selected project

        self.init_ui()
        self.load_projects()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        main_layout.addWidget(QLabel("<h1>ContractorPro Estimator</h1>", alignment=Qt.AlignCenter))

        # Search Bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Projects:")
        search_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Project Name or Client Name...")
        self.search_input.textChanged.connect(self.load_projects) # Filter on text change
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Projects Table
        self.projects_table = QTableWidget()
        # Increased column count to 9: ID, Project Name, Client Name, Status, Bid Due Date, Project Start Date, Expected Completion Date, Total Direct Cost, Final Estimate
        self.projects_table.setColumnCount(9)
        self.projects_table.setHorizontalHeaderLabels([
            "ID", "Project Name", "Client Name", "Status", "Bid Due Date",
            "Project Start Date", "Expected Completion Date", "Total Direct Cost", "Final Estimate"
        ])
        self.projects_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.projects_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.projects_table.setSelectionMode(QTableWidget.SingleSelection)
        self.projects_table.itemSelectionChanged.connect(self.on_project_selection_changed)
        main_layout.addWidget(self.projects_table)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_new_project_button = QPushButton("Add New Project")
        self.add_new_project_button.clicked.connect(self.add_new_project)
        buttons_layout.addWidget(self.add_new_project_button)

        self.open_general_info_button = QPushButton("Open General Info")
        self.open_general_info_button.clicked.connect(self.open_general_info)
        self.open_general_info_button.setEnabled(False) # Disabled until project is selected
        buttons_layout.addWidget(self.open_general_info_button)

        self.open_line_items_button = QPushButton("Open Line Items")
        self.open_line_items_button.clicked.connect(self.open_line_items)
        self.open_line_items_button.setEnabled(False) # Disabled until project is selected
        buttons_layout.addWidget(self.open_line_items_button)

        self.manage_common_data_button = QPushButton("Manage Common Items / Cost Codes")
        self.manage_common_data_button.clicked.connect(self.open_manage_common_data)
        buttons_layout.addWidget(self.manage_common_data_button)


        self.delete_selected_project_button = QPushButton("Delete Selected Project")
        self.delete_selected_project_button.clicked.connect(self.delete_selected_project)
        self.delete_selected_project_button.setEnabled(False) # Disabled until project is selected
        buttons_layout.addWidget(self.delete_selected_project_button)

        main_layout.addLayout(buttons_layout)

    def load_projects(self):
        self.projects_table.setRowCount(0)
        search_text = self.search_input.text().strip()
        try:
            projects = self.db_session.query(Project).all()
            if search_text:
                projects = [p for p in projects if search_text.lower() in p.project_name.lower() or search_text.lower() in p.client_name.lower()]

            self.projects_table.setRowCount(len(projects))
            for row_idx, project in enumerate(projects):
                # These totals are now columns in the Project object
                total_direct_cost = project.total_direct_cost
                final_estimate = project.final_project_estimate

                self.projects_table.setItem(row_idx, 0, QTableWidgetItem(str(project.project_id)))
                self.projects_table.setItem(row_idx, 1, QTableWidgetItem(project.project_name))
                self.projects_table.setItem(row_idx, 2, QTableWidgetItem(project.client_name))
                self.projects_table.setItem(row_idx, 3, QTableWidgetItem(project.project_status or ""))
                self.projects_table.setItem(row_idx, 4, QTableWidgetItem(project.bid_due_date.strftime("%Y-%m-%d") if project.bid_due_date else ""))
                self.projects_table.setItem(row_idx, 5, QTableWidgetItem(project.project_start_date.strftime("%Y-%m-%d") if project.project_start_date else ""))
                self.projects_table.setItem(row_idx, 6, QTableWidgetItem(project.expected_completion_date.strftime("%Y-%m-%d") if project.expected_completion_date else ""))
                self.projects_table.setItem(row_idx, 7, QTableWidgetItem(f"${total_direct_cost:.2f}"))
                self.projects_table.setItem(row_idx, 8, QTableWidgetItem(f"${final_estimate:.2f}"))

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load projects: {e}")


    def on_project_selection_changed(self):
        selected_rows = self.projects_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.current_project_id = int(self.projects_table.item(row, 0).text())
            self.open_general_info_button.setEnabled(True)
            self.open_line_items_button.setEnabled(True)
            self.delete_selected_project_button.setEnabled(True)
        else:
            self.current_project_id = None
            self.open_general_info_button.setEnabled(False)
            self.open_line_items_button.setEnabled(False)
            self.delete_selected_project_button.setEnabled(False)

    def add_new_project(self):
        self.general_info_window = GeneralInfoWindow(project_id=None, db_session=self.db_session, parent_dashboard=self)
        self.general_info_window.project_updated_signal.connect(self.load_projects) # Refresh on new project
        self.general_info_window.show()

    def open_general_info(self):
        if self.current_project_id is not None:
            self.general_info_window = GeneralInfoWindow(project_id=self.current_project_id, db_session=self.db_session, parent_dashboard=self)
            self.general_info_window.project_updated_signal.connect(self.load_projects) # Refresh on update
            self.general_info_window.show()
        else:
            QMessageBox.warning(self, "No Project Selected", "Please select a project from the table first.")

    def open_line_items(self):
        selected_row = self.projects_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a project to view line items.")
            return

        project_id = int(self.projects_table.item(selected_row, 0).text())

        # This is the line that caused the error, but should be fine
        # once EstimateLineItemsWindow's __init__ is updated.
        self.line_items_window = EstimateLineItemsWindow(project_id=project_id, db_session=self.db_session, parent=self)
        self.line_items_window.show()

    def open_manage_common_data(self):
        self.manage_common_data_window = ManageCommonDataWindow(db_session=self.db_session, parent=self)
        self.manage_common_data_window.data_updated_signal.connect(self.load_projects) # Refresh dashboard if project names change in future
        self.manage_common_data_window.show()


    def delete_selected_project(self):
        if self.current_project_id is not None:
            reply = QMessageBox.question(self, 'Confirm Delete',
                                         f"Are you sure you want to delete Project ID {self.current_project_id} and all its line items?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    project_to_delete = self.db_session.query(Project).filter_by(project_id=self.current_project_id).first()
                    if project_to_delete:
                        self.db_session.delete(project_to_delete)
                        self.db_session.commit()
                        QMessageBox.information(self, "Success", f"Project ID {self.current_project_id} deleted successfully.")
                        self.load_projects() # Refresh the table
                        self.on_project_selection_changed() # Reset button states
                    else:
                        QMessageBox.warning(self, "Error", "Selected project not found in database.")
                except Exception as e:
                    self.db_session.rollback()
                    QMessageBox.critical(self, "Database Error", f"Failed to delete project: {e}")
        else:
            QMessageBox.warning(self, "No Project Selected", "Please select a project to delete.")

    def closeEvent(self, event):
        if self.db_session:
            self.db_session.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Ensure database tables are created when the app starts
    create_db_and_tables() # Call the function
    window = ContractorProEstimator()
    window.show()
    sys.exit(app.exec())