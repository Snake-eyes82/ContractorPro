# src/database.py

import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import sys


# Define the path to the database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', 'contractor_pro.db') # One level up from src

# Create the engine
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    project_name = Column(String, nullable=False, unique=True)
    client_name = Column(String)
    client_contact_person = Column(String)
    client_phone = Column(String)
    client_email = Column(String)

    # Client Address
    client_address_street = Column(String)
    client_address_city = Column(String)
    client_address_state = Column(String)
    client_address_zip = Column(String)

    # Project Address
    project_address = Column(String)
    project_city = Column(String)
    project_state = Column(String)
    project_zip = Column(String)

    # Date fields (stored as YYYY-MM-DD strings)
    estimate_date = Column(String)
    bid_due_date = Column(String)
    project_start_date = Column(String)
    completion_date = Column(String) # Corrected name from 'expected_completion_date'
    estimate_date = Column(String)

    # Status and Type
    project_status = Column(String)
    contract_type = Column(String)

    # Financial Percentages
    markup_percentage = Column(Float)
    overhead_percentage = Column(Float)
    profit_percentage = Column(Float)

    # Text Areas
    scope_of_work = Column(Text)
    notes = Column(Text) # Renamed from project_notes to notes for consistency

    # Other financial columns
    contract_date = Column(String)
    project_description = Column(Text)
    contract_amount = Column(Float)
    payment_terms = Column(Text)
    change_orders_total = Column(Float)
    current_contract_amount = Column(Float)
    tax_rate = Column(Float)
    permit_cost = Column(Float)
    bonding_cost = Column(Float)
    insurance_cost = Column(Float)
    misc_expenses = Column(Float)
    estimated_total_cost = Column(Float)
    final_total_cost = Column(Float)
    total_direct_cost = Column(Float)
    final_project_estimate = Column(Float)

    # Relationships
    line_items = relationship('LineItem', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Project(id={self.id}, project_name='{self.project_name}')>"

class CommonItem(Base):
    __tablename__ = 'common_items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    unit = Column(String) # e.g., EA, LF, HR
    type = Column(String) # e.g., Material, Labor, Service
    mf_code = Column(String) # MasterFormat code for common items (optional)

    def __repr__(self):
        return f"<CommonItem(id={self.id}, name='{self.name}')>"

class MFGroup(Base):
    __tablename__ = 'mf_groups'
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    level = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey('mf_groups.id'))

    parent = relationship(
        'MFGroup',
        remote_side=[id],
        back_populates='children'
    )

    children = relationship(
        'MFGroup',
        back_populates='parent',
        cascade='all, delete-orphan'
    )

    cost_codes = relationship('CostCode', back_populates='mf_group', cascade='all, delete-orphan')
    def __repr__(self):
        return f"<MFGroup(id={self.id}, code='{self.code}', name='{self.name}', level={self.level})>"


class CostCode(Base):
    __tablename__ = 'cost_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True) # e.g., 03 30 00
    name = Column(String, nullable=False)
    description = Column(Text)
    mf_group_id = Column(Integer, ForeignKey('mf_groups.id'), nullable=True)
    mf_group = relationship('MFGroup', back_populates='cost_codes')

    def __repr__(self):
        return f"<CostCode(id={self.id}, code='{self.code}', name='{self.name}')>"

class LineItem(Base):
    __tablename__ = 'line_items'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String)
    unit_cost = Column(Float, nullable=False)
    markup_percentage = Column(Float, default=0.0)
    total_cost = Column(Float)
    notes = Column(Text)
    is_common_item = Column(Integer, default=0)
    common_item_id = Column(Integer, ForeignKey('common_items.id'), nullable=True)
    cost_code_id = Column(Integer, ForeignKey('cost_codes.id'), nullable=True)

    # Relationships
    project = relationship('Project', back_populates='line_items')
    common_item = relationship('CommonItem')
    cost_code = relationship('CostCode')

    def __repr__(self):
        return f"<LineItem(id={self.id}, project_id={self.project_id}, description='{self.description}')>"

Session = sessionmaker(bind=engine)

