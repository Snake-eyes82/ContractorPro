# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import date
import sys, os

# Function to get the database path dynamically
def get_database_path():
    if getattr(sys, 'frozen', False):
        # We are running in a PyInstaller bundle
        # sys.executable is the path to the .exe
        # os.path.dirname(sys.executable) is the directory containing the .exe
        return os.path.join(os.path.dirname(sys.executable), 'contractor_pro.db')
    else:
        # We are running as a normal Python script
        # This assumes contractor_pro.db is in the project root, one level up from src
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'contractor_pro.db')

DATABASE_URL = f"sqlite:///{get_database_path()}"
engine = create_engine(DATABASE_URL) # Removed connect_args={"check_same_thread": False} as it's often not needed for simple SQLite apps
print(F"DEBUG: Database file path: {get_database_path()}")
# Declare a base for declarative models
Base = declarative_base()

# Define the Project model
class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    client_name = Column(String, index=True)
    client_contact_person = Column(String, nullable=True)
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
    project_start_date = Column(Date)
    expected_completion_date = Column(Date)
    project_status = Column(String, default="Draft") # e.g., Draft, Sent, Accepted, Rejected
    contract_type = Column(String, nullable=True)
    scope_of_work = Column(Text, nullable=True)
    project_notes = Column(Text, nullable=True)
    markup_percentage = Column(Float, default=0.0)
    overhead_percentage = Column(Float, default=0.0)
    profit_percentage = Column(Float, default=0.0)
    total_direct_cost = Column(Float, default=0.0) # These will be calculated and saved
    total_overhead = Column(Float, default=0.0)   # by EstimateLineItemsWindow
    total_profit = Column(Float, default=0.0)     # and GeneralInfoWindow
    final_project_estimate = Column(Float, default=0.0)

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
    unit_of_measure_uom = Column(String) # Renamed to match your provided DB schema
    quantity = Column(Float)
    unit_cost = Column(Float)
    total_cost = Column(Float) # Calculated field (quantity * unit_cost)
    common_item_name = Column(String) # Store the name of the common item used, if any
    cost_code = Column(String) # Store the code of the cost code used, if any (e.g., "03 30 00")

    # Relationship to Project
    project = relationship("Project", back_populates="line_items")

    def __repr__(self):
        return f"<EstimateLineItem(id={self.line_item_id}, project_id={self.project_id}, description='{self.description}')>"

# Define CommonItem model (RE-INTRODUCED)
class CommonItem(Base):
    __tablename__ = 'common_items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    unit = Column(String) # UOM
    type = Column(String) # e.g., Material, Labor, Service
    mf_code = Column(String) # MasterFormat Code (optional)

    def __repr__(self):
        return f"<CommonItem(id={self.id}, name='{self.name}')>"

# Define CostCode model (RE-INTRODUCED)
class CostCode(Base):
    __tablename__ = 'cost_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True) # e.g., 03 30 00
    name = Column(String, nullable=False) # e.g., Cast-in-Place Concrete
    description = Column(String)
    mf_division = Column(String) # MasterFormat Division (optional)

    def __repr__(self):
        return f"<CostCode(id={self.id}, code='{self.code}', name='{self.name}')>"

# Create a sessionmaker to interact with the database
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create tables
def create_db_and_tables():
    db_file_path = get_database_path()
    if not os.path.exists(db_file_path):
        print(f"Database file not found at {db_file_path}. Creating new database and tables.")
    else:
        print(f"Database file found at {db_file_path}. Ensuring tables exist.")
    # This will create tables if they don't exist.
    # It does NOT handle schema migrations (e.g., adding columns to existing tables).
    # For schema changes, you'd typically use a migration tool like Alembic.
    Base.metadata.create_all(engine)

# Call create_db_and_tables when this module is imported to ensure tables are ready
create_db_and_tables()

if __name__ == '__main__':
    print("\nAttempting to add initial data if tables are empty...")
    # The create_db_and_tables() function is already called at module level,
    # but it's good practice to ensure it if this file is run directly.
    # create_db_and_tables() # Already called above, no need to call again here if it's top-level

    session = Session()
    try:
        # Add Common Items if table is empty
        if session.query(CommonItem).count() == 0:
            print("Adding initial common items...")
            session.add_all([
                CommonItem(name="2x4 Lumber (8')", description="Standard framing lumber", unit="EA", type="Material", mf_code="06 10 00"),
                CommonItem(name="Electrician Hour", description="Skilled labor for electrical work", unit="HR", type="Labor", mf_code="26 00 00"),
                CommonItem(name="Drywall Sheet (4x8)", description="Gypsum board for walls/ceilings", unit="EA", type="Material", mf_code="09 20 00"),
                CommonItem(name="Interior Paint (Gallon)", description="Standard interior latex paint", unit="GAL", type="Material", mf_code="09 90 00"),
                CommonItem(name="Plumbing Fixture Install", description="Labor for installing plumbing fixtures", unit="EA", type="Service", mf_code="22 00 00"),
            ])
            session.commit()
            print("Initial common items added.")
        else:
            print(f"CommonItem table already contains {session.query(CommonItem).count()} items")

        # Add Cost Codes if table is empty
        if session.query(CostCode).count() == 0:
            print("Adding initial cost codes...")
            session.add_all([
                CostCode(code="03 00 00", name="Concrete", description="All concrete related work", mf_division="03"),
                CostCode(code="06 10 00", name="Rough Carpentry", description="Framing, sheathing, and blocking", mf_division="06"),
                CostCode(code="09 20 00", name="Gypsum Board", description="Drywall installation and finishing", mf_division="09"),
                CostCode(code="09 90 00", name="Painting", description="Interior and exterior painting", mf_division="09"),
                CostCode(code="22 00 00", name="Plumbing", description="All plumbing systems and fixtures", mf_division="22"),
                CostCode(code="26 00 00", name="Electrical", description="All electrical systems and wiring", mf_division="26"),
            ])
            session.commit()
            print("Initial cost codes added.")
    except Exception as e:
        session.rollback()
        print(f"Error adding initial data: {e}")
    finally:
        session.close()