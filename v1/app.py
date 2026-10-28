
from flask import Flask, render_template, request, redirect
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "questions.json"

def load_questions():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()

        if question and answer:
            questions = load_questions()
            questions.append({
                "id": len(questions) + 1,
                "question": question,
                "answer": answer
            })
            DATA_FILE.write_text(
                json.dumps(questions, indent=2),
                encoding="utf-8"
            )
        return redirect("/")

    return render_template(
        "index.html",
        questions=load_questions()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
