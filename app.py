from Flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # This will show the homepage

if __name__ == '__main__':
    app.run(debug=True)