import pytest
import os
import tempfile
import shutil # For cleaning up temporary data directory
import pytest

# Adjust the Python path to include the root directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the main application
from app import app as flask_app
import json_store # Import our json_store module
from user import JsonUser # Import the actual JsonUser class

@pytest.fixture(scope='session')
def test_app_instance(tmp_path_factory):
    """
    Creates a Flask app instance for the test session.
    Uses a temporary directory for JSON data storage.
    """
    # Create a temporary directory for the data for this test session
    temp_data_dir = tmp_path_factory.mktemp("data")
    
    # Monkeypatch json_store's DATA_DIR, USER_DATA_DIR, NOTE_DATA_DIR
    # This is crucial so that json_store functions use the temp directory
    original_data_dir = json_store.DATA_DIR
    original_user_dir = json_store.USER_DATA_DIR
    original_note_dir = json_store.NOTE_DATA_DIR

    json_store.DATA_DIR = str(temp_data_dir)
    json_store.USER_DATA_DIR = os.path.join(json_store.DATA_DIR, 'users')
    json_store.NOTE_DATA_DIR = os.path.join(json_store.DATA_DIR, 'notes')

    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key",
        "LOGIN_DISABLED": False
    })

    yield flask_app

    # Teardown: Restore original paths and remove temp directory
    json_store.DATA_DIR = original_data_dir
    json_store.USER_DATA_DIR = original_user_dir
    json_store.NOTE_DATA_DIR = original_note_dir
    # shutil.rmtree(temp_data_dir) # tmp_path_factory handles cleanup

@pytest.fixture()
def test_app(test_app_instance):
    """
    Provides the Flask app instance for each test function.
    Ensures the temporary data store is initialized for each test.
    """
    # Ensure data directories are created within the temp_data_dir for each test
    json_store.init_data_store()
    
    with test_app_instance.app_context():
        yield test_app_instance
    
    # Clean up files within the temp data store after each test if necessary,
    # or rely on session-scoped cleanup if that's preferred.
    # For per-test isolation of data:
    if os.path.exists(json_store.USER_DATA_DIR):
        for f in os.listdir(json_store.USER_DATA_DIR):
            os.remove(os.path.join(json_store.USER_DATA_DIR, f))
    if os.path.exists(json_store.NOTE_DATA_DIR):
        for f in os.listdir(json_store.NOTE_DATA_DIR):
            os.remove(os.path.join(json_store.NOTE_DATA_DIR, f))


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
    # This fixture is mainly for ensuring the app context is active for tests
    # that might need it for URL building, etc., even if not directly using db.
    pass


@pytest.fixture
def auth_client(client, test_app):
    """
    Provides a test client that is pre-authenticated with a test user.
    Uses json_store to save the test user.
    """
    from werkzeug.security import generate_password_hash

    user_data = {
        "username": "testuser",
        "name": "Test User",
        "password_hash": generate_password_hash("password"),
        "note_ids": [] # Initialize with empty notes
    }
    # Save user directly using json_store within the app context provided by test_app
    with test_app.app_context():
        json_store.save_user(user_data)

    # Log in the user through the client
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password'
    }, follow_redirects=True)
    
    assert response.status_code == 200 # Should be on dashboard or wherever login redirects
    # print("Auth client response data:", response.data.decode()) # For debugging
    # assert b"Login successful!" in response.data # Check for flash message if applicable after redirect

    return client # Return the same client, now with session cookies set
