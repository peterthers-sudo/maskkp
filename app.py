from flask import Flask, render_template, jsonify, request, session
import json, os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("QUIZ_SECRET_KEY", "hemmeligt")

QUESTIONS_PATH = Path(__file__).parent / "questions.json"
with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

LEVELS = {q["level"]: q for q in QUESTIONS}
MAX_LEVEL = max(LEVELS.keys())
SAFE_LEVELS = {5}

def init_state():
    session.setdefault("level", 1)
    session.setdefault("safe_level", 0)
    session.setdefault("finished", False)
    session.setdefault("stopped", False)

def current_question():
    lvl = session.get("level", 1)
    return LEVELS.get(lvl)

@app.route('/')
def index():
    init_state()
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    init_state()
    return jsonify({'ok': True})

@app.route('/state')
def state():
    init_state()
    q = current_question()
    return jsonify({
        'level': session['level'],
        'safe_level': session['safe_level'],
        'finished': session['finished'],
        'stopped': session['stopped'],
        'max_level': MAX_LEVEL,
        'question': q
    })

@app.route('/answer', methods=['POST'])
def answer():
    init_state()
    data = request.get_json(silent=True) or {}
    selected = data.get('answer')
    q = current_question()
    correct = (selected == q['correct'])
    if correct:
        if q['level'] in SAFE_LEVELS and session['safe_level'] < q['level']:
            session['safe_level'] = q['level']
        session['level'] = q['level'] + 1
        if session['level'] > MAX_LEVEL:
            session['finished'] = True
            return jsonify({'result': 'correct', 'finished': True, 'message': 'Du er nu optaget på Konservator!'})
        next_q = LEVELS[session['level']]
        return jsonify({'result': 'correct', 'finished': False, 'message': f'Du er nu optaget på {q["edu"]}!', 'next_edu': next_q["edu"]})
    else:
        back_to = session.get('safe_level', 0) or 1
        session['level'] = back_to
        return jsonify({'result': 'wrong', 'finished': False, 'message': f'Afslag! Du ryger tilbage til {LEVELS[back_to]["edu"]}.'})

@app.route('/stay', methods=['POST'])
def stay():
    q = LEVELS.get(session.get('level', 1)-1, LEVELS[1])
    session['stopped'] = True
    return jsonify({'ok': True, 'message': f'Du vælger at blive på {q["edu"]}. 🎓'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
