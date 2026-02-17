"""
Tests for the Mergington High School API

Tests cover:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Reset to initial state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
    })
    yield
    # Cleanup after test
    activities.clear()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activity_participants_are_strings(self, client):
        """Test that participants are email strings"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_returns_200(self, client):
        """Test that signing up a new student returns 200"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_returns_success_message(self, client):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds the student to participants"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered_returns_400(self, client):
        """Test that signing up an already registered student returns 400"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_students_different_activities(self, client):
        """Test signing up multiple students for different activities"""
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        activities_list = ["Chess Club", "Programming Class"]
        
        for email, activity in zip(emails, activities_list):
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert "student1@mergington.edu" in data["Chess Club"]["participants"]
        assert "student2@mergington.edu" in data["Programming Class"]["participants"]

    def test_signup_same_student_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "student@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]

    def test_signup_preserves_existing_participants(self, client):
        """Test that signup doesn't remove existing participants"""
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Chess Club"]["participants"].copy()
        
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        final_response = client.get("/activities")
        final_participants = final_response.json()["Chess Club"]["participants"]
        
        # All original participants should still be there
        for participant in initial_participants:
            assert participant in final_participants


class TestRoot:
    """Tests for root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Redirect status
        assert "/static" in response.headers["location"]
