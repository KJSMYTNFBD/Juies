import pytest
import os
import tempfile

# Adjust the Python path to include the root directory
# This allows 'from app import app' and 'from models import db' to work
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the main application
from app import app as flask_app 
from models import db as sqlalchemy_db, User, Note, Tag # Import all models

@pytest.fixture(scope='session')
def test_app_instance():
    """
    Creates a Flask app instance for the test session.
    This is scoped to 'session' to avoid recreating the app for every test function,
    but the database setup/teardown will be per function or as needed.
    """
    # Use a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False, # Disable CSRF for easier form testing
        "SECRET_KEY": "test_secret_key", # Consistent secret key for tests
        "LOGIN_DISABLED": False # Ensure login is not disabled unless specifically tested
    })

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture()
def test_app(test_app_instance):
    """
    Provides the Flask app with a clean database for each test function.
    """
    with test_app_instance.app_context():
        sqlalchemy_db.create_all()
        yield test_app_instance # The app itself
        sqlalchemy_db.session.remove() # Ensure session is closed
        sqlalchemy_db.drop_all()


@pytest.fixture()
def client(test_app):
    """
    Provides a test client for the Flask application.
    This fixture depends on `test_app` to ensure the app context and database are set up.
    """
    return test_app.test_client()

@pytest.fixture()
def runner(test_app):
    """
    Provides a test CLI runner for the Flask application.
    """
    return test_app.test_cli_runner()


@pytest.fixture()
def init_database(test_app):
    """
    Fixture to set up initial data in the database if needed.
    For now, it just ensures tables are created (which test_app already does).
    This can be expanded to create default users, notes, etc.
    """
    # test_app fixture already creates tables and drops them.
    # If you need specific pre-populated data for a set of tests, add it here.
    # Example:
    # user = User(username='testuser', password_hash=generate_password_hash('password'))
    # db.session.add(user)
    # db.session.commit()
    yield sqlalchemy_db # Yield the db instance if tests need to use it directly for setup
    # Teardown is handled by test_app fixture
    pass

@pytest.fixture
def auth_client(client, test_app):
    """
    Provides a test client that is pre-authenticated with a test user.
    This is a helper fixture for tests that require a logged-in user.
    """
    from werkzeug.security import generate_password_hash

    with test_app.app_context():
        # Create a test user directly in the database
        test_user = User(
            username="testuser",
            name="Test User",
            password_hash=generate_password_hash("password")
        )
        sqlalchemy_db.session.add(test_user)
        sqlalchemy_db.session.commit()

    # Log in the user through the client
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password'
    }, follow_redirects=True)
    
    assert response.status_code == 200 # Should be on dashboard or wherever login redirects
    # print("Auth client response data:", response.data.decode()) # For debugging
    # assert b"Login successful!" in response.data # Check for flash message if applicable after redirect

    return client # Return the same client, now with session cookies set
