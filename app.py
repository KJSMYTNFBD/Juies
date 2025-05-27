import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm, NoteForm, SettingsForm
import json_store 
from user import JsonUser 

instance_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_folder_path):
    os.makedirs(instance_folder_path)

app = Flask(__name__)
json_store.init_data_store() 

app.config['SECRET_KEY'] = 'dev_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id): 
    return JsonUser.get(user_id)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    notes_data = json_store.get_notes_by_user(current_user.username)
    notes_data.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    return render_template('dashboard.html', title='Dashboard', notes=notes_data)

@app.route('/create_note', methods=['GET', 'POST'])
@login_required
def create_note():
    form = NoteForm()
    if form.validate_on_submit():
        note_id = json_store.generate_note_id()
        tags = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        
        note_data = {
            "id": note_id,
            "user_id": current_user.username,
            "title": form.title.data,
            "content": form.content.data,
            "tags": tags,
            # "created_at" and "updated_at" are handled by json_store.save_note
        }
        
        if json_store.save_note(note_data):
            user_data = json_store.get_user(current_user.username)
            if user_data:
                if 'note_ids' not in user_data or not isinstance(user_data['note_ids'], list):
                    user_data['note_ids'] = []
                user_data['note_ids'].append(note_id)
                json_store.save_user(user_data)
            
            flash('Your note has been created!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('An error occurred while saving your note.', 'danger')
            
    return render_template('create_note.html', title='Create Note', form=form)

@app.route('/note/<string:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note_data = json_store.get_note(note_id)
    if not note_data:
        abort(404)
    if note_data.get('user_id') != current_user.username:
        abort(403)
    
    form = NoteForm()
    if form.validate_on_submit():
        note_data['title'] = form.title.data
        note_data['content'] = form.content.data
        note_data['tags'] = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        # "updated_at" is handled by json_store.save_note
        
        if json_store.save_note(note_data):
            flash('Your note has been updated!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('An error occurred while updating your note.', 'danger')

    elif request.method == 'GET':
        form.title.data = note_data.get('title')
        form.content.data = note_data.get('content')
        form.tags.data = ", ".join(note_data.get('tags', []))
        
    return render_template('edit_note.html', title='Edit Note', form=form, note=note_data)

@app.route('/note/<string:note_id>')
def view_note(note_id):
    note_data = json_store.get_note(note_id)
    if not note_data:
        abort(404)
    
    author_data = json_store.get_user(note_data.get('user_id'))
    
    return render_template('view_note.html', title=note_data.get('title'), note=note_data, author=author_data)

@app.route('/tag/<string:tag_name>')
def notes_by_tag(tag_name):
    notes_data = json_store.get_notes_by_tag(tag_name)
    enriched_notes = []
    for note_dict in notes_data:
        author_data = json_store.get_user(note_dict.get('user_id'))
        display_note = note_dict.copy() 
        display_note['author'] = author_data if author_data else {'username': 'Unknown'}
        enriched_notes.append(display_note)
    
    enriched_notes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    return render_template('notes_by_tag.html', notes=enriched_notes, tag_name=tag_name, title="Notes tagged with '" + tag_name + "'")

@app.route('/user/<string:username>')
def user_profile(username):
    profile_user_data = json_store.get_user(username)
    if not profile_user_data:
        abort(404)
    
    profile_user_obj = JsonUser( 
        username=profile_user_data['username'],
        name=profile_user_data.get('name'),
        bio=profile_user_data.get('bio'),
        web_color=profile_user_data.get('web_color')
    )
    
    notes_data = json_store.get_notes_by_user(username)
    notes_data.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    
    return render_template('user_profile.html', profile_user=profile_user_obj, notes=notes_data, title=f"Profile of {profile_user_obj.username}")

@app.route('/users')
def users_list():
    all_users_data = json_store.get_all_users()
    all_users = [
        JsonUser(
            username=ud['username'], 
            name=ud.get('name'), 
            bio=ud.get('bio'), 
            web_color=ud.get('web_color')
        ) for ud in all_users_data
    ]
    all_users.sort(key=lambda u: u.username.lower())
    return render_template('users_list.html', users=all_users, title="All Users")

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        user_data = json_store.get_user(current_user.get_id()) 
        if not user_data: 
            flash("Error: Could not find your user data.", "danger")
            return redirect(url_for('dashboard'))

        user_data['name'] = form.name.data
        user_data['bio'] = form.bio.data
        user_data['web_color'] = form.web_color.data
        
        password_updated_successfully = False
        if form.current_password.data and form.new_password.data:
            if check_password_hash(user_data.get('password_hash'), form.current_password.data):
                if form.new_password.data == form.confirm_new_password.data: 
                    user_data['password_hash'] = generate_password_hash(form.new_password.data)
                    password_updated_successfully = True
                    flash('Your password has been updated.', 'success')
                else: 
                    flash('New passwords do not match.', 'danger')
            else:
                flash('Incorrect current password. Password not updated.', 'danger')
        
        json_store.save_user(user_data)
        
        if not (form.current_password.data and form.new_password.data and not password_updated_successfully):
            if not (form.current_password.data and not password_updated_successfully):
                 flash('Your settings have been updated.', 'success')
        
        if password_updated_successfully:
            # current_user object in memory is not automatically updated by changing the store
            # Re-fetch to update current_user's in-memory state for the current request,
            # or rely on next request's load_user. For immediate reflection:
            updated_user_session_obj = JsonUser.get(current_user.username)
            if updated_user_session_obj :
                login_user(updated_user_session_obj, remember=current_user.is_remembered if hasattr(current_user, 'is_remembered') else False)


        return redirect(url_for('settings'))
    
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.bio.data = current_user.bio
        form.web_color.data = current_user.web_color
        
    return render_template('settings.html', title='User Settings', form=form)

@app.route('/note/<string:note_id>/delete', methods=['POST']) # Changed to string:note_id
@login_required
def delete_note(note_id):
    note_data = json_store.get_note(note_id)
    if not note_data:
        abort(404)
    if note_data.get('user_id') != current_user.username:
        abort(403)
    
    if json_store.delete_note_data(note_id):
        user_data = json_store.get_user(note_data['user_id'])
        if user_data and 'note_ids' in user_data and note_id in user_data['note_ids']:
            user_data['note_ids'].remove(note_id)
            json_store.save_user(user_data)
        flash('Your note has been deleted!', 'success')
    else:
        flash('An error occurred while deleting your note.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user_data = {
            "username": form.username.data,
            "name": form.name.data,
            "password_hash": hashed_password,
            "bio": form.bio.data,
            "web_color": form.web_color.data,
            "note_ids": [] 
        }
        
        if json_store.save_user(user_data):
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('An error occurred while creating your account. Please try again.', 'danger')
            
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user_data = json_store.get_user(form.username.data)
        
        if user_data and check_password_hash(user_data.get('password_hash'), form.password.data):
            user = JsonUser.get(user_data['username']) 
            if user: 
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else: 
                flash('An error occurred during login. User object could not be created.', 'danger')
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
