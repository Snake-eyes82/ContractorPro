# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import date
import sys, os
from sqlalchemy import inspect # Import inspect to check for columns

# Define the database file path
def get_database_path():
    if getattr(sys, 'frozen', False):
        # We are running in a PyInstaller bundle
        return os.path.join(os.path.dirname(sys.executable), 'contractor_pro.db')
    else:
        # We are running as a normal Python script
        # This assumes contractor_pro.db is in the project root, one level up from src
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'contractor_pro.db')

DATABASE_URL = f"sqlite:///{get_database_path()}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Renamed to SessionLocal for clarity

Base = declarative_base()

# Predefined 2024 MasterFormat Divisions (for project categorization)
MASTER_FORMAT_DIVISIONS_2024 = [
    "00 - Procurement and Contracting Requirements",
    "01 - General Requirements",
    "02 - Existing Conditions",
    "03 - Concrete",
    "04 - Masonry",
    "05 - Metals",
    "06 - Wood, Plastics, and Composites",
    "07 - Thermal and Moisture Protection",
    "08 - Openings",
    "09 - Finishes",
    "10 - Specialties",
    "11 - Equipment",
    "12 - Furnishings",
    "13 - Special Construction",
    "14 - Conveying Equipment",
    "21 - Fire Suppression",
    "22 - Plumbing",
    "23 - Heating, Ventilating, and Air Conditioning (HVAC)",
    "25 - Integrated Automation",
    "26 - Electrical",
    "27 - Communications",
    "28 - Electronic Safety and Security",
    "31 - Earthwork",
    "32 - Exterior Improvements",
    "33 - Utilities",
    "34 - Transportation",
    "35 - Waterway and Marine Construction",
    "40 - Process Integration",
    "41 - Material Processing and Handling Equipment",
    "42 - Process Heating, Cooling, and Drying Equipment",
    "43 - Process Gas and Liquid Handling, Purification, and Storage Equipment",
    "44 - Pollution Control Equipment",
    "45 - Industry-Specific Manufacturing Equipment",
    "46 - Water and Wastewater Equipment",
    "48 - Electrical Power Generation",
]

# Baseline Common Items (examples, user will provide prices)
# Format: (name, description, unit, type, master_format_code_link)
BASELINE_COMMON_ITEMS = [
    # Materials
    ("2x4x8' Stud", "Standard dimensional lumber for framing", "EA", "Material", "06 10 00 - Rough Carpentry"),
    ("4x8x1/2\" Drywall", "Gypsum board for walls/ceilings", "EA", "Material", "09 29 00 - Gypsum Board Assemblies"),
    ("Romex 14/2 Wire", "Non-metallic sheathed cable for electrical circuits", "LF", "Material", "26 05 00 - Common Work Results for Electrical"),
    ("Standard Outlet", "15A 120V Duplex Receptacle", "EA", "Material", "26 27 26 - Wiring Devices"),
    ("PVC 1.5\" Pipe", "Schedule 40 PVC pipe for drainage", "LF", "Material", "22 10 00 - Plumbing Piping"),
    ("Galvanized Nail (1.5\")", "Common nail for various fastening", "LB", "Material", None), # No specific MF code for common nails
    # Labor
    ("Rough Carpenter", "Skilled labor for framing and rough carpentry", "HR", "Labor", "06 10 00 - Rough Carpentry"),
    ("Electrician", "Journeyman electrician labor", "HR", "Labor", "26 00 00 - Electrical"),
    ("Plumber", "Journeyman plumber labor", "HR", "Labor", "22 00 00 - Plumbing"),
    ("Drywall Installer", "Skilled labor for drywall hanging and finishing", "HR", "Labor", "09 29 00 - Gypsum Board Assemblies"),
    # Services
    ("Demolition (Interior)", "Removal of interior walls, fixtures, etc.", "LS", "Service", "02 41 16 - Structure Demolition"),
    ("Waste Disposal (10yd)", "Roll-off dumpster and disposal fees (10 cubic yard)", "LS", "Service", "01 50 00 - Temporary Facilities and Controls"),
]

