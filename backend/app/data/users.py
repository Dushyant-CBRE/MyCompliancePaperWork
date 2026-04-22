from typing import List
from app.models.user import User

USERS: List[User] = [
    User(
        id=1,
        username="john.doe",
        email="john.doe@mycompliance.com",
        full_name="John Doe",
        role="Admin",
        is_active=True,
        phone="+1-555-0101",
        department="IT",
    ),
    User(
        id=2,
        username="jane.smith",
        email="jane.smith@mycompliance.com",
        full_name="Jane Smith",
        role="Compliance Officer",
        is_active=True,
        phone="+1-555-0102",
        department="Legal",
    ),
    User(
        id=3,
        username="bob.johnson",
        email="bob.johnson@mycompliance.com",
        full_name="Bob Johnson",
        role="Analyst",
        is_active=False,
        phone="+1-555-0103",
        department="Finance",
    ),
    User(
        id=4,
        username="alice.williams",
        email="alice.williams@mycompliance.com",
        full_name="Alice Williams",
        role="Manager",
        is_active=True,
        phone="+1-555-0104",
        department="Operations",
    ),
]
