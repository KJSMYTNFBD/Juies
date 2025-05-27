# Notion-Like Note-Taking System

A web-based note-taking application built with Python and Flask, inspired by Notion. This version stores all user and note data in local JSON files.

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
*   **Data Storage:**
    *   User and note data are stored in JSON files in the local file system (`data/users/` and `data/notes/`).

## Technologies Used

*   Python
*   Flask
*   Flask-Login (for user session management)
*   Flask-WTF (for forms)
*   JSON (for data storage)
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
    *   The `requirements.txt` file should contain:
        ```
        Flask>=2.0
        Flask-Login>=0.5
        Flask-WTF>=1.0
        Werkzeug>=2.0
        WTForms>=3.0
        pytest>=6.0
        ```
    *   Install them:
        ```bash
        pip install -r requirements.txt
        ```
5.  **Run the application:**
    ```bash
    flask run
    ```
6.  **Data Storage:**
    The application uses a local file system for data storage. Upon first run (or if the directory doesn't exist), a `data/` directory will be created in the project root by the `json_store.py` module. This directory will contain `users/` and `notes/` subdirectories where user profiles and notes are stored as individual JSON files.

7.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000/`.
