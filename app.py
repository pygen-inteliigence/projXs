from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import pandas as pd
from openai import OpenAI
import random

app = Flask(__name__)
app.secret_key = 'pygen-and-co-8113261-2024-projXs'

# Google Apps Script URL
GSHEET_URL = "https://script.google.com/macros/s/AKfycbykSer38aeWUFsyOfVkEv4ul7kJrz2DZhk85WX-GpkIuncRs53kaoiF1jpLuBYU2g/exec"

# OpenAI API Configuration
BASE_URLS = [
    'https://api-handler-ddc-free-api.hf.space/v2',
    'https://devsdocode-ddc-free-api.hf.space/v2',
    'https://free-ddc.xiolabs.xyz/v1'
]

client = OpenAI(
    base_url=random.choice(BASE_URLS),
    api_key="DDC-Free-For-Subscribers-YT-@DevsDoCode"
)

# Memory storage for chat history (per session)
chat_memory = {}

# Helper function for sending POST requests
def send_post_request(action, params):
    data = {'action': action, **params}
    response = requests.post(GSHEET_URL, json=data)
    return response.json()

# Chat route with persistent memory
@app.route('/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_message = request.json['message']
    username = session['username']

    # Initialize user chat history if not present in memory
    if username not in chat_memory:
        chat_memory[username] = [
            {"role": "system", "content": f"You are ProjXs AI, a helpful assistant for {username}. "
                                              f"You were developed by Ameer Hamza Khan, Founder and CEO of PyGen & Co. "
                                              "Always respond as though you personally know and are assisting {username} with their goals. "
                                              "Personalize every response using their name."}
        ]

    # Append user message to chat history
    chat_memory[username].append({"role": "user", "content": user_message})

    try:
        # Send chat history to OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_memory[username],
            temperature=0.7,
            max_tokens=1000
        )

        # Get AI's response and append to chat history
        ai_response = completion.choices[0].message.content
        chat_memory[username].append({"role": "assistant", "content": ai_response})

        return jsonify({'response': ai_response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Logout route to clear session and user chat memory
@app.route('/logout')
def logout():
    username = session.pop('username', None)
    if username and username in chat_memory:
        del chat_memory[username]  # Clear user's chat history from memory
    return redirect(url_for('index'))

# Other existing routes remain unchanged
@app.route('/')
def index():
    if 'username' not in session:
        return render_template('login.html', logged_in=False, terms_url=url_for('terms'), doc_url=url_for('documentation'))
    return redirect(url_for('main_page'))


@app.route('/terms')
def terms():
    return render_template('terms.html')  # Ensure 'terms.html' exists


@app.route('/documentation')
def documentation():
    return render_template('doc-projxs.html')  # Ensure 'doc-projxs.html' exists


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    params = {'email': email, 'password': password}
    result = send_post_request('login', params)

    if 'Login successful!' in result['result']:
        session['username'] = email
        return redirect(url_for('main_page'))

    return jsonify(result)


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    params = {'username': username, 'email': email, 'password': password}
    result = send_post_request('signup', params)

    if 'Signup successful!' in result['result']:
        session['username'] = email
        return redirect(url_for('main_page'))

    return jsonify(result)


@app.route('/main', methods=['GET', 'POST'])
def main_page():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    params = {'username': username}
    projects = send_post_request('get_projects', params).get('projects', [])

    if request.method == 'POST':
        title = request.form['title']
        note = request.form['note']
        params = {'username': username, 'title': title, 'note': note}
        result = send_post_request('addProject', params)
        return jsonify({"success": True})

    user_activity = get_user_activity()
    user_data = user_activity[user_activity["Username"] == username]
    if not user_data.empty:
        user_status = user_data["ActivityLevel"].values[0]
        total_notes = user_data["TotalNotes"].values[0]
    else:
        user_status = "Getting Started"
        total_notes = 0

    motivational_message = get_motivational_message(user_status, total_notes)

    return render_template(
        'main.html',
        username=username,
        projects=projects,
        user_status=user_status,
        motivational_message=motivational_message,
        terms_url=url_for('terms'),
        doc_url=url_for('documentation')
    )


def get_user_activity():
    response = requests.get(GSHEET_URL)
    data = response.json()["data"]
    df = pd.DataFrame(data)
    df = df[df["Title"] != ""]
    user_activity = df.groupby("Username").size().reset_index(name="TotalNotes")

    def activity_label(note_count):
        if note_count > 10:
            return "Most Active"
        elif 5 <= note_count <= 10:
            return "Moderately Active"
        else:
            return "Getting Started"

    user_activity["ActivityLevel"] = user_activity["TotalNotes"].apply(activity_label)
    return user_activity


def get_motivational_message(user_status, total_notes):
    messages = {
        "Most Active": f"Fantastic job! You're a leader on the Productivity Champion leaderboard with {total_notes} notes! 🏆",
        "Moderately Active": f"You're doing great! Keep it up to reach the top ranks. You've added {total_notes} notes so far. 🚀",
        "Getting Started": f"Don't miss out! Start adding notes to unlock your full potential. You have {total_notes} notes. 💪",
    }
    return messages.get(user_status, "Keep going!")

if __name__ == "__main__":
    app.run()
