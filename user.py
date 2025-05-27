from flask_login import UserMixin
import json_store # Our new module for JSON-based data storage

class JsonUser(UserMixin):
    """
    User class for interacting with user data stored in JSON files.
    Inherits from UserMixin for Flask-Login compatibility.
    """
    def __init__(self, username, name=None, bio=None, web_color=None, password_hash=None, note_ids=None):
        """
        Initializes a JsonUser instance.
        
        Args:
            username (str): The user's unique username.
            name (str, optional): The user's display name.
            bio (str, optional): A short biography of the user.
            web_color (str, optional): Preferred web color for profile styling.
            password_hash (str, optional): The hashed password.
            note_ids (list, optional): A list of note IDs associated with the user.
        """
        self.username = username
        self.name = name
        self.bio = bio
        self.web_color = web_color
        self.password_hash = password_hash
        self.note_ids = note_ids if note_ids is not None else []

    def get_id(self):
        """
        Required by Flask-Login. Returns a unique ID for the user as a string.
        In this case, the username is used as the unique ID.
        """
        return self.username

    @staticmethod
    def get(username):
        """
        Retrieves a user by their username from the JSON store.
        This method is typically used by Flask-Login's user_loader.
        
        Args:
            username (str): The username of the user to retrieve.
            
        Returns:
            JsonUser: An instance of JsonUser if the user is found.
            None: If no user is found with the given username.
        """
        user_data = json_store.get_user(username)
        if user_data:
            return JsonUser(
                username=user_data['username'],
                name=user_data.get('name'),
                bio=user_data.get('bio'),
                web_color=user_data.get('web_color'),
                password_hash=user_data.get('password_hash'),
                note_ids=user_data.get('note_ids', []) # Ensure note_ids defaults to empty list
            )
        return None

    # Note: The `is_active`, `is_authenticated`, `is_anonymous` properties
    # are provided by UserMixin.
    # For `is_active`, UserMixin defaults to True. This can be overridden if needed.
    # For `is_authenticated`, UserMixin defaults to True after successful login.
    # For `is_anonymous`, UserMixin defaults to False for logged-in users.

    # Example of how to represent the user as a dictionary for saving
    def to_dict(self):
        """
        Returns a dictionary representation of the user, suitable for JSON storage.
        """
        return {
            'username': self.username,
            'name': self.name,
            'bio': self.bio,
            'web_color': self.web_color,
            'password_hash': self.password_hash,
            'note_ids': self.note_ids
        }

    def __repr__(self):
        return f"<JsonUser {self.username}>"
