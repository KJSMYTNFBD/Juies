import pytest
from flask_login import current_user, login_user # Keep for auth_client usage
# Removed: from models import db as sqlalchemy_db, User, Note, Tag
# from app import TempUser # If we need to interact with user objects directly
from werkzeug.security import generate_password_hash # Keep if creating users for non-DB auth tests

import json_store # For direct data manipulation and verification
import os

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
        'title': 'My Test Note with Tags',
        'content': 'This is the content of my test note with tags.',
        'tags': 'test, flask, python'
    }, follow_redirects=False)

    assert response.status_code == 302 # Redirects to dashboard
    assert '/dashboard' in response.location

    # Verify note file and user file
    user_data = json_store.get_user('testuser') # 'testuser' is from auth_client
    assert user_data is not None
    assert len(user_data['note_ids']) > 0
    
    note_id = user_data['note_ids'][-1] # Assume last added
    note_data = json_store.get_note(note_id)
    assert note_data is not None
    assert note_data['title'] == 'My Test Note with Tags'
    assert note_data['content'] == 'This is the content of my test note with tags.'
    assert note_data['user_id'] == 'testuser'
    assert sorted(note_data['tags']) == sorted(['test', 'flask', 'python'])
    assert 'created_at' in note_data
    assert 'updated_at' in note_data

def test_successful_note_creation_without_tags(auth_client, test_app):
    """Test successful note creation with only title and content."""
    response = auth_client.post('/create_note', data={
        'title': 'Note Without Tags',
        'content': 'Content for note without tags.',
        'tags': '' # Empty tags field
    }, follow_redirects=True) 

    assert response.status_code == 200 # Lands on dashboard
    assert b"Your note has been created!" in response.data 

    user_data = json_store.get_user('testuser')
    assert user_data is not None
    assert len(user_data['note_ids']) > 0 

    note_id = user_data['note_ids'][-1] 
    note_data = json_store.get_note(note_id)
    assert note_data is not None
    assert note_data['title'] == 'Note Without Tags'
    assert note_data['tags'] == []

# === Note Editing Tests ===

def test_edit_note_page_loads_for_author(auth_client, test_app):
    """Test that the edit note page loads for the note's author."""
    user_data = json_store.get_user('testuser')
    note_id = json_store.generate_note_id()
    note_data = {
        "id": note_id, "user_id": "testuser", 
        "title": "Editable Note", "content": "Initial content", "tags": ["original"]
    }
    json_store.save_note(note_data)
    user_data['note_ids'].append(note_id)
    json_store.save_user(user_data)

    response = auth_client.get(f'/note/{note_id}/edit')
    assert response.status_code == 200
    assert b"Edit Note" in response.data
    assert b"Editable Note" in response.data 
    assert b"Initial content" in response.data
    assert b"original" in response.data # Check for tag

def test_edit_note_forbidden_for_non_author(auth_client, test_app):
    """Test that editing is forbidden if the logged-in user is not the author."""
    other_user_data = {
        "username": "otheruser", "password_hash": generate_password_hash("otherpass"), "note_ids": []
    }
    json_store.save_user(other_user_data)
    
    note_id = json_store.generate_note_id()
    note_by_other_data = {
        "id": note_id, "user_id": "otheruser", 
        "title": "Other's Note", "content": "Belongs to other", "tags": []
    }
    json_store.save_note(note_by_other_data)
    other_user_data['note_ids'].append(note_id)
    json_store.save_user(other_user_data)

    response = auth_client.get(f'/note/{note_id}/edit') # auth_client is 'testuser'
    assert response.status_code == 403

def test_successful_note_update(auth_client, test_app):
    """Test successfully updating a note's title, content, and tags."""
    user_data = json_store.get_user('testuser')
    note_id = json_store.generate_note_id()
    original_note_data = {
        "id": note_id, "user_id": "testuser",
        "title": "Old Title", "content": "Old Content", "tags": ["oldtag"]
    }
    json_store.save_note(original_note_data)
    user_data['note_ids'].append(note_id)
    json_store.save_user(user_data)
    
    original_updated_at = json_store.get_note(note_id).get('updated_at')


    response = auth_client.post(f'/note/{note_id}/edit', data={
        'title': 'New Updated Title',
        'content': 'New updated content.',
        'tags': 'updated, newtag'
    }, follow_redirects=True)

    assert response.status_code == 200 
    assert b"Your note has been updated!" in response.data

    updated_note_data = json_store.get_note(note_id)
    assert updated_note_data is not None
    assert updated_note_data['title'] == 'New Updated Title'
    assert updated_note_data['content'] == 'New updated content.'
    assert sorted(updated_note_data['tags']) == sorted(['updated', 'newtag'])
    assert 'updated_at' in updated_note_data
    assert updated_note_data['updated_at'] != original_updated_at # Check timestamp changed

# === Note Deletion Tests ===

def test_successful_note_deletion_by_author(auth_client, test_app):
    """Test that the author can successfully delete their note."""
    user_data = json_store.get_user('testuser')
    note_id = json_store.generate_note_id()
    note_to_delete_data = {
        "id": note_id, "user_id": "testuser",
        "title": "Delete Me", "content": "This note will be deleted.", "tags": []
    }
    json_store.save_note(note_to_delete_data)
    user_data['note_ids'].append(note_id)
    json_store.save_user(user_data)
    
    assert json_store.get_note(note_id) is not None # Confirm it's in store

    response = auth_client.post(f'/note/{note_id}/delete', follow_redirects=True)
    
    assert response.status_code == 200 
    assert b"Your note has been deleted!" in response.data

    assert json_store.get_note(note_id) is None # Confirm it's gone
    updated_user_data = json_store.get_user('testuser')
    assert note_id not in updated_user_data['note_ids']

def test_note_deletion_forbidden_for_non_author(auth_client, test_app):
    """Test that deleting a note is forbidden if not the author."""
    other_user_data = {
        "username": "anotheruser", "password_hash": generate_password_hash("anotherpass"), "note_ids": []
    }
    json_store.save_user(other_user_data)
    
    note_id = json_store.generate_note_id()
    note_by_other_data = {
        "id": note_id, "user_id": "anotheruser",
        "title": "Protected Note", "content": "Cannot be deleted by testuser", "tags": []
    }
    json_store.save_note(note_by_other_data)
    other_user_data['note_ids'].append(note_id)
    json_store.save_user(other_user_data)

    response = auth_client.post(f'/note/{note_id}/delete') # No redirect following to check 403 directly
    assert response.status_code == 403 

    assert json_store.get_note(note_id) is not None # Note should still exist
