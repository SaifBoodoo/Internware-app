import typer
from sqlmodel import select
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from app.utilities.security import encrypt_password

cli = typer.Typer()

@cli.command()
def initialize():
    """Wipe and seed the database with test users and profiles."""
    with get_cli_session() as db:
        print("Wiping database...")
        drop_all()
        create_db_and_tables()

        # 1. Create Admin
        admin_auth = User(
            username='admin', 
            email='admin@internware.com', 
            password=encrypt_password('adminpass'), # Matches model field
            role='admin'
        )
        db.add(admin_auth)
        db.commit() # Commit to generate ID

        # 2. Create Student (Bob)
        student_user = User(
            username='bob', 
            email='bob@university.edu', 
            password=encrypt_password('bobpass'), # Matches model field
            role='student'
        )
        db.add(student_user)
        db.commit() 
        db.refresh(student_user)

        # Link Student Profile - Now Bob will definitely have a profile record
        student_profile = StudentProfile(
            user_id=student_user.id,
            name="Bob Smith",
            major="Computer Science",
            gpa=3.85,
            graduation_year=2027,
            skills="Python, FastAPI, SQLModel"
        )
        db.add(student_profile)
        db.commit()

        # 3. Create Company
        company_user = User(
            username='techcorp', 
            email='hr@techcorp.com', 
            password=encrypt_password('companypass'), # Matches model field
            role='company'
        )
        db.add(company_user)
        db.commit()
        db.refresh(company_user)

        # Link Company Profile
        company_profile = CompanyProfile(
            user_id=company_user.id,
            company_name="TechCorp Solutions",
            industry="Software Engineering",
            location="San Francisco, CA"
        )
        db.add(company_profile)
        db.commit()
        db.refresh(company_profile)

        # 4. Create Sample Projects
        # Project 1: Standard Backend
        sample_project = Project(
            title="Backend Development Internship",
            description="Work on high-scale FastAPI microservices.",
            requirements="Basic knowledge of Python and REST APIs.",
            duration=5, # Using this as the 'spots available' count
            stipend=2500.0,
            location="Remote",
            company_id=company_profile.id
        )
        
        # Project 2: For variety/testing UI layout
        ui_project = Project(
            title="Frontend UI/UX Intern",
            description="Help us build beautiful Jinja2 templates.",
            requirements="HTML, CSS, and a bit of Javascript.",
            duration=3,
            stipend=2000.0,
            location="San Francisco, CA",
            company_id=company_profile.id
        )
        
        db.add(sample_project)
        db.add(ui_project)
        db.commit()

        print("--- Seed Data Created ---")
        print("Admin: admin / adminpass")
        print("Student: bob / bobpass")
        print("Company: techcorp / companypass")

@cli.command()
def stats():
    """Quick check of database counts."""
    with get_cli_session() as db:
        u_count = len(db.exec(select(User)).all())
        p_count = len(db.exec(select(Project)).all())
        s_count = len(db.exec(select(StudentProfile)).all())
        print(f"Users: {u_count}")
        print(f"Student Profiles: {s_count}")
        print(f"Projects: {p_count}")

if __name__ == "__main__":
    cli()