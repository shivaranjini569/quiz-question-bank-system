
from flask import Flask, render_template, request, redirect
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"

def load_questions():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def save_questions(questions):
    DATA_FILE.write_text(
        json.dumps(questions, indent=2),
        encoding="utf-8"
    )

@app.route("/")
def index():
    return render_template("index.html", questions=load_questions())

@app.route("/edit/<int:question_id>", methods=["POST"])
def edit_question(question_id):
    questions = load_questions()
    for item in questions:
        if item["id"] == question_id:
            item["question"] = request.form.get("question", "").strip()
            item["answer"] = request.form.get("answer", "").strip()
            break
    save_questions(questions)
    return redirect("/")

@app.route("/delete/<int:question_id>", methods=["POST"])
def delete_question(question_id):
    questions = [
        item for item in load_questions()
        if item["id"] != question_id
    ]
    save_questions(questions)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
