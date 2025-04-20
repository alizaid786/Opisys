from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

# In-memory data structure to simulate user data
users = {'admin': {'password': 'admin123'}}

# Setup for file upload and storage
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# Home page with file upload
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('process_data', filename=file.filename))
    return render_template('index.html')

# Process data based on user selection
@app.route("/process/<filename>", methods=["GET", "POST"])
@login_required
def process_data(filename):
    df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Handle user filter options
    if request.method == "POST":
        date_range = request.form.get("date_range")
        report_type = request.form.get("report_type")
        # Logic to filter and generate reports based on selections
        filtered_data = df  # Apply your filters here based on user input

        # Generate report logic based on the selected report type
        if report_type == "sales":
            report_data = filtered_data.groupby('Sales').sum()
        elif report_type == "marketing":
            report_data = filtered_data.groupby('Marketing').sum()
        # You can add more report types like leads, inventory, etc.

        # Save the filtered report to a new Excel file
        output_file = f'reports/{report_type}_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        report_data.to_excel(output_file)

        return send_file(output_file, as_attachment=True)

    return render_template('process.html', filename=filename, df=df)

# User login route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

# User logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)