from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Process Management Simulator is Running!"

if __name__ == "__main__":
    app.run(debug=True)