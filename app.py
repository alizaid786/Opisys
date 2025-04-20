from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import sqlite3
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# ================= User Class ====================
class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username

    @staticmethod
    def get_user_by_username(username):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user:
            return User(user[0], user[1])
        return None

    @staticmethod
    def get_user_by_id(user_id):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        if user:
            return User(user[0], user[1])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(user_id)

# ================ DB Setup ======================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            report_type TEXT,
            date_created TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Call once to create a test user
def create_test_user():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
    except sqlite3.IntegrityError:
        pass  # user already exists
    conn.commit()
    conn.close()

init_db()
create_test_user()

# =============== Routes =====================

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            user_obj = User(user[0], user[1])
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        session['uploaded_file'] = filepath
        flash('File uploaded successfully!')
    return redirect(url_for('index'))

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')

    filepath = session.get('uploaded_file')
    if not filepath or not os.path.exists(filepath):
        flash("No file uploaded.")
        return redirect(url_for('index'))

    # Dummy report generation using pandas
    df = pd.read_excel(filepath)
    report = df.head(10)  # Placeholder

    report_filename = f"{current_user.username}_{report_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    report_path = os.path.join(REPORT_FOLDER, report_filename)
    report.to_excel(report_path, index=False)

    # Save to history
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, file_name, report_type, date_created) VALUES (?, ?, ?, ?)",
              (current_user.id, report_filename, report_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    flash("Report generated successfully!")
    return send_file(report_path, as_attachment=True)

@app.route('/history')
@login_required
def history():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT file_name, report_type, date_created FROM history WHERE user_id = ?", (current_user.id,))
    history_data = c.fetchall()
    conn.close()
    return render_template('history.html', history=history_data)

# ================ Run App ======================
if __name__ == '__main__':
    app.run(debug=True)
