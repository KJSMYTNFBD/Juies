import pytest
from flask_login import current_user, login_user
from models import db as sqlalchemy_db, User, Note, Tag # Renamed to avoid conflict
from werkzeug.security import generate_password_hash

# === Note Creation Tests ===

def test_create_note_page_loads_when_logged_in(auth_client):
    """Test that the create note page loads correctly when logged in."""
    response = auth_client.get('/create_note')
    assert response.status_code == 200
    assert b"Create New Note" in response.data

def test_create_note_requires_login(client):
    """Test that accessing /create_note redirects to login if not authenticated."""
    response = client.get('/create_note', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location
    
    response_redirect = client.get('/create_note', follow_redirects=True)
    assert response_redirect.status_code == 200 # Should land on login page
    assert b"Login</h1>" in response_redirect.data

def test_successful_note_creation_with_tags(auth_client, test_app):
    """Test successful note creation with title, content, and tags."""
    response = auth_client.post('/create_note', data={
        'title': 'My Test Note',
        'content': 'This is the content of my test note.',
        'tags': 'test, flask, python'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.location

    with test_app.app_context():
        # User 'testuser' is created by auth_client fixture
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        
        note = Note.query.filter_by(title='My Test Note', user_id=user.id).first()
        assert note is not None
        assert note.content == 'This is the content of my test note.'
        
        assert len(note.tags) == 3
        tag_names = sorted([tag.name for tag in note.tags])
        assert tag_names == sorted(['test', 'flask', 'python'])
        
        # Check if tags were added to the Tag table
        assert Tag.query.filter_by(name='test').first() is not None
        assert Tag.query.filter_by(name='flask').first() is not None
        assert Tag.query.filter_by(name='python').first() is not None

def test_successful_note_creation_without_tags(auth_client, test_app):
    """Test successful note creation with only title and content."""
    response = auth_client.post('/create_note', data={
        'title': 'Note Without Tags',
        'content': 'Content for note without tags.',
        'tags': '' # Empty tags field
    }, follow_redirects=True) # follow_redirects=True to land on dashboard

    assert response.status_code == 200 # Should be on dashboard
    assert b"Your note has been created!" in response.data # Check flash message

    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        note = Note.query.filter_by(title='Note Without Tags', user_id=user.id).first()
        assert note is not None
        assert note.content == 'Content for note without tags.'
        assert len(note.tags) == 0

# === Note Editing Tests ===

def test_edit_note_page_loads_for_author(auth_client, test_app):
    """Test that the edit note page loads for the note's author."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        note = Note(title="Editable Note", content="Initial content", author=user)
        sqlalchemy_db.session.add(note)
        sqlalchemy_db.session.commit()
        note_id = note.id

    response = auth_client.get(f'/note/{note_id}/edit')
    assert response.status_code == 200
    assert b"Edit Note" in response.data
    assert b"Editable Note" in response.data # Check if form is pre-filled
    assert b"Initial content" in response.data

def test_edit_note_forbidden_for_non_author(auth_client, test_app):
    """Test that editing is forbidden if the logged-in user is not the author."""
    with test_app.app_context():
        # Create another user and their note
        other_user = User(username="otheruser", name="Other User", password_hash=generate_password_hash("otherpass"))
        sqlalchemy_db.session.add(other_user)
        sqlalchemy_db.session.flush() # Ensure other_user gets an ID
        
        note_by_other = Note(title="Other's Note", content="Belongs to other", author=other_user)
        sqlalchemy_db.session.add(note_by_other)
        sqlalchemy_db.session.commit()
        note_id = note_by_other.id

    # auth_client is logged in as 'testuser'
    response = auth_client.get(f'/note/{note_id}/edit')
    assert response.status_code == 403 # Forbidden

def test_successful_note_update(auth_client, test_app):
    """Test successfully updating a note's title, content, and tags."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        tag_initial = Tag(name="initial")
        note = Note(title="Old Title", content="Old Content", author=user, tags=[tag_initial])
        sqlalchemy_db.session.add_all([tag_initial, note])
        sqlalchemy_db.session.commit()
        note_id = note.id

    response = auth_client.post(f'/note/{note_id}/edit', data={
        'title': 'New Updated Title',
        'content': 'New updated content.',
        'tags': 'updated, newtag'
    }, follow_redirects=True)

    assert response.status_code == 200 # Should be on dashboard
    assert b"Your note has been updated!" in response.data

    with test_app.app_context():
        updated_note = Note.query.get(note_id)
        assert updated_note.title == 'New Updated Title'
        assert updated_note.content == 'New updated content.'
        
        tag_names = sorted([tag.name for tag in updated_note.tags])
        assert tag_names == sorted(['updated', 'newtag'])
        assert Tag.query.filter_by(name="initial").first() is not None # Initial tag should still exist
        assert Tag.query.filter_by(name="updated").first() is not None
        assert Tag.query.filter_by(name="newtag").first() is not None


# === Note Deletion Tests ===

def test_successful_note_deletion_by_author(auth_client, test_app):
    """Test that the author can successfully delete their note."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        note_to_delete = Note(title="Delete Me", content="This note will be deleted.", author=user)
        sqlalchemy_db.session.add(note_to_delete)
        sqlalchemy_db.session.commit()
        note_id = note_to_delete.id
        assert Note.query.get(note_id) is not None # Confirm it's in DB

    response = auth_client.post(f'/note/{note_id}/delete', follow_redirects=True)
    
    assert response.status_code == 200 # Should be on dashboard
    assert b"Your note has been deleted!" in response.data

    with test_app.app_context():
        assert Note.query.get(note_id) is None # Confirm it's gone from DB

def test_note_deletion_forbidden_for_non_author(auth_client, test_app):
    """Test that deleting a note is forbidden if not the author."""
    with test_app.app_context():
        other_user = User(username="anotheruser", name="Another User", password_hash=generate_password_hash("anotherpass"))
        sqlalchemy_db.session.add(other_user)
        sqlalchemy_db.session.flush()
        
        note_by_other = Note(title="Protected Note", content="Cannot be deleted by testuser", author=other_user)
        sqlalchemy_db.session.add(note_by_other)
        sqlalchemy_db.session.commit()
        note_id = note_by_other.id

    response = auth_client.post(f'/note/{note_id}/delete', follow_redirects=True)
    assert response.status_code == 403 # Forbidden

    with test_app.app_context():
        assert Note.query.get(note_id) is not None # Note should still exist
