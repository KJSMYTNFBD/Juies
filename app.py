import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Import db object and models from models.py
from models import db, User, Note, Tag
from forms import RegistrationForm, LoginForm, NoteForm # Import the NoteForm

# Create instance folder if it doesn't exist
instance_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_folder_path):
    os.makedirs(instance_folder_path)

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'dev_secret_key' # Replace with a real secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/notes_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # The name of the route for the login page

@login_manager.user_loader
def load_user(user_id):
    """User loader function for Flask-Login."""
    return User.query.get(int(user_id))

# Create database tables if they don't exist
# This is a common way to do it, but for larger apps, Flask-Migrate is recommended.
db_file_path = os.path.join(instance_folder_path, 'notes_app.db')
if not os.path.exists(db_file_path):
    with app.app_context():
        db.create_all()
    print(f"Database created at {db_file_path}")
else:
    print(f"Database already exists at {db_file_path}")


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login')) # Or render a landing page


@app.route('/dashboard')
@login_required
def dashboard():
    user_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    return render_template('dashboard.html', title='Dashboard', notes=user_notes)


@app.route('/create_note', methods=['GET', 'POST'])
@login_required
def create_note():
    form = NoteForm()
    if form.validate_on_submit():
        new_note = Note(title=form.title.data, content=form.content.data, author=current_user)
        
        # Process tags
        new_note.tags.clear() # Good practice, though less critical for new notes
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag) # Add new tag to session
                new_note.tags.append(tag)
        
        db.session.add(new_note)
        db.session.commit()
        flash('Your note has been created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_note.html', title='Create Note', form=form)


@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    form = NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        
        # Process tags
        note.tags.clear()
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag) # Add new tag to session
                note.tags.append(tag)
        
        note.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Your note has been updated!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
        form.tags.data = ", ".join([tag.name for tag in note.tags])
    return render_template('edit_note.html', title='Edit Note', form=form, note=note)


@app.route('/note/<int:note_id>')
# @login_required # Removed for public viewing
def view_note(note_id):
    note = Note.query.get_or_404(note_id)
    return render_template('view_note.html', title=note.title, note=note)


@app.route('/tag/<string:tag_name>')
# @login_required # Removed for public viewing
def notes_by_tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    # For more complex scenarios, you might filter notes by current_user.id as well if tags are user-specific
    # or if notes are private even if tagged.
    # The current setup implies tags are global and notes are shown if they have that global tag.
    # If notes are strictly private, then we'd need:
    # notes = Note.query.with_parent(current_user).filter(Note.tags.any(name=tag.name)).order_by(Note.updated_at.desc()).all()
    notes = tag.notes.order_by(Note.updated_at.desc()).all() # Simpler if relationships are set
    return render_template('notes_by_tag.html', notes=notes, tag_name=tag.name, title="Notes tagged with '" + tag.name + "'")


@app.route('/user/<string:username>')
def user_profile(username):
    profile_user = User.query.filter_by(username=username).first_or_404()
    user_notes = Note.query.filter_by(author=profile_user).order_by(Note.updated_at.desc()).all()
    return render_template('user_profile.html', profile_user=profile_user, notes=user_notes, title=f"Profile of {profile_user.username}")


@app.route('/users')
def users_list():
    all_users = User.query.order_by(User.username).all()
    return render_template('users_list.html', users=all_users, title="All Users")


@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    flash('Your note has been deleted!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            username=form.username.data,
            password_hash=hashed_password,
            bio=form.bio.data,
            web_color=form.web_color.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login')) # Changed redirect to login page
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) # Redirect if already logged in
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            # Redirect to next_page if it exists, otherwise to dashboard
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Ensure the app context is available for operations like db.create_all() if run directly
    # and not already handled by the check above.
    # However, the above check is more robust for initial creation.
    app.run(debug=True)
