ContractorPro Estimator
Overview
ContractorPro Estimator is a desktop application designed to streamline the process of creating professional and accurate project estimates for contractors. Built with Python and the PySide6 framework for a user-friendly graphical interface, this tool helps manage project details, calculate costs, generate detailed line-item estimates, and export them as PDF documents.

This version of ContractorPro Estimator includes functionality for:

Managing general project information (client details, project name, etc.).
Defining and calculating costs for various line items (labor, materials, subcontractors, etc.).
Adjusting pricing with markup and overhead calculations.
Generating professional-looking PDF estimates.
Storing and retrieving project data using a local SQLite database.
Packaging as a standalone executable for easy distribution (via PyInstaller).
Installation
Prerequisites
Python 3.x must be installed on the user's system.
While the included executable in the dist folder allows for immediate use on Windows, running from the source code requires the dependencies listed below.
Running from the Executable (Windows)
Navigate to the dist folder in the repository.
Double-click the ContractorProEstimator.exe file to run the application.
Running from Source Code
Clone the repository to your local machine: ```bash git clone https://github.com/Snake-eyes82/ContractorPro.git cd ContractorPro ```
Create a virtual environment (recommended): ```bash python -m venv venv ```
Activate the virtual environment:
Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate
Install the required dependencies: ```bash pip install -r requirements.txt ```
Run the application: ```bash python src/main_app.py ```
Usage
Launch the ContractorPro Estimator application.
Use the provided interface to enter project details, add line items with descriptions, quantities, and costs.
Apply markup and overhead as needed.
Preview the estimate.
Export the estimate as a PDF file.
Project data is automatically saved in a local contractor_pro.db database.
Project Structure
```
ContractorPro/
├── assets/             # Contains images, icons, or other static assets
├── data/               # May contain default data or templates
├── dist/               # Contains the bundled executable (Windows)
├── docs/               # For documentation (if any)
├── src/                # Contains the Python source code
│   ├── pycache/    # Python compiled bytecode (ignored by Git)
│   ├── database.py     # Handles database interactions
│   ├── estimate_line_items_view.py # UI for managing estimate items
│   ├── general_info_view.py      # UI for general project details
│   ├── main_app.py           # Main application entry point
│   ├── pdf_generator.py      # Logic for generating PDF estimates
│   ├── project_details_window.py # UI for detailed project settings
│   └── project_options_dialog.py # UI for project options
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── ContractorProEstimator.spec # PyInstaller specification file
├── contractor_pro.db     # Local SQLite database (ignored by Git)
├── Estimate_test_1.pdf   # Example PDF estimate (may be present)
├── requirements.txt      # Lists the project's dependencies
└── Step-by-Step for Windows Warnings.txt # (Likely a temporary file, consider removing or including in docs)
```

Technologies Used
Python: The primary programming language.
PySide6: A Python binding for the Qt 6 cross-platform application development framework, used for the graphical user interface.
SQLite: A lightweight, disk-based database that doesn't require a separate server, used for local data storage.
ReportLab: A library for generating PDFs, used for creating the estimate documents.
PyInstaller: Used to bundle the Python application and its dependencies into a standalone executable.
Contributing


Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to:

Fork the repository.
Create a new branch for your feature or fix.
Make your changes and commit them.
Push your changes to your fork.
Submit a pull request.