# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import date # Import date for default values
import sys, os
# Define the database file path
DATABASE_URL = "sqlite:///./contractor_pro.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Declare a base for declarative models
Base = declarative_base()

# Function to get the database path
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
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def create_db_and_tables():
    # Only create tables if the database file doesn't exist yet
    db_file_path = get_database_path()
    if not os.path.exists(db_file_path):
        print(f"Database file not found at {db_file_path}. Creating new database and tables.")
        Base.metadata.create_all(engine)
    else:
        print(f"Database file found at {db_file_path}. Tables should already exist.")

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

    # Relationship to Project
    project = relationship("Project", back_populates="line_items")

    def __repr__(self):
        return f"<EstimateLineItem(id={self.line_item_id}, project_id={self.project_id}, description='{self.description}')>"

# Create a sessionmaker to interact with the database
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create tables
def create_db_and_tables():
    db_file_path = get_database_path()
    if not os.path.exists(db_file_path):
        print(f"Database file not found at {db_file_path}. Creating new database and tables.")
        Base.metadata.create_all(engine)
    else:
        print(f"Database file found at {db_file_path}. Tables should already exist.")