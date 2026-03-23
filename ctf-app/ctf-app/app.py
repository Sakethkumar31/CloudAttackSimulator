import os

import requests
from flask import Flask, jsonify, redirect, render_template_string, request, session

app = Flask(__name__)
app.secret_key = os.getenv("CTF_SECRET_KEY", "ctf_secret_key")

FLAG = os.getenv("CTF_FLAG", "ctf{hi}")
POINTS = 100
scores = {}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
ANSWER_REQUEST_HINTS = (
    "answer",
    "final answer",
    "exact answer",
    "just tell me",
    "give me answer",
    "provide answer",
    "what is the answer",
    "solve it for me",
)

BASE_STYLE = """
<style>
:root {
    --bg-main: #070c16;
    --panel-bg: #101a2b;
    --border-soft: #294465;
    --accent: #6ef2c5;
    --muted: #9ec3e2;
    --text-main: #e6f4ff;
    --ok: #63f0a2;
    --bad: #ff8e8e;
}
body {
    margin: 0;
    font-family: Consolas, monospace;
    background: radial-gradient(circle at 20% 0%, #173056, #070c16 48%);
    color: var(--text-main);
    min-height: 100vh;
}
.wrap { max-width: 720px; margin: 24px auto; padding: 16px; }
.card { background: var(--panel-bg); border: 1px solid var(--border-soft); border-radius: 10px; padding: 18px; }
h2 { margin: 0 0 14px; color: var(--accent); }
p { color: var(--muted); font-size: 14px; line-height: 1.5; }
input {
    width: 100%;
    padding: 10px;
    margin-top: 10px;
    border: 1px solid var(--border-soft);
    background: #0a1220;
    color: var(--text-main);
}
button {
    width: 100%;
    padding: 10px;
    margin-top: 10px;
    border: 1px solid #3d6ea0;
    background: #143055;
    color: var(--text-main);
    cursor: pointer;
}
a { color: #8fe7ff; }
.ok { color: var(--ok); }
.bad { color: var(--bad); }
.chat {
    margin-top: 14px;
    border: 1px solid var(--border-soft);
    background: #0a1220;
    padding: 10px;
}
.chatlog {
    height: 150px;
    overflow: auto;
    white-space: pre-line;
    border: 1px solid #27405e;
    padding: 8px;
    font-size: 12px;
    margin-bottom: 8px;
}
.chatrow { display: flex; gap: 6px; }
.chatrow input { margin-top: 0; flex: 1; }
.chatrow button { margin-top: 0; width: auto; }
.chat select { width: 100%; padding: 8px; margin: 8px 0; background: #0a1220; color: var(--text-main); border: 1px solid var(--border-soft); }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { border-bottom: 1px solid #223650; padding: 8px; text-align: left; }
</style>
"""

LOGIN_PAGE = BASE_STYLE + """
<div class="wrap"><div class="card">
<h2>Cloud Attack Path Simulator - CTF Access Terminal</h2>
<p>Hands-on challenge space for attack understanding and mitigation practice.</p>
<form method="post">
  <input name="username" placeholder="Enter codename" required>
  <button type="submit">Login</button>
</form>
</div></div>
"""

CHALLENGE_PAGE = BASE_STYLE + """
<div class="wrap"><div class="card">
<h2>Cloud Attack Path Simulator - CTF Module</h2>
<p>Welcome {{ user }}</p>
<p><b>Challenge:</b> A word we say when we meet someone. Submit in format <code>ctf{...}</code>.</p>

<form method="post" action="/submit">
  <input name="flag" placeholder="Enter flag">
  <button type="submit">Submit Flag</button>
</form>

{% if message %}<p class="{{ 'ok' if success else 'bad' }}">{{ message }}</p>{% endif %}
<p>Score: <b>{{ score }}</b></p>

<div class="chat">
  <b>CTF Tutor</b>
  <select id="ctfTutorMode">
    <option value="beginner">Tutor: Beginner</option>
    <option value="intermediate" selected>Tutor: Intermediate</option>
    <option value="expert">Tutor: Expert</option>
  </select>
  <div id="chatLog" class="chatlog">Tutor: Ask me to explain the topic step by step.</div>
  <div class="chatrow">
    <input id="chatInput" placeholder="Ask: explain this challenge from basics">
    <button type="button" onclick="sendChat()">Ask</button>
  </div>
</div>

<p style="margin-top:12px;"><a href="/scoreboard">View Scoreboard</a> | <a href="/logout">Logout</a></p>
</div></div>
<script>
async function sendChat(){
  const input = document.getElementById('chatInput');
  const log = document.getElementById('chatLog');
  const msg = (input.value || '').trim();
  if(!msg) return;
  log.textContent += "\nYou: " + msg;
  input.value = '';
  const res = await fetch('/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: msg})
  });
  const data = await res.json();
  log.textContent += "\nTutor: " + (data.reply || 'No response');
  log.scrollTop = log.scrollHeight;
}
async function loadTutorMode(){
  const res = await fetch('/mode');
  const data = await res.json();
  if(data.mode) document.getElementById('ctfTutorMode').value = data.mode;
}
async function saveTutorMode(){
  const mode = document.getElementById('ctfTutorMode').value;
  await fetch('/mode', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({mode})
  });
}
document.addEventListener('keydown', function(e){
  if(e.key==='Enter' && document.activeElement && document.activeElement.id==='chatInput') sendChat();
});
document.addEventListener('DOMContentLoaded', function(){
  loadTutorMode();
  const el = document.getElementById('ctfTutorMode');
  if (el) el.addEventListener('change', saveTutorMode);
});
</script>
"""

