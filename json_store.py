import os
import json
import uuid
from datetime import datetime

# Constants for Data Paths
DATA_DIR = 'data'
USER_DATA_DIR = os.path.join(DATA_DIR, 'users')
NOTE_DATA_DIR = os.path.join(DATA_DIR, 'notes')

# --- Directory Initialization ---
def init_data_store():
    """Creates data directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(NOTE_DATA_DIR, exist_ok=True)

# --- User Data Functions ---
def get_user_filepath(username):
    """Returns the filepath for a given username's JSON data file."""
    return os.path.join(USER_DATA_DIR, f"{username}.json")

def save_user(user_data):
    """Saves user data to a JSON file. user_data should be a dictionary."""
    if 'username' not in user_data:
        raise ValueError("User data must contain a 'username' field.")
    
    filepath = get_user_filepath(user_data['username'])
    try:
        with open(filepath, 'w') as f:
            json.dump(user_data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving user {user_data['username']}: {e}")
        return False

def get_user(username):
    """Loads user data from a JSON file by username."""
    filepath = get_user_filepath(username)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            user_data = json.load(f)
        return user_data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading user {username}: {e}")
        return None

def get_all_users():
    """Loads all user data from the user data directory."""
    users = []
    if not os.path.exists(USER_DATA_DIR):
        return users
        
    try:
        for filename in os.listdir(USER_DATA_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(USER_DATA_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        user_data = json.load(f)
                        users.append(user_data)
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error reading or parsing user file {filename}: {e}")
                    # Optionally, decide if one bad file should stop all, or just skip
    except OSError as e:
        print(f"Error listing user directory {USER_DATA_DIR}: {e}")
    return users

def delete_user_data(username):
    """Deletes a user's JSON data file."""
    filepath = get_user_filepath(username)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False # File didn't exist
    except OSError as e:
        print(f"Error deleting user file {username}.json: {e}")
        return False

# --- Note Data Functions ---
def get_note_filepath(note_id):
    """Returns the filepath for a given note_id's JSON data file."""
    return os.path.join(NOTE_DATA_DIR, f"{note_id}.json")

def generate_note_id():
    """Generates a unique note ID."""
    return uuid.uuid4().hex

def save_note(note_data):
    """
    Saves note data to a JSON file. note_data should be a dictionary.
    Handles 'created_at' and 'updated_at' timestamps.
    """
    if 'id' not in note_data:
        raise ValueError("Note data must contain an 'id' field.")

    filepath = get_note_filepath(note_data['id'])
    now_iso = datetime.utcnow().isoformat()

    if not os.path.exists(filepath): # New note
        note_data['created_at'] = now_iso
    
    note_data['updated_at'] = now_iso # Always update 'updated_at'

    try:
        with open(filepath, 'w') as f:
            json.dump(note_data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving note {note_data['id']}: {e}")
        return False

def get_note(note_id):
    """Loads note data from a JSON file by note_id."""
    filepath = get_note_filepath(note_id)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            note_data = json.load(f)
        return note_data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading note {note_id}: {e}")
        return None

def get_all_notes():
    """Loads all note data from the note data directory."""
    notes = []
    if not os.path.exists(NOTE_DATA_DIR):
        return notes
        
    try:
        for filename in os.listdir(NOTE_DATA_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(NOTE_DATA_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        note_data = json.load(f)
                        notes.append(note_data)
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error reading or parsing note file {filename}: {e}")
    except OSError as e:
        print(f"Error listing note directory {NOTE_DATA_DIR}: {e}")
    return notes

def delete_note_data(note_id):
    """Deletes a note's JSON data file."""
    filepath = get_note_filepath(note_id)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False # File didn't exist
    except OSError as e:
        print(f"Error deleting note file {note_id}.json: {e}")
        return False

def get_notes_by_user(username):
    """Retrieves all notes for a given username."""
    all_notes = get_all_notes()
    user_notes = [note for note in all_notes if note.get('user_id') == username]
    return user_notes

def get_notes_by_tag(tag_name):
    """Retrieves all notes containing a specific tag."""
    all_notes = get_all_notes()
    tagged_notes = [
        note for note in all_notes 
        if tag_name in note.get('tags', []) # Ensure 'tags' key exists and is a list
    ]
    return tagged_notes

# Example of how to call init_data_store() when the app starts:
# This would typically be done in your main app.py
# if __name__ == '__main__': # Or in app factory
#     init_data_store()
#     print("Data store initialized.")
#
#     # Example Usage (for testing this file directly)
#     # test_user = {"username": "johndoe", "name": "John Doe", "email": "john@example.com"}
#     # save_user(test_user)
#     # loaded_user = get_user("johndoe")
#     # print("Loaded User:", loaded_user)
#
#     # test_note_id = generate_note_id()
#     # test_note = {
#     #     "id": test_note_id,
#     #     "user_id": "johndoe",
#     #     "title": "My First Note",
#     #     "content": "This is a test note.",
#     #     "tags": ["test", "first"]
#     # }
#     # save_note(test_note)
#     # loaded_note = get_note(test_note_id)
#     # print("Loaded Note:", loaded_note)
#
#     # print("All Users:", get_all_users())
#     # print("All Notes:", get_all_notes())
#     # print("John's notes:", get_notes_by_user("johndoe"))
#     # print("Notes tagged 'test':", get_notes_by_tag("test"))
#
#     # delete_note_data(test_note_id)
#     # delete_user_data("johndoe")
#     # print("Deleted user and note. Check data directory.")
#
#     # # Clean up data directory for testing
#     # import shutil
#     # if os.path.exists(DATA_DIR):
#     #     shutil.rmtree(DATA_DIR)
#     # print("Data directory cleaned up.")
