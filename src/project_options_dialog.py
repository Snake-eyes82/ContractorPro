# src/project_options_dialog.py
import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from datetime import date # Only needed for the __main__ block for standalone testing

# Import your existing view windows. This new dialog will launch them.
from general_info_view import GeneralInfoWindow
from estimate_line_items_view import EstimateLineItemsView
from src.database import Session, Project # Needed to fetch project details for display

class ProjectOptionsDialog(QDialog):
    # Signals to communicate back to the main application
    open_general_info_requested = Signal(int) # Emits the project_id when General Info button is clicked
    open_line_items_requested = Signal(int)   # Emits the project_id when Estimate Line Items button is clicked
    project_deleted_signal = Signal(int)      # Propagates the project_id if it's deleted from GeneralInfoView

    def __init__(self, project_id: int, parent=None):
        """
        Initializes the ProjectOptionsDialog.

        Args:
            project_id (int): The ID of the project for which options are to be displayed.
            parent (QWidget): The parent widget, typically the main application window (ContractorProApp).
        """
        super().__init__(parent)
        self.project_id = project_id
        self.parent_app = parent # Store a reference to the main app (ContractorProApp instance)
        self.db_session = Session() # Create a new database session for this dialog's operations

        self.setWindowTitle(f"Project Options - ID: {self.project_id}")
        self.setGeometry(200, 200, 400, 200) # Sets initial position (200,200) and size (400x200)
        self.setMinimumSize(300, 150) # Sets the minimum allowable size for the dialog

        self.init_ui() # Call method to set up the visual interface
        self.load_project_name() # Load and display the project's name

    def init_ui(self):
        """Sets up the graphical user interface elements within the dialog."""
        main_layout = QVBoxLayout() # Vertical layout for the entire dialog
        self.setLayout(main_layout)

        # Label to display the project's name and ID
        self.project_label = QLabel(f"<h2>Project ID: {self.project_id}</h2>")
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center the text
        main_layout.addWidget(self.project_label) # Add label to the main layout

        # Horizontal layout for the primary action buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout) # Add this horizontal layout to the main vertical layout

        # Button to open the General Info window
        self.general_info_button = QPushButton("General Info")
        # Connect the button click to a method that emits a signal
        self.general_info_button.clicked.connect(self.request_open_general_info_window)
        button_layout.addWidget(self.general_info_button) # Add button to horizontal layout

        # Button to open the Estimate Line Items window
        self.line_items_button = QPushButton("Estimate Line Items")
        # Connect the button click to a method that emits a signal
        self.line_items_button.clicked.connect(self.request_open_estimate_line_items)
        button_layout.addWidget(self.line_items_button) # Add button to horizontal layout

        # Placeholder for future buttons (e.g., Expenses, Invoices, etc.)
        # These are currently disabled and illustrative.
        # self.expenses_button = QPushButton("Expenses")
        # self.expenses_button.setEnabled(False) # Set to False to disable
        # button_layout.addWidget(self.expenses_button)

        # self.invoices_button = QPushButton("Invoices")
        # self.invoices_button.setEnabled(False) # Set to False to disable
        # button_layout.addWidget(self.invoices_button)

        # Button for generating PDF reports (as discussed for future implementation)
        self.pdf_report_button = QPushButton("Generate PDF Report (Coming Soon)")
        self.pdf_report_button.setEnabled(False) # Keep disabled for now
        main_layout.addWidget(self.pdf_report_button) # Add button to the main vertical layout

    def load_project_name(self):
        """Fetches the project's name from the database using its ID and updates the dialog's label and title."""
        try:
            # Query the database for the Project object matching the given project_id
            project = self.db_session.query(Project).filter_by(project_id=self.project_id).first()
            if project:
                # If project found, update label with project name and ID, and update dialog window title
                self.project_label.setText(f"<h2>Project: {project.project_name}<br>(ID: {self.project_id})</h2>")
                self.setWindowTitle(f"Project Options - {project.project_name}")
            else:
                # If project not found, indicate that
                self.project_label.setText(f"<h2>Project ID: {self.project_id} (Not Found)</h2>")
        except Exception as e:
            # Display a critical error message if database operation fails
            QMessageBox.critical(self, "Database Error", f"Failed to load project name: {e}")

    def request_open_general_info_window(self):
        """Emits the signal `open_general_info_requested` with the current project's ID."""
        # This signal will be connected to a method in the main app (ContractorProApp)
        # which will then handle opening or showing the GeneralInfoView.
        self.open_general_info_requested.emit(self.project_id)
        # Optional: Uncomment the line below if you want this dialog to close immediately
        # after the General Info button is clicked.
        # self.accept() # Close the dialog

    def request_open_estimate_line_items(self):
        """Emits the signal `open_line_items_requested` with the current project's ID."""
        # Similar to the above, this signal informs the main app to open/show the EstimateLineItemsView.
        self.open_line_items_requested.emit(self.project_id)
        # Optional: Uncomment the line below if you want this dialog to close immediately
        # after the Estimate Line Items button is clicked.
        # self.accept() # Close the dialog

    def closeEvent(self, event):
        """
        Overrides the close event to ensure the database session is properly closed
        when the ProjectOptionsDialog window is closed.
        """
        self.db_session.close() # Close the database session
        super().closeEvent(event) # Call the base class's closeEvent to ensure proper Qt cleanup

