import pytest
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user

# Assuming conftest.py is in the same directory or accessible in python path
# and models.py is in the parent directory.
# The path adjustment in conftest.py should handle this.
# Removed: from models import User, db as sqlalchemy_db
# Removed: from app import TempUser, TEMP_USERS, TEMP_USER_ID_COUNTER
import json_store # For checking file system directly

# === Registration Tests ===

def test_register_page_loads(client):
    """Test that the registration page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Register</h1>" in response.data # Check for a unique element

def test_successful_registration(client, test_app):
    """Test successful user registration."""
    response = client.post('/register', data={
        'name': 'Test User',
        'username': 'testuser1',
        'password': 'password123',
        'confirm_password': 'password123',
        'bio': 'Test bio',
        'web_color': '#123456'
    }, follow_redirects=False) # Important: follow_redirects=False to check 302
    
    assert response.status_code == 302 # Should redirect
    assert '/login' in response.location

    # Verify user data was saved correctly
    user_data = json_store.get_user('testuser1')
    assert user_data is not None
    assert user_data['name'] == 'Test User'
    assert user_data['bio'] == 'Test bio'
    assert user_data['web_color'] == '#123456'
    assert 'note_ids' in user_data # Should be initialized, likely empty
    assert check_password_hash(user_data['password_hash'], 'password123')

def test_registration_existing_username(client, test_app):
    """Test registration with an already existing username."""
    # First, register a user (this will create a user file via the route)
    initial_user_data = {
        'name': 'Original User',
        'username': 'existinguser',
        'password': 'password123',
        'confirm_password': 'password123'
    }
    client.post('/register', data=initial_user_data, follow_redirects=True)

    # Then, attempt to register another user with the same username
    response = client.post('/register', data={
        'name': 'Another User',
        'username': 'existinguser', # Same username
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)

    assert response.status_code == 200 # Stays on the registration page
    assert b"That username is already taken." in response.data # Check for error message

    # Verify that only one user file for 'existinguser' exists
    # This check is implicitly handled by json_store.save_user overwriting if allowed,
    # but the form validation should prevent this.
    # We can check the number of users or specific content if needed.
    all_users = json_store.get_all_users()
    existing_user_count = sum(1 for u in all_users if u['username'] == 'existinguser')
    assert existing_user_count == 1

# === Login/Logout Tests ===

def test_login_page_loads(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login</h1>" in response.data

def test_successful_login_logout(client, test_app):
    """Test successful login and then logout."""
    # 1. Create a user directly using json_store
    user_to_login_data = {
        "username": "loginuser",
        "name": "Login Test",
        "password_hash": generate_password_hash("testpass"),
        "note_ids": []
    }
    json_store.save_user(user_to_login_data)

    # 2. Attempt Login
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'testpass'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.location

    # 2.1. Follow the redirect to check the dashboard
    response_dashboard = client.get(response.location, follow_redirects=True)
    assert response_dashboard.status_code == 200
    assert b"Welcome, Login Test!" in response_dashboard.data
    assert b"Logout</a>" in response_dashboard.data

    # 3. Attempt Logout
    response_logout = client.get('/logout', follow_redirects=False)
    assert response_logout.status_code == 302
    assert '/login' in response_logout.location

    # 3.1 Follow redirect and check if user is logged out
    response_after_logout = client.get(response_logout.location, follow_redirects=True)
    assert response_after_logout.status_code == 200
    assert b"Login</h1>" in response_after_logout.data
    assert b"Logout</a>" not in response_after_logout.data
    assert b"Login</a>" in response_after_logout.data


def test_login_invalid_username(client):
    """Test login with an invalid username."""
    response = client.post('/login', data={
        'username': 'nonexistentuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Login Unsuccessful. Please check username and password" in response.data

def test_login_invalid_password(client, test_app):
    """Test login with a valid username but invalid password."""
    # Create a user directly using json_store
    user_data_for_pass_test = {
        "username": "userwithcorrectpass",
        "password_hash": generate_password_hash("correctpassword"),
        "note_ids": []
    }
    json_store.save_user(user_data_for_pass_test)
        
    response = client.post('/login', data={
        'username': 'userwithcorrectpass',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Login Unsuccessful. Please check username and password" in response.data
