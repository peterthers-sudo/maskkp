from flask import Flask, render_template, jsonify, request, session
import json, os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("QUIZ_SECRET_KEY", "hemmeligt")

# ---------- Indlæs spørgsmål ----------
QUESTIONS_PATH = Path(__file__).parent / "questions.json"
with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

LEVELS = {q["level"]: q for q in QUESTIONS}
MAX_LEVEL = max(LEVELS.keys())
SAFE_LEVELS = {5}  # trin hvor man “redder” sit niveau

# ---------- Hjælpefunktioner ----------
def init_state():
    session.setdefault("level", 1)
    session.setdefault("safe_level", 0)
    session.setdefault("finished", False)
    session.setdefault("stopped", False)

def current_question():
    lvl = session.get("level", 1)
    return LEVELS.get(lvl)

# ---------- Routes ----------
@app.route("/")
def index():
    init_state()
    return render_template("index.html")

@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    init_state()
    return jsonify({"ok": True})

@app.route("/state")
def state():
    """Returnerer aktuel quizstatus og spørgsmål."""
    init_state()
    q = current_question() or {}
    return jsonify({
        "level": session["level"],
        "safe_level": session["safe_level"],
        "finished": session["finished"],
        "stopped": session["stopped"],
        "max_level": MAX_LEVEL,
        "question": {
            "edu": q.get("edu"),
            "cutoff": q.get("cutoff"),
            "question": q.get("question"),
            "options": q.get("options"),
            "correct": q.get("correct")
        }
    })

@app.route("/answer", methods=["POST"])
def answer():
    """Modtager svar og afgør om det er korrekt."""
    init_state()
    data = request.get_json(silent=True) or {}
    selected = data.get("answer")
    q = current_question() or {}

    correct = (selected == q.get("correct"))
    if correct:
        # Opdater sikre trin
        if q.get("level") in SAFE_LEVELS and session["safe_level"] < q["level"]:
            session["safe_level"] = q["level"]
        # Gå videre til næste spørgsmål
        session["level"] = q["level"] + 1
        if session["level"] > MAX_LEVEL:
            session["finished"] = True
            return jsonify({
                "result": "correct",
                "finished": True,
                "message": "Du er nu Oversygeplejerske! 👑"
            })
        next_q = LEVELS[session["level"]]
        return jsonify({
            "result": "correct",
            "finished": False,
            "message": f"Du er nu {q['edu']}!",
            "next_edu": next_q["edu"]
        })
    else:
        # Forkert svar → tilbage til sikkert niveau
        back_to = session.get("safe_level", 0) or 1
        session["level"] = back_to
        return jsonify({
            "result": "wrong",
            "finished": False,
            "message": f"Dumpet! Du ryger tilbage til {LEVELS[back_to]['edu']}."
        })

@app.route("/stay", methods=["POST"])
def stay():
    """Bruger vælger at stoppe ved sit nuværende niveau."""
    q = LEVELS.get(session.get("level", 1) - 1, LEVELS[1])
    session["stopped"] = True
    return jsonify({"ok": True, "message": f"Du vælger at blive som {q['edu']}. 🎓"})

# ---------- Start ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
