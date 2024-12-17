from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Google Apps Script URL
GSHEET_URL = "https://script.google.com/macros/s/AKfycbx6u6n8NuxFE4hylm5LAWDr35qGm_Txe0qK-XApv8PXwA_eMlOm6wiq22yJxuNa5oE/exec"

# Function to send POST requests to the Google Apps Script API
def send_post_request(action, params):
    data = {
        'action': action,
        **params
    }
    response = requests.post(GSHEET_URL, json=data)
    if action == 'get_projects':
        return response.json()
    return response.json()

@app.route('/')
def index():
    # Redirect to login/signup page if not logged in
    if 'username' not in session:
        return render_template('index.html', logged_in=False)
    return redirect(url_for('main_page'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    params = {
        'email': email,
        'password': password
    }
    result = send_post_request('login', params)
    if 'Login successful!' in result['result']:
        session['username'] = email  # Store email in session
        return redirect(url_for('main_page'))
    return jsonify(result)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    params = {
        'username': username,
        'email': email,
        'password': password
    }
    result = send_post_request('signup', params)
    if 'Signup successful!' in result['result']:
        session['username'] = email  # Store email in session
        return redirect(url_for('main_page'))
    return jsonify(result)

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    params = {
        'username': username
    }
    projects = send_post_request('get_projects', params).get('projects', [])
    
    if request.method == 'POST':
        title = request.form['title']
        note = request.form['note']
        # color = request.form.get('color', 'blue')  # Default to blue if not provided
        params = {
            'username': username,
            'title': title,
            'note': note,
        }
        result = send_post_request('addProject', params)
        return redirect(url_for('main_page'))

    return render_template('main.html', username=username, projects=projects)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()