# Baseline Cost Codes (examples, based on common construction categories)
# Format: (code, name, description, master_format_division)
BASELINE_COST_CODES = [
    ("01 50 00", "Temporary Facilities and Controls", "Includes temporary utilities, site offices, sanitation.", "01 - General Requirements"),
    ("02 20 00", "Site Preparation", "Clearing, grubbing, earthwork.", "02 - Existing Conditions"),
    ("03 30 00", "Cast-in-Place Concrete", "Forming, rebar, pouring, finishing concrete slabs and foundations.", "03 - Concrete"),
    ("04 20 00", "Unit Masonry", "Brick, block, stone work.", "04 - Masonry"),
    ("05 10 00", "Structural Metal Framing", "Steel beams, columns, decking.", "05 - Metals"),
    ("06 10 00", "Rough Carpentry", "Framing, sheathing, blocking.", "06 - Wood, Plastics, and Composites"),
    ("07 21 00", "Building Insulation", "Thermal insulation for walls, roofs.", "07 - Thermal and Moisture Protection"),
    ("08 11 00", "Standard Steel Doors and Frames", "Installation of standard metal doors.", "08 - Openings"),
    ("09 29 00", "Gypsum Board Assemblies", "Drywall hanging, taping, mudding, sanding.", "09 - Finishes"),
    ("09 65 00", "Resilient Flooring", "Installation of vinyl, linoleum, or rubber flooring.", "09 - Finishes"),
    ("22 10 00", "Plumbing Piping", "Rough-in and finish plumbing pipes and fittings.", "22 - Plumbing"),
    ("23 05 00", "Common Work Results for HVAC", "General HVAC installation and connection.", "23 - Heating, Ventilating, and Air Conditioning (HVAC)"),
    ("26 05 00", "Common Work Results for Electrical", "General electrical rough-in and finish.", "26 - Electrical"),
]


# Define the Project model
class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    client_name = Column(String, index=True)
    client_contact = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    client_address_street = Column(String, nullable=True)
    client_address_city = Column(String, nullable=True)
    client_address_state = Column(String, nullable=True)
    client_address_zip = Column(String, nullable=True)
    project_address_street = Column(String, nullable=True)
    project_address_city = Column(String, nullable=True)
    project_address_state = Column(String, nullable=True)
    project_address_zip = Column(String, nullable=True)
    estimate_date = Column(Date, default=date.today)
    bid_due_date = Column(Date, nullable=True)
    project_status = Column(String, default="Draft") # e.g., Draft, Sent, Accepted, Rejected
    contract_type = Column(String, nullable=True)
    scope_of_work = Column(Text, nullable=True)
    project_notes = Column(Text, nullable=True)
    markup_percentage = Column(Float, default=0.0)
    overhead_percentage = Column(Float, default=0.0)
    profit_percentage = Column(Float, default=0.0)
    total_direct_cost = Column(Float, default=0.0)
    total_overhead = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    final_project_estimate = Column(Float, default=0.0)
    # NEW COLUMN for MasterFormat Division
    master_format_division = Column(String, nullable=True)

    # Relationship to EstimateLineItem
    line_items = relationship("EstimateLineItem", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.project_id}, name='{self.project_name}', client='{self.client_name}')>"

# Define the EstimateLineItem model
class EstimateLineItem(Base):
    __tablename__ = "estimate_line_items"

    line_item_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"))
    description = Column(String)
    category = Column(String) # e.g., Material, Labor, Subcontractor, Equipment
    unit_of_measure_uom = Column(String) # e.g., LF, SF, HR, EA
    quantity = Column(Float)
    unit_cost = Column(Float)
    total_cost = Column(Float) # Calculated field (quantity * unit_cost)
    # NEW COLUMNS for linking to common items and cost codes
    common_item_id = Column(Integer, ForeignKey("common_items.item_id"), nullable=True)
    cost_code_id = Column(Integer, ForeignKey("cost_codes.cost_code_id"), nullable=True)

    # Relationships to Project, CommonItem, and CostCode
    project = relationship("Project", back_populates="line_items")
    common_item = relationship("CommonItem", back_populates="line_items")
    cost_code = relationship("CostCode", back_populates="line_items")


    def __repr__(self):
        return f"<EstimateLineItem(id={self.line_item_id}, project_id={self.project_id}, description='{self.description}')>"

# NEW MODEL: CommonItem (for materials, labor, services)
class CommonItem(Base):
    __tablename__ = "common_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String, unique=True, nullable=False)
    item_description = Column(Text, nullable=True)
    item_unit = Column(String, nullable=False)
    item_type = Column(String, nullable=False) # e.g., 'Material', 'Labor', 'Service'
    master_format_code = Column(String, nullable=True) # Links to a specific MF code (e.g., "06 10 00")

    line_items = relationship("EstimateLineItem", back_populates="common_item")

    def __repr__(self):
        return f"<CommonItem(id={self.item_id}, name='{self.item_name}', type='{self.item_type}')>"

