import pytest
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user

# Assuming conftest.py is in the same directory or accessible in python path
# and models.py is in the parent directory.
# The path adjustment in conftest.py should handle this.
from models import User, db as sqlalchemy_db # Renamed to avoid conflict with pytest 'db' fixture if any

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

    with test_app.app_context():
        user = User.query.filter_by(username='testuser1').first()
        assert user is not None
        assert user.name == 'Test User'
        assert user.bio == 'Test bio'
        assert user.web_color == '#123456'
        assert check_password_hash(user.password_hash, 'password123')

def test_registration_existing_username(client, test_app):
    """Test registration with an already existing username."""
    # First, register a user
    client.post('/register', data={
        'name': 'Original User',
        'username': 'existinguser',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    # Then, attempt to register another user with the same username
    response = client.post('/register', data={
        'name': 'Another User',
        'username': 'existinguser', # Same username
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)

    assert response.status_code == 200 # Stays on the registration page
    assert b"That username is already taken." in response.data # Check for error message

    with test_app.app_context():
        users_count = User.query.filter_by(username='existinguser').count()
        assert users_count == 1 # Ensure no new user was created with the same username

# === Login/Logout Tests ===

def test_login_page_loads(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login</h1>" in response.data

def test_successful_login_logout(client, test_app):
    """Test successful login and then logout."""
    # 1. Register a user first
    with test_app.app_context():
        hashed_password = generate_password_hash('testpass')
        user = User(username='loginuser', password_hash=hashed_password, name='Login Test')
        sqlalchemy_db.session.add(user)
        sqlalchemy_db.session.commit()

    # 2. Attempt Login
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'testpass'
    }, follow_redirects=False) # Check redirect before it happens

    assert response.status_code == 302
    assert '/dashboard' in response.location 

    # 2.1. Follow the redirect to check the dashboard and current_user
    response = client.get(response.location, follow_redirects=True) # Follow the redirect
    assert response.status_code == 200
    assert b"Welcome, Login Test!" in response.data # Assuming name is displayed on dashboard
    
    # To check current_user, we need to be within a request context or use a helper
    # A simple way is to check a route that displays username or requires login
    # The navbar in base.html displays "Logout" if authenticated
    assert b"Logout</a>" in response.data 

    # 3. Attempt Logout
    response_logout = client.get('/logout', follow_redirects=False)
    assert response_logout.status_code == 302
    assert '/login' in response_logout.location

    # 3.1 Follow redirect and check if user is logged out
    response_after_logout = client.get(response_logout.location, follow_redirects=True)
    assert response_after_logout.status_code == 200
    assert b"Login</h1>" in response_after_logout.data # Should be back on login page
    
    # Check navbar links again, "Logout" should not be present
    assert b"Logout</a>" not in response_after_logout.data
    assert b"Login</a>" in response_after_logout.data


def test_login_invalid_username(client):
    """Test login with an invalid username."""
    response = client.post('/login', data={
        'username': 'nonexistentuser',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200 # Stays on login page
    assert b"Login Unsuccessful. Please check username and password" in response.data

def test_login_invalid_password(client, test_app):
    """Test login with a valid username but invalid password."""
    # Register a user
    with test_app.app_context():
        hashed_password = generate_password_hash('correctpassword')
        user = User(username='userwithcorrectpass', password_hash=hashed_password)
        sqlalchemy_db.session.add(user)
        sqlalchemy_db.session.commit()

    response = client.post('/login', data={
        'username': 'userwithcorrectpass',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200 # Stays on login page
    assert b"Login Unsuccessful. Please check username and password" in response.data
