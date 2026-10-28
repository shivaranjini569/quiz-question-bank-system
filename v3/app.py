
from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"

def load_questions():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

@app.route("/")
def index():
    return render_template(
        "index.html",
        questions=load_questions()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