def create_db_and_tables():
    Base.metadata.create_all(engine)
    print(f"Database file found at {DATABASE_PATH}. Ensuring tables exist.")
    session = Session()
    try:
        # Check if MFGroup table is empty and populate if so
        if session.query(MFGroup).count() == 0:
            print("Populating initial MasterFormat Groups...")
            mf_groups_data = [
                {'code': '00', 'name': 'Procurement and Contracting Requirements', 'level': 0},
                {'code': '01', 'name': 'General Requirements', 'level': 0},
                {'code': '02', 'name': 'Existing Conditions', 'level': 0},
                {'code': '03', 'name': 'Concrete', 'level': 0},
                {'code': '04', 'name': 'Masonry', 'level': 0},
                {'code': '05', 'name': 'Metals', 'level': 0},
                {'code': '06', 'name': 'Wood, Plastics, and Composites', 'level': 0},
                {'code': '07', 'name': 'Thermal and Moisture Protection', 'level': 0},
                {'code': '08', 'name': 'Openings', 'level': 0},
                {'code': '09', 'name': 'Finishes', 'level': 0},
                {'code': '10', 'name': 'Specialties', 'level': 0},
                {'code': '11', 'name': 'Equipment', 'level': 0},
                {'code': '12', 'name': 'Furnishings', 'level': 0},
                {'code': '13', 'name': 'Special Construction', 'level': 0},
                {'code': '14', 'name': 'Conveying Equipment', 'level': 0},
                {'code': '21', 'name': 'Fire Suppression', 'level': 0},
                {'code': '22', 'name': 'Plumbing', 'level': 0},
                {'code': '23', 'name': 'Heating, Ventilating, and Air Conditioning (HVAC)', 'level': 0},
                {'code': '25', 'name': 'Integrated Automation', 'level': 0},
                {'code': '26', 'name': 'Electrical', 'level': 0},
                {'code': '27', 'name': 'Communications', 'level': 0},
                {'code': '28', 'name': 'Electronic Safety and Security', 'level': 0},
                {'code': '31', 'name': 'Earthwork', 'level': 0},
                {'code': '32', 'name': 'Exterior Improvements', 'level': 0},
                {'code': '33', 'name': 'Utilities', 'level': 0},
                {'code': '34', 'name': 'Transportation', 'level': 0},
                {'code': '35', 'name': 'Waterway and Marine Construction', 'level': 0},
                {'code': '40', 'name': 'Process Integration', 'level': 0},
                {'code': '41', 'name': 'Material Processing and Handling Equipment', 'level': 0},
                {'code': '42', 'name': 'Process Heating, Cooling, and Drying Equipment', 'level': 0},
                {'code': '43', 'name': 'Process Gas and Liquid Handling, Purification and Storage Equipment', 'level': 0},
                {'code': '44', 'name': 'Pollution Control Equipment', 'level': 0},
                {'code': '45', 'name': 'Industry-Specific Manufacturing Equipment', 'level': 0},
                {'code': '46', 'name': 'Water and Wastewater Equipment', 'level': 0},
                {'code': '48', 'name': 'Electrical Power Generation', 'level': 0},
            ]

            mf_group_objs = {}
            for data in mf_groups_data:
                group = MFGroup(**data)
                session.add(group)
                mf_group_objs[data['code']] = group
            session.commit()

            if session.query(MFGroup).filter(MFGroup.parent_id.isnot(None)).count() == 0:
                print("Populating initial MasterFormat Sub-Groups...")
                mf_sub_groups_data = [
                    {'code': '03 01 00', 'name': 'Maintenance of Concrete', 'level': 1, 'parent_code': '03'},
                    {'code': '03 05 00', 'name': 'Common Work Results for Concrete', 'level': 1, 'parent_code': '03'},
                    {'code': '03 10 00', 'name': 'Concrete Forming and Accessories', 'level': 1, 'parent_code': '03'},
                    {'code': '03 15 00', 'name': 'Concrete Accessories', 'level': 1, 'parent_code': '03'},
                    {'code': '03 20 00', 'name': 'Concrete Reinforcing', 'level': 1, 'parent_code': '03'},
                    {'code': '03 30 00', 'name': 'Cast-in-Place Concrete', 'level': 1, 'parent_code': '03'},
                    {'code': '06 10 00', 'name': 'Rough Carpentry', 'level': 1, 'parent_code': '06'},
                    {'code': '09 20 00', 'name': 'Gypsum Board', 'level': 1, 'parent_code': '09'},
                    {'code': '09 90 00', 'name': 'Painting and Coating', 'level': 1, 'parent_code': '09'},
                ]
                for data in mf_sub_groups_data:
                    parent = mf_group_objs.get(data['parent_code'])
                    if parent:
                        group = MFGroup(
                            code=data['code'],
                            name=data['name'],
                            level=data['level'],
                            parent=parent
                        )
                        session.add(group)
                        mf_group_objs[data['code']] = group
                session.commit()

        # Check if CommonItem table is empty and populate if so
        if session.query(CommonItem).count() == 0:
            print("Populating initial Common Items...")
            common_items_data = [
                {'name': '2x4 Lumber', 'description': 'Standard 2x4 framing lumber, 8ft length', 'unit': 'EA', 'type': 'Material', 'mf_code': '06 10 00'},
                {'name': 'Drywall Sheet', 'description': '1/2 inch gypsum board, 4x8 sheet', 'unit': 'EA', 'type': 'Material', 'mf_code': '09 20 00'},
                {'name': 'Concrete Mix', 'description': '50lb bag of ready-mix concrete', 'unit': 'BAG', 'type': 'Material', 'mf_code': '03 05 00'},
                {'name': 'Painter Hourly Rate', 'description': 'Hourly rate for skilled painter', 'unit': 'HR', 'type': 'Labor', 'mf_code': '09 90 00'},
                {'name': 'Electrician Hourly Rate', 'description': 'Hourly rate for licensed electrician', 'unit': 'HR', 'type': 'Labor', 'mf_code': '26 00 00'},
                {'name': 'Plumbing Fixture Installation', 'description': 'Installation service for standard plumbing fixtures', 'unit': 'LS', 'type': 'Service', 'mf_code': '22 00 00'},
                {'name': 'Structural Steel Beam', 'description': 'W10x33 structural steel beam, per linear foot', 'unit': 'LF', 'type': 'Material', 'mf_code': '05 12 00'},
            ]
            session.bulk_insert_mappings(CommonItem, common_items_data)
            session.commit()

        # Check if CostCode table is empty and populate if so
        if session.query(CostCode).count() == 0:
            print("Populating initial Cost Codes...")
            mf_concrete_group = session.query(MFGroup).filter_by(code='03 30 00').first()
            mf_rough_carpentry_group = session.query(MFGroup).filter_by(code='06 10 00').first()
            mf_gypsum_board_group = session.query(MFGroup).filter_by(code='09 20 00').first()
            mf_painting_group = session.query(MFGroup).filter_by(code='09 90 00').first()
            mf_plumbing_group = session.query(MFGroup).filter_by(code='22').first()
            mf_electrical_group = session.query(MFGroup).filter_by(code='26').first()

            cost_codes_data = [
                {'code': '03 30 00', 'name': 'Cast-in-Place Concrete', 'description': 'All concrete related work for slabs, foundations, walls.', 'mf_group': mf_concrete_group},
                {'code': '06 10 00', 'name': 'Rough Carpentry', 'description': 'Framing, sheathing, and blocking.', 'mf_group': mf_rough_carpentry_group},
                {'code': '09 20 00', 'name': 'Gypsum Board', 'description': 'Drywall installation and finishing.', 'mf_group': mf_gypsum_board_group},
                {'code': '09 90 00', 'name': 'Painting', 'description': 'Interior and exterior painting.', 'mf_group': mf_painting_group},
                {'code': '22 00 00', 'name': 'Plumbing Systems', 'description': 'All plumbing systems and fixtures.', 'mf_group': mf_plumbing_group},
                {'code': '26 00 00', 'name': 'Electrical Systems', 'description': 'All electrical systems, wiring, and fixtures.', 'mf_group': mf_electrical_group},
            ]
            valid_cost_codes = [
                CostCode(code=d['code'], name=d['name'], description=d['description'], mf_group=d['mf_group'])
                for d in cost_codes_data if d['mf_group'] is not None
            ]
            session.add_all(valid_cost_codes)
            session.commit()

        # Check if Project table is empty and populate if so
        if session.query(Project).count() == 0:
            print("Populating initial Project data...")
            initial_project = Project(
                project_name="Sample Project 1",
                client_name="Client A",
                client_contact_person="John Doe",
                client_phone="555-123-4567",
                client_email="john.doe@example.com",

                client_address_street="1234 High Ln",
                client_address_city="Client City",
                client_address_state="CA",
                client_address_zip="90210",

                project_address="123 Main St",
                project_city="Anytown",
                project_state="FL",
                project_zip="12345",

                estimate_date='2023-01-10',
                bid_due_date='2023-01-25',
                project_start_date='2023-02-01',
                completion_date='2023-06-30',

                project_status="Planned",
                contract_type="Fixed Price",

                markup_percentage=0.25,
                overhead_percentage=0.10,
                profit_percentage=0.15,

                scope_of_work="Renovation of kitchen and two bathrooms, including demolition, framing, drywall, painting, and basic plumbing/electrical fixtures.",
                notes='Client prefers communication via email.',

                contract_date='2023-01-15',
                project_description='Renovation of kitchen and two bathrooms.',
                contract_amount=50000.00,
                payment_terms='50% up front, 25% at rough-in, 25% upon completion.',
                change_orders_total=0.00,
                current_contract_amount=50000.00,
                tax_rate=0.07,
                permit_cost=500.00,
                bonding_cost=0.00,
                insurance_cost=250.00,
                misc_expenses=100.00,
                estimated_total_cost=0.0, # Initial value
                final_total_cost=0.0, # Initial value
                total_direct_cost=0.0, # Initial value
                final_project_estimate=0.0 # Initial value
            )
            session.add(initial_project)
            session.commit()

            # Add some line items to the initial project
            if session.query(LineItem).count() == 0:
                print("Populating initial Line Items...")
                lumber_item = session.query(CommonItem).filter_by(name='2x4 Lumber').first()
                drywall_item = session.query(CommonItem).filter_by(name='Drywall Sheet').first()
                painter_labor = session.query(CommonItem).filter_by(name='Painter Hourly Rate').first()

                rough_carpentry_code = session.query(CostCode).filter_by(code='06 10 00').first()
                gypsum_board_code = session.query(CostCode).filter_by(code='09 20 00').first()
                painting_code = session.query(CostCode).filter_by(code='09 90 00').first()

                line_items_data = [
                    LineItem(
                        project=initial_project,
                        description="Rough framing for kitchen walls",
                        quantity=100.0,
                        unit="EA",
                        unit_cost=3.50,
                        markup_percentage=0.20,
                        is_common_item=1,
                        common_item=lumber_item,
                        cost_code=rough_carpentry_code
                    ) if lumber_item and rough_carpentry_code else None,
                    LineItem(
                        project=initial_project,
                        description="Install drywall in kitchen",
                        quantity=20.0,
                        unit="EA",
                        unit_cost=12.00,
                        markup_percentage=0.15,
                        is_common_item=1,
                        common_item=drywall_item,
                        cost_code=gypsum_board_code
                    ) if drywall_item and gypsum_board_code else None,
                    LineItem(
                        project=initial_project,
                        description="Painting kitchen walls (labor)",
                        quantity=40.0,
                        unit="HR",
                        unit_cost=50.00,
                        markup_percentage=0.25,
                        is_common_item=1,
                        common_item=painter_labor,
                        cost_code=painting_code
                    ) if painter_labor and painting_code else None,
                    LineItem(
                        project=initial_project,
                        description="Demolition of existing kitchen cabinets",
                        quantity=1.0,
                        unit="LS",
                        unit_cost=800.00,
                        markup_percentage=0.10,
                        is_common_item=0, # Custom item
                        common_item=None,
                        cost_code=None # No specific cost code for this example
                    )
                ]
                valid_line_items = [item for item in line_items_data if item is not None]
                session.add_all(valid_line_items)
                session.commit()

    except Exception as e:
        session.rollback()
        print(f"DEBUG: Database Error during initialization: {e}")
    finally:
        session.close()

if not os.path.exists(DATABASE_PATH):
    print(f"Database file not found at {DATABASE_PATH}. Creating new database and tables.")
    create_db_and_tables()
else:
    print(f"Database file found at {DATABASE_PATH}. Ensuring tables exist.")
    create_db_and_tables()

Session = sessionmaker(bind=engine)