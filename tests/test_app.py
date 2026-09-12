"""
Test suite for the High School Activities API.
Uses AAA (Arrange-Act-Assert) pattern for test structure clarity.
"""

import pytest
from src.app import activities


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, clean_activities):
        """
        Arrange: API is set up with activity data
        Act: Call GET /activities
        Assert: Response includes all activities with correct structure
        """
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data) > 0
        
        # Verify each activity has required fields
        for activity_name, activity_details in activities_data.items():
            assert isinstance(activity_name, str)
            assert all(key in activity_details for key in expected_keys)
    
    def test_get_activities_returns_chess_club(self, client, clean_activities):
        """
        Arrange: Chess Club exists in the database
        Act: Call GET /activities
        Assert: Chess Club is present in response
        """
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert activity_name in activities_data
        assert "description" in activities_data[activity_name]
        assert "participants" in activities_data[activity_name]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_for_activity_success(self, client, clean_activities):
        """
        Arrange: Chess Club exists with available spots
        Act: Sign up a new student for Chess Club
        Assert: Response confirms successful signup
        """
        # Arrange
        activity_name = "Chess Club"
        email = "netstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, clean_activities):
        """
        Arrange: Chess Club has initial participants
        Act: Sign up a new student
        Assert: Participant is added to the activity's participant list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_participants = len(activities[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        updated_participants = activities[activity_name]["participants"]
        assert len(updated_participants) == initial_participants + 1
        assert email in updated_participants
    
    def test_signup_fails_when_activity_at_capacity(self, client, clean_activities):
        """
        Arrange: Create an activity with max capacity of 2 and 2 existing participants
        Act: Try to sign up a third student
        Assert: Response is 400 with capacity error message
        """
        # Arrange
        activity_name = "Test Activity"
        activities[activity_name] = {
            "description": "Test",
            "schedule": "Test",
            "max_participants": 2,
            "participants": ["user1@test.edu", "user2@test.edu"]
        }
        new_email = "user3@test.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"].lower()
        assert len(activities[activity_name]["participants"]) == 2
        
        # Cleanup
        del activities[activity_name]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/participant/{email}/unregister endpoint."""
    
    def test_unregister_removes_participant_from_activity(self, client, clean_activities):
        """
        Arrange: Programming Class has Emma signed up
        Act: Unregister Emma from Programming Class
        Assert: Emma is removed from the participants list
        """
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"
        assert email in activities[activity_name]["participants"]
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant/{email}/unregister"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_updates_participant_list(self, client, clean_activities):
        """
        Arrange: Gym Class has participants
        Act: Unregister John and verify with GET /activities
        Assert: John is no longer in the participant list
        """
        # Arrange
        activity_name = "Gym Class"
        email = "john@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/participant/{email}/unregister"
        )
        response = client.get("/activities")
        
        # Assert
        updated_activity = response.json()[activity_name]
        assert email not in updated_activity["participants"]


class TestRootEndpoint:
    """Tests for the GET / endpoint."""
    
    def test_root_redirects_to_index(self, client):
        """
        Arrange: Root endpoint is configured with redirect
        Act: Call GET /
        Assert: Response is a redirect (301 or 307) to /static/index.html
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code in [301, 302, 307]
        assert "/static/index.html" in response.headers.get("location", "")


class TestSequentialOperations:
    """Tests for sequential operations (signup -> unregister -> re-signup)."""
    
    def test_signup_unregister_signup_sequence(self, client, clean_activities):
        """
        Arrange: Soccer Club with available spots
        Act: Sign up, unregister, sign up again with same email
        Assert: All operations succeed and final state shows student registered once
        """
        # Arrange
        activity_name = "Soccer Club"
        email = "retest@mergington.edu"
        
        # Act: First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: First signup succeeds
        assert response1.status_code == 200
        assert email in activities[activity_name]["participants"]
        first_count = len(activities[activity_name]["participants"])
        
        # Act: Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/participant/{email}/unregister"
        )
        
        # Assert: Unregister succeeds
        assert response2.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == first_count - 1
        
        # Act: Re-signup
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Re-signup succeeds and student appears once
        assert response3.status_code == 200
        assert email in activities[activity_name]["participants"]
        assert activities[activity_name]["participants"].count(email) == 1
        assert len(activities[activity_name]["participants"]) == first_count