# NEW MODEL: CostCode (for reusable cost codes)
class CostCode(Base):
    __tablename__ = "cost_codes"

    cost_code_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False) # e.g., "03 30 00", "EL-01"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    master_format_division = Column(String, nullable=True) # e.g., "03 - Concrete"

    line_items = relationship("EstimateLineItem", back_populates="cost_code")

    def __repr__(self):
        return f"<CostCode(id={self.cost_code_id}, code='{self.code}', name='{self.name}')>"


# Function to create tables and handle basic migrations
def create_db_and_tables():
    db_file_path = get_database_path()
    if not os.path.exists(db_file_path):
        print(f"Database file not found at {db_file_path}. Creating new database and tables.")
        Base.metadata.create_all(engine)
    else:
        print(f"Database file found at {db_file_path}.")
        # Use a session to check if new columns exist and add them
        with SessionLocal() as session:
            inspector = inspect(engine)

            # --- Add master_format_division to projects if missing ---
            project_columns = [col['name'] for col in inspector.get_columns('projects')]
            if 'master_format_division' not in project_columns:
                print("Adding 'master_format_division' column to 'projects' table...")
                with engine.connect() as conn:
                    conn.execute(Text("ALTER TABLE projects ADD COLUMN master_format_division TEXT"))
                    conn.commit()
                print("'master_format_division' column added.")

            # --- Add common_item_id and cost_code_id to estimate_line_items if missing ---
            line_item_columns = [col['name'] for col in inspector.get_columns('estimate_line_items')]
            if 'common_item_id' not in line_item_columns:
                print("Adding 'common_item_id' column to 'estimate_line_items' table...")
                with engine.connect() as conn:
                    conn.execute(Text("ALTER TABLE estimate_line_items ADD COLUMN common_item_id INTEGER REFERENCES common_items (item_id) ON DELETE SET NULL"))
                    conn.commit()
                print("'common_item_id' column added.")
            if 'cost_code_id' not in line_item_columns:
                print("Adding 'cost_code_id' column to 'estimate_line_items' table...")
                with engine.connect() as conn:
                    conn.execute(Text("ALTER TABLE estimate_line_items ADD COLUMN cost_code_id INTEGER REFERENCES cost_codes (cost_code_id) ON DELETE SET NULL"))
                    conn.commit()
                print("'cost_code_id' column added.")

            # --- Create new tables if they don't exist ---
            if not inspector.has_table("common_items"):
                print("Creating 'common_items' table...")
                CommonItem.__table__.create(engine)
                print("'common_items' table created.")
            if not inspector.has_table("cost_codes"):
                print("Creating 'cost_codes' table...")
                CostCode.__table__.create(engine)
                print("'cost_codes' table created.")

            # --- Populate initial data for common_items and cost_codes ---
            populate_initial_data(session)

def populate_initial_data(session):
    # Populate common_items if table is empty
    if session.query(CommonItem).count() == 0:
        print("Populating initial common items...")
        for item_data in BASELINE_COMMON_ITEMS:
            item = CommonItem(
                item_name=item_data[0],
                item_description=item_data[1],
                item_unit=item_data[2],
                item_type=item_data[3],
                master_format_code=item_data[4]
            )
            session.add(item)
        session.commit()
        print(f"Added {len(BASELINE_COMMON_ITEMS)} baseline common items.")

    # Populate cost_codes if table is empty
    if session.query(CostCode).count() == 0:
        print("Populating initial cost codes...")
        for code_data in BASELINE_COST_CODES:
            code = CostCode(
                code=code_data[0],
                name=code_data[1],
                description=code_data[2],
                master_format_division=code_data[3]
            )
            session.add(code)
        session.commit()
        print(f"Added {len(BASELINE_COST_CODES)} baseline cost codes.")

# --- Helper functions to retrieve data for UI ---

def get_master_format_divisions():
    """Returns the predefined 2024 MasterFormat divisions."""
    return MASTER_FORMAT_DIVISIONS_2024

def get_all_common_items(session):
    """Retrieves all common items from the database."""
    return session.query(CommonItem).order_by(CommonItem.item_name).all()

def get_all_cost_codes(session):
    """Retrieves all cost codes from the database."""
    return session.query(CostCode).order_by(CostCode.code).all()

def get_db():
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For direct execution (e.g., to create/update DB manually)
if __name__ == "__main__":
    create_db_and_tables()