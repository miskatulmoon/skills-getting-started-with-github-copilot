"""
Pytest configuration and fixtures for the activity management system tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient for making HTTP requests to the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def clean_activities():
    """
    Fixture that resets the in-memory activities database to a clean state
    before and after each test. This ensures test isolation.
    """
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def sample_activity():
    """
    Fixture providing sample test data for activities.
    Useful for parametrized or data-driven tests.
    """
    return {
        "name": "Test Club",
        "email": "student@test.edu",
        "full_activity": {
            "description": "A test activity",
            "schedule": "Test Time",
            "max_participants": 2,
            "participants": ["existing@test.edu"]
        }
    }
