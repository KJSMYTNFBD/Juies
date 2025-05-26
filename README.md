# Notion-Like Note-Taking System

A web-based note-taking application built with Python and Flask, inspired by Notion.

## Features Implemented

*   **User Authentication:**
    *   User registration (name, username, password, bio, preferred web color for profile).
    *   Login and Logout.
    *   Session management.
*   **Note Management:**
    *   Create, edit, and delete notes.
    *   Notes include a title and content.
*   **Tagging System:**
    *   Add comma-separated tags to notes.
    *   View all notes associated with a specific tag.
    *   Tags are displayed on notes.
*   **User Profiles & Public Viewing:**
    *   Public user profiles displaying name, bio, and personal notes.
    *   User profiles are styled with the user's chosen web color.
    *   A page listing all registered users.
    *   Publicly viewable notes and tag pages (edit/delete restricted to authors).

## Technologies Used

*   Python
*   Flask
*   Flask-SQLAlchemy (for database interaction with SQLite)
*   Flask-Login (for user session management)
*   Flask-WTF (for forms)
*   HTML/CSS

## Setup and Running the Application

1.  **Clone the repository (if applicable).**
2.  **Ensure Python 3 is installed.**
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install dependencies:**
    *   Create a `requirements.txt` file with the following content:
        ```
        Flask>=2.0
        Flask-SQLAlchemy>=2.5
        Flask-Login>=0.5
        Flask-WTF>=1.0
        Werkzeug>=2.0 
        SQLAlchemy>=1.4 
        WTForms>=3.0
        ```
    *   Install them:
        ```bash
        pip install -r requirements.txt
        ```
5.  **Run the application:**
    ```bash
    flask run
    ```
    (The application should create the `instance/notes_app.db` SQLite database file automatically on first run if it doesn't exist, based on the current `app.py` setup.)

6.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000/`.