SCOREBOARD_PAGE = BASE_STYLE + """
<div class="wrap"><div class="card">
<h2>Scoreboard</h2>
<table>
<tr><th>Player</th><th>Score</th></tr>
{% for user, score in scores %}
<tr><td>{{ user }}</td><td>{{ score }}</td></tr>
{% endfor %}
</table>
<p><a href="/challenge">Back to Challenge</a></p>
</div></div>
"""


def _messages_to_gemini_payload(messages):
    system_parts = []
    contents = []

    for msg in messages:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": content}]})

    if system_parts:
        preamble = "System guidance:\n" + "\n\n".join(system_parts)
        if contents and contents[0]["role"] == "user":
            first_text = contents[0]["parts"][0].get("text", "")
            contents[0]["parts"][0]["text"] = f"{preamble}\n\n{first_text}".strip()
        else:
            contents.insert(0, {"role": "user", "parts": [{"text": preamble}]})

    if not contents:
        contents = [{"role": "user", "parts": [{"text": "Help with cybersecurity tutoring."}]}]

    return contents


def call_gemini(messages):
    if not GEMINI_API_KEY:
        return None
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "x-goog-api-client": "cloud-attack-lab/1.0",
                "Content-Type": "application/json",
            },
            json={
                "contents": _messages_to_gemini_payload(messages),
                "generationConfig": {
                    "temperature": 0.35,
                    "maxOutputTokens": 450,
                },
            },
            timeout=20,
        )
        r.raise_for_status()
        payload = r.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            return None
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
        reply = "".join(part.get("text", "") for part in parts if part.get("text")).strip()
        return reply or None
    except Exception:
        return None


def get_chat_history():
    return session.get("ctf_chat_history", [])


def set_chat_history(history):
    session["ctf_chat_history"] = history[-12:]


def fallback_tutor(msg):
    return (
        f"Question: {msg}\n\n"
        "Tutor Explanation:\n"
        "1) Understand the challenge format and intent.\n"
        "2) Identify which basic command/concept the task tests.\n"
        "3) Validate one hypothesis with a safe test.\n"
        "4) Compare result with expected pattern.\n"
        "5) Submit only after reasoned verification.\n\n"
        "Common mistake: guessing without verifying context."
    )


def get_tutor_mode():
    mode = (session.get("ctf_tutor_mode") or "intermediate").strip().lower()
    if mode not in {"beginner", "intermediate", "expert"}:
        return "intermediate"
    return mode


def mode_instruction(mode):
    if mode == "beginner":
        return (
            "Use very simple language, define each term, and include one concrete example. "
            "If the user explicitly asks for the final answer, provide it directly first, then explain why."
        )
    if mode == "expert":
        return "Use advanced technical depth, include tradeoffs and pitfalls."
    return "Use balanced depth with clear reasoning and practical steps."


def wants_direct_answer(text):
    msg = (text or "").strip().lower()
    if not msg:
        return False
    return any(token in msg for token in ANSWER_REQUEST_HINTS)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username'].strip()
        session['user'] = user
        scores.setdefault(user, 0)
        return redirect('/challenge')
    return LOGIN_PAGE


@app.route('/challenge')
def challenge():
    if 'user' not in session:
        return redirect('/')
    user = session['user']
    return render_template_string(
        CHALLENGE_PAGE,
        user=user,
        score=scores[user],
        message="",
        success=False,
    )


@app.route('/submit', methods=['POST'])
def submit():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    submitted_flag = (request.form.get('flag') or '').strip()

    if submitted_flag == FLAG:
        scores[user] = POINTS
        message = "Flag captured."
        success = True
    else:
        message = "Incorrect flag."
        success = False

    return render_template_string(
        CHALLENGE_PAGE,
        user=user,
        score=scores[user],
        message=message,
        success=success,
    )


@app.route('/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    msg = (data.get('message') or '').strip()
    mode = get_tutor_mode()

    if mode == "beginner" and wants_direct_answer(msg):
        return jsonify(
            {
                "reply": (
                    "Direct answer: `ctf{hi}`\n"
                    "Reason: the challenge says it is the greeting word in ctf{...} format."
                )
            }
        )

    history = get_chat_history()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a CTF tutor. Teach deeply like ChatGPT tutor mode. "
                "Explain basics, reasoning, examples, common mistakes, and next steps. "
                "Reveal final answer only when explicitly asked, or when tutor mode is beginner and user asks for answer."
            ),
        },
        {"role": "system", "content": "Current challenge context: format ctf{...}, beginner endpoint/security basics."},
        {"role": "system", "content": f"Tutor depth mode: {mode}. {mode_instruction(mode)}"},
    ]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": msg or "Teach me this challenge from basics."})

    reply = call_gemini(messages)
    if not reply:
        reply = fallback_tutor(msg or "Teach me this challenge")
    else:
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        set_chat_history(history)

    return jsonify({"reply": reply})


@app.route('/mode', methods=['GET', 'POST'])
def mode():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'GET':
        return jsonify({"mode": get_tutor_mode()})
    data = request.get_json(silent=True) or {}
    incoming = (data.get("mode") or "").strip().lower()
    if incoming not in {"beginner", "intermediate", "expert"}:
        incoming = "intermediate"
    session["ctf_tutor_mode"] = incoming
    return jsonify({"mode": incoming})


@app.route('/scoreboard')
def scoreboard():
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return render_template_string(SCOREBOARD_PAGE, scores=sorted_scores)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
