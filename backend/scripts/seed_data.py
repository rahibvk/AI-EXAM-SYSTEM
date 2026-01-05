"""
Initial Data Seeder

Purpose:
    Bootstraps the database with default users for each role:
    - Admin (admin@example.com)
    - Teacher (teacher@example.com)
    - Student (student@example.com)
    
    Should be run once after fresh DB creation.
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole

async def seed_data():
    """Seeds 3 default users."""
    async with SessionLocal() as db:
        # Create Admin
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)

        # Create Teacher
        teacher = User(
            email="teacher@example.com",
            hashed_password=get_password_hash("teacher123"),
            full_name="John Professor",
            role=UserRole.TEACHER,
            is_active=True
        )
        db.add(teacher)

        # Create Student
        student = User(
            email="student@example.com",
            hashed_password=get_password_hash("student123"),
            full_name="Jane Student",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(student)

        try:
            await db.commit()
            print("Seeding successful!")
        except Exception as e:
            await db.rollback()
            print(f"Seeding failed (maybe users exist): {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
