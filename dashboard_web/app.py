import os
import sys
import re
from collections import Counter

import requests
from flask import Flask, jsonify, redirect, render_template, render_template_string, request, session, url_for
from neo4j import GraphDatabase

# ---------------- PATH FIX ----------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "redops_secure_key")

# ---------------- NEO4J ----------------
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Saketh2004")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)

# ---------------- LOGIN ----------------
USERNAME = os.getenv("DASHBOARD_USER", "socadmin")
PASSWORD = os.getenv("DASHBOARD_PASS", "redops123")
ALLOW_MULTI_USER = os.getenv("ALLOW_MULTI_USER", "1").strip().lower() in {"1", "true", "yes", "on"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")

# ---------------- OPENAI ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
VALID_TUTOR_MODES = {"beginner", "intermediate", "expert"}

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

# ---------------- CTF (embedded in same app) ----------------
ctf_progress = {}

CTF_LEVELS = [
    {
        "level": 1,
        "name": "Easy",
        "question": "You suspect a compromised Linux host. Which command quickly confirms the current active user context?",
        "answer": "whoami",
        "hint": "Use the command that prints your current username.",
        "topic": "user-context validation on endpoints",
    },
    {
        "level": 2,
        "name": "Medium",
        "question": "During triage, you must identify which host generated a suspicious alert. Which command gives the host identity?",
        "answer": "hostname",
        "hint": "It returns the machine name.",
        "topic": "host attribution in incident response",
    },
    {
        "level": 3,
        "name": "Easy",
        "question": "To check if malware dropped files in the current folder, which command should you run first?",
        "answer": "ls",
        "hint": "Use the command that lists directory contents.",
        "topic": "artifact discovery fundamentals",
    },
    {
        "level": 4,
        "name": "Easy",
        "question": "Before collecting evidence, you must confirm your current investigation path. Which command helps?",
        "answer": "pwd",
        "hint": "This command prints the working directory.",
        "topic": "evidence path verification",
    },
    {
        "level": 5,
        "name": "Easy",
        "question": "An endpoint may be beaconing externally. Which command helps inspect interface/network configuration quickly?",
        "answer": "ifconfig",
        "hint": "Legacy but commonly known network interface command.",
        "topic": "network triage on compromised hosts",
    },
    {
        "level": 6,
        "name": "Medium",
        "question": "You need to inspect active sockets and listening ports to detect suspicious C2 activity. Which command is preferred?",
        "answer": "netstat",
        "hint": "check which ports are litening on machine to find the hidden service.",
        "topic": "connection visibility and detection",
    },
    {
        "level": 7,
        "name": "Medium",
        "question": "Map this behavior to MITRE: attacker uses shell/PowerShell commands to execute payloads. What technique ID fits best?",
        "answer": "t1059",
        "hint": "Command and scripting interpreter technique.",
        "topic": "behavior-to-mitre mapping",
    },
    {
        "level": 8,
        "name": "Medium",
        "question": "Attack spread is moving host-to-host internally. Which defensive strategy best limits east-west movement?",
        "answer": "network segmentation",
        "hint": "Split network zones and limit trust paths.",
        "topic": "lateral movement containment",
    },
    {
        "level": 9,
        "name": "Hard",
        "question": "You confirm active compromise with potential data theft. What is the first priority response action?",
        "answer": "isolate",
        "hint": "Immediate containment step.",
        "topic": "incident response decision priority",
    },
    {
        "level": 10,
        "name": "Hard",
        "question": "After containment and eradication, what action proves controls are effective and attacker activity is gone?",
        "answer": "verify",
        "hint": "Final validation/check stage of IR lifecycle.",
        "topic": "post-incident assurance and hardening",
    },
]

CTF_STYLE = """
<style>
body{margin:0;background:#070b12;color:#d6e9ff;font-family:Consolas,monospace;overflow-x:hidden}
.fx-grid{position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,247,176,.08) 1px, transparent 1px),linear-gradient(90deg, rgba(79,247,176,.08) 1px, transparent 1px);background-size:26px 26px;opacity:.25}
.fx-scan{position:fixed;inset:0;pointer-events:none;background:linear-gradient(180deg,transparent 0%,rgba(79,247,176,.09) 50%,transparent 100%);background-size:100% 6px;mix-blend-mode:screen;animation:scan 6s linear infinite}
@keyframes scan{from{transform:translateY(-12%)}to{transform:translateY(12%)}}
.wrap{max-width:780px;margin:26px auto;padding:16px;position:relative;z-index:2}
.card{background:rgba(12,20,34,.92);border:1px solid #2d4b73;padding:16px;border-radius:10px;box-shadow:0 0 22px rgba(88,170,255,.18)}
h2{margin-top:0;color:#4ff7b0;text-shadow:0 0 8px rgba(79,247,176,.45)}
input{width:100%;padding:10px;background:#08111f;color:#d6e9ff;border:1px solid #2a4260}
button{margin-top:10px;padding:10px;background:#102741;color:#d6e9ff;border:1px solid #2f5f95;cursor:pointer}
button:hover{box-shadow:0 0 14px rgba(79,247,176,.25)}
a{color:#7fe6ff}
small{color:#9ec7e6}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:8px;border-bottom:1px solid #223650;text-align:left}
.ok{color:#84f6b6}
.bad{color:#ff8a8a}
.ai{margin-top:12px;border:1px solid #2a4260;background:#08111f;padding:10px;white-space:pre-line}
.switcher{display:flex;justify-content:flex-end;margin-bottom:8px;gap:8px}
.switcher button{margin-top:0;padding:6px 8px;font-size:12px}
body.hacker-green .card{border-color:#2d6b4d;box-shadow:0 0 22px rgba(79,247,176,.22)}
body.hacker-green h2{color:#4ff7b0}
body.hacker-green .fx-grid{background-image:linear-gradient(rgba(79,247,176,.08) 1px, transparent 1px),linear-gradient(90deg, rgba(79,247,176,.08) 1px, transparent 1px)}
body.red-alert .card{border-color:#6b2d38;box-shadow:0 0 22px rgba(255,98,120,.23)}
body.red-alert h2{color:#ff7d92}
body.red-alert .fx-grid{background-image:linear-gradient(rgba(255,98,120,.08) 1px, transparent 1px),linear-gradient(90deg, rgba(255,98,120,.08) 1px, transparent 1px)}
body.red-alert button{background:#3a1120;border-color:#7f2944}
</style>
<script>
function applyTheme(theme){
  document.body.classList.remove('hacker-green','red-alert');
  document.body.classList.add(theme);
  localStorage.setItem('ctf_theme', theme);
}
function toggleTheme(){
  const cur = localStorage.getItem('ctf_theme') || 'hacker-green';
  applyTheme(cur === 'hacker-green' ? 'red-alert' : 'hacker-green');
}
document.addEventListener('DOMContentLoaded', function(){
  applyTheme(localStorage.getItem('ctf_theme') || 'hacker-green');
});
</script>
"""

CTF_CHALLENGE_PAGE = CTF_STYLE + """
<div class="fx-grid"></div><div class="fx-scan"></div>
<div class="wrap"><div class="card">
<div class="switcher"><button type="button" onclick="toggleTheme()">Switch Theme</button></div>
<h2>Cloud Attack Path Simulator - CTF Level {{ level.level }} ({{ level.name }})</h2>
<p>User: <b>{{ user }}</b></p>
<p><b>Task:</b> {{ level.question }}</p>
<small>Type your answer in simple words. Not case-sensitive.</small>
<p><b>Basic Operations:</b> Recon -> Detect -> Contain -> Recover</p>
<ul>
  <li><small><b>Recon:</b> understand attacker action and target.</small></li>
  <li><small><b>Detect:</b> identify suspicious behavior in logs.</small></li>
  <li><small><b>Contain:</b> isolate affected host/account quickly.</small></li>
  <li><small><b>Recover:</b> patch root cause and validate controls.</small></li>
</ul>
<form method="post" action="/ctf/submit">
  <input name="answer" placeholder="Enter answer">
  <button type="submit">Submit</button>
</form>
<form method="get" action="/ctf" style="margin-top:8px;">
  <input type="hidden" name="show_hint" value="1">
  <button type="submit">Show Hint</button>
</form>
<form method="post" action="/ctf/insight" style="margin-top:8px;">
  <button type="submit">Get AI Insight For This Level</button>
</form>
{% if show_hint %}<p><b>Hint:</b> {{ level.hint }}</p>{% endif %}
{% if message %}<p class="{{ 'ok' if success else 'bad' }}">{{ message }}</p>{% endif %}
<p>Score: <b>{{ score }}</b> | Attempts on this level: <b>{{ attempts }}</b></p>
{% if ai_text %}<div class="ai"><b>AI Insight:</b> {{ ai_text }}</div>{% endif %}
<div class="ai">
  <b>CTF Chatbot:</b>
  <div style="margin-top:8px;">
    <select id="ctfTutorMode">
      <option value="beginner">Tutor: Beginner</option>
      <option value="intermediate" selected>Tutor: Intermediate</option>
      <option value="expert">Tutor: Expert</option>
    </select>
  </div>
  <div id="ctfChatLog">Bot: Ask me directly about this level, attack type, or mitigation steps.</div>
  <div style="display:flex;gap:6px;margin-top:8px;">
    <input id="ctfChatInput" placeholder="Ask: how to solve this level safely?">
    <button type="button" onclick="sendCtcChat()">Ask</button>
  </div>
</div>
<a href="/ctf/scoreboard">View scoreboard</a> |
<a href="/learn/maze">Back to maze</a>
</div></div>
<script>
async function sendCtcChat() {
  const input = document.getElementById('ctfChatInput');
  const log = document.getElementById('ctfChatLog');
  const msg = (input.value || '').trim();
  if (!msg) return;
  log.textContent += "\\nYou: " + msg;
  input.value = "";
  const res = await fetch('/ctf/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg})
  });
  const data = await res.json();
  log.textContent += "\\nBot: " + (data.reply || 'No response');
}
async function loadCtfTutorMode() {
  const res = await fetch('/api/tutor_mode?module=ctf');
  const data = await res.json();
  if (data.mode) document.getElementById('ctfTutorMode').value = data.mode;
}
async function saveCtfTutorMode() {
  const mode = document.getElementById('ctfTutorMode').value;
  await fetch('/api/tutor_mode', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({module: 'ctf', mode})
  });
}
document.addEventListener('keydown', function(e){
  if (e.key === 'Enter' && document.activeElement && document.activeElement.id === 'ctfChatInput') {
    sendCtcChat();
  }
});
document.addEventListener('DOMContentLoaded', function(){
  loadCtfTutorMode();
  const el = document.getElementById('ctfTutorMode');
  if (el) el.addEventListener('change', saveCtfTutorMode);
});
</script>
"""

CTF_DONE_PAGE = CTF_STYLE + """
<div class="fx-grid"></div><div class="fx-scan"></div>
<div class="wrap"><div class="card">
<div class="switcher"><button type="button" onclick="toggleTheme()">Switch Theme</button></div>
<h2>Cloud Attack Path Simulator - CTF Completed</h2>
<p>Great work {{ user }}. You completed all levels.</p>
<p>Final Score: <b>{{ score }}</b></p>
{% if ai_text %}<div class="ai"><b>AI Career Insight:</b> {{ ai_text }}</div>{% endif %}
<a href="/ctf/scoreboard">View scoreboard</a> |
<a href="/learn/maze">Back to maze</a>
</div></div>
"""

CTF_SCOREBOARD_PAGE = CTF_STYLE + """
<div class="fx-grid"></div><div class="fx-scan"></div>
<div class="wrap"><div class="card">
<div class="switcher"><button type="button" onclick="toggleTheme()">Switch Theme</button></div>
<h2>Cloud Attack Path Simulator - CTF Scoreboard</h2>
<table>
<tr><th>User</th><th>Score</th><th>Current Level</th></tr>
{% for row in rows %}
<tr><td>{{ row.user }}</td><td>{{ row.score }}</td><td>{{ row.level }}</td></tr>
{% endfor %}
</table>
<a href="/ctf">Back to challenge</a>
</div></div>
"""

CTF_REGISTER_PAGE = CTF_STYLE + """
<div class="fx-grid"></div><div class="fx-scan"></div>
<div class="wrap"><div class="card">
<h2>CTF Student Registration</h2>
<p>Choose your username and continue with your own CTF progress.</p>
{% if error %}<p class="bad">{{ error }}</p>{% endif %}
<form method="post">
  <input name="username" placeholder="Username (3-24 chars: letters, numbers, _)" required>
  <button type="submit">Start CTF</button>
</form>
<p><small>Use a unique username. Progress and score are tracked per username.</small></p>
<a href="/login">Back to SOC login</a>
</div></div>
"""

TECHNIQUE_DEFENSES = {
    "T1059": [
        "Restrict script interpreters using application control policies.",
        "Enable command-line auditing and alert on suspicious parent-child process chains.",
    ],
    "T1003": [
        "Enable LSASS protection and disable debug privileges for non-admin accounts.",
        "Monitor credential dumping tools and memory access anomalies.",
    ],
    "T1047": [
        "Harden WMI permissions and monitor remote WMI execution patterns.",
        "Segment admin networks and enforce just-in-time access.",
    ],
    "T1021": [
        "Require MFA for remote access and disable legacy authentication.",
        "Alert on abnormal remote service creation and lateral movement paths.",
    ],
    "T1053": [
        "Monitor task scheduler creations and modifications.",
        "Restrict who can create persistent scheduled tasks.",
    ],
}


def get_ctf_state(user):
    if user not in ctf_progress:
        ctf_progress[user] = {"level_index": 0, "score": 0, "attempts": 0}
    return ctf_progress[user]


def _ctf_difficulty_mode(level_name):
    name = (level_name or "").strip().lower()
    if name == "easy":
        return "beginner"
    if name == "hard":
        return "expert"
    return "intermediate"


def _ctf_difficulty_guidance(level_name):
    name = (level_name or "").strip().lower()
    if name == "easy":
        return "Respond with simple language and direct actionable guidance. If user asks for the answer, provide it directly."
    if name == "hard":
        return "Respond with advanced depth, include tradeoffs, verification strategy, and at least one pitfall."
    return "Respond with step-by-step guided hints first, then answer directly only if user explicitly requests it."


def _valid_student_username(username):
    return bool(USERNAME_PATTERN.fullmatch((username or "").strip()))


def call_openai_messages(messages, max_tokens=220, temperature=0.35):
    if not OPENAI_API_KEY:
        return None
    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=20,
        )
        res.raise_for_status()
        payload = res.json()
        return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def call_openai(system_prompt, user_prompt, max_tokens=220):
    return call_openai_messages(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
    )


def _get_chat_history(channel):
    key = f"chat_history_{channel}"
    return session.get(key, [])


def _set_chat_history(channel, history):
    key = f"chat_history_{channel}"
    session[key] = history[-12:]


def _normalize_mode(value):
    mode = (value or "").strip().lower()
    if mode not in VALID_TUTOR_MODES:
        return "intermediate"
    return mode


def _mode_prompt(mode):
    if mode == "beginner":
        return "Use very simple language, define every key term, and include a small example."
    if mode == "expert":
        return "Use advanced detail, include tradeoffs, edge cases, and practical pitfalls."
    return "Use balanced technical depth with clear explanation and practical steps."


def _module_from_channel(channel):
    if channel.startswith("tutor_"):
        return channel.replace("tutor_", "", 1)
    return channel


def _get_tutor_mode(channel):
    module = _module_from_channel(channel)
    return _normalize_mode(session.get(f"tutor_mode_{module}", "intermediate"))


def _set_tutor_mode(module, mode):
    session[f"tutor_mode_{module}"] = _normalize_mode(mode)


def chat_with_memory(channel, system_prompt, user_message, context_block="", max_tokens=220, mode_override=None):
    mode = _normalize_mode(mode_override) if mode_override else _get_tutor_mode(channel)
    history = _get_chat_history(channel)
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "system", "content": f"Tutor depth mode: {mode}. {_mode_prompt(mode)}"})
    if context_block:
        messages.append({"role": "system", "content": f"Context:\n{context_block}"})
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    reply = call_openai_messages(messages, max_tokens=max_tokens)
    if reply:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        _set_chat_history(channel, history)
    return reply


def fallback_insight(topic):
    return (
        f"Focus area: {topic}.\\n"
        "1) Identify attacker objective.\\n"
        "2) Contain spread quickly.\\n"
        "3) Collect evidence logs.\\n"
        "4) Patch and harden weak points.\\n"
        "5) Validate controls with a replay drill."
    )


def fallback_coach(domain, message, context):
    msg = (message or "").strip()
    if domain == "soc":
        risk = context.get("risk", "LOW")
        techniques = context.get("techniques", [])
        top = ", ".join(techniques[:3]) if techniques else "No mapped techniques yet"
        return (
            f"Topic: SOC Incident Tutoring\n"
            f"Question: {msg or 'How do I handle this incident?'}\n\n"
            f"What this means:\n"
            f"- Current risk is {risk}.\n"
            f"- Top observed behaviors: {top}.\n\n"
            "Step-by-step response:\n"
            "1) Scope the incident: identify affected hosts/users and timeline.\n"
            "2) Contain quickly: isolate impacted host or account.\n"
            "3) Preserve evidence: collect process, network, and auth logs.\n"
            "4) Eradicate root cause: block IOC, remove persistence, patch weakness.\n"
            "5) Validate recovery: monitor for recurrence and run replay checks.\n\n"
            "Common mistake:\n"
            "- Patching before evidence collection can destroy useful forensic traces."
        )
    if domain == "maze":
        scenario = context.get("scenario_name", "Unknown scenario")
        expected = context.get("expected_cmd", "help")
        return (
            f"Topic: Maze Scenario Tutoring ({scenario})\n"
            f"Question: {msg or 'What should I do now?'}\n\n"
            "How to think:\n"
            "- This lab trains real incident sequence, not random commands.\n"
            "- Each step reduces uncertainty before action.\n\n"
            f"Immediate next command: `{expected}`\n"
            "Why this step matters:\n"
            "- It prepares evidence/context for the following containment action.\n\n"
            "After this:\n"
            "1) run next expected command,\n"
            "2) verify output,\n"
            "3) move to next scenario only after verify succeeds."
        )
    if domain == "ctf":
        level = context.get("level", "Unknown")
        topic = context.get("topic", "security fundamentals")
        return (
            f"Topic: CTF Tutor (Level {level})\n"
            f"Focus: {topic}\n"
            f"Question: {msg or 'How do I solve this level?'}\n\n"
            "Learning approach:\n"
            "1) Rephrase the question in your own words.\n"
            "2) Identify what evidence or command is being tested.\n"
            "3) Try one controlled hypothesis and observe output.\n"
            "4) If wrong, compare expected concept vs your assumption.\n"
            "5) Retry with corrected reasoning.\n\n"
            "Quick checklist:\n"
            "- Did I verify context first?\n"
            "- Did I use the right command/control for this task?\n"
            "- Did I validate before submitting?"
        )
    return (
        f"Topic: Security Tutor\nQuestion: {msg or 'Explain this topic'}\n\n"
        "Use this flow: Understand objective -> Contain risk -> Collect evidence -> Fix root cause -> Validate controls."
    )


def tutor_response(channel, user_message, context_block="", teaching_goal="security operations", mode_override=None):
    system_prompt = (
        "You are an expert cybersecurity tutor, like ChatGPT in teaching mode. "
        "Teach thoroughly but clearly. "
        "Explain concepts from basics to advanced, define terms, give examples, and provide practical steps. "
        "When useful, include: What, Why, How, Common Mistakes, and Quick Checklist. "
        "If user asks a direct action question, still teach the reasoning behind the action."
    )
    return chat_with_memory(
        channel,
        system_prompt,
        user_message or f"Teach me {teaching_goal} in detail.",
        context_block=context_block,
        max_tokens=500,
        mode_override=mode_override,
    )


def _wants_direct_answer(text):
    msg = (text or "").strip().lower()
    if not msg:
        return False
    return any(token in msg for token in ANSWER_REQUEST_HINTS)


MAZE_LEVELS = ("easy", "medium", "hard")

MAZE_SCENARIOS = [
    {
        "level": "easy",
        "name": "Initial Compromise",
        "technique": "T1059",
        "attack": "Command execution via suspicious script",
        "case_study": "Attackers often launch script-based payloads to disable defenses before ransomware deployment.",
        "steps": [
            {"cmd": "recon", "label": "Recon host", "points": 10},
            {"cmd": "review_logs", "label": "Review logs", "points": 10},
            {"cmd": "isolate_host", "label": "Isolate host", "points": 20},
            {"cmd": "block_ioc", "label": "Block IOC", "points": 20},
            {"cmd": "verify", "label": "Verify containment", "points": 15},
        ],
    },
    {
        "level": "easy",
        "name": "Lateral Movement",
        "technique": "T1021",
        "attack": "Remote service abuse to move between systems",
        "case_study": "Breaches spread quickly when remote protocols are exposed with weak access control.",
        "steps": [
            {"cmd": "recon", "label": "Map spread", "points": 10},
            {"cmd": "review_logs", "label": "Trace remote sessions", "points": 10},
            {"cmd": "isolate_host", "label": "Quarantine pivot host", "points": 20},
            {"cmd": "rotate_creds", "label": "Rotate credentials", "points": 20},
            {"cmd": "verify", "label": "Verify lateral stop", "points": 15},
        ],
    },
    {
        "level": "medium",
        "name": "Credential Access",
        "technique": "T1003",
        "attack": "Credential dumping attempt on critical host",
        "case_study": "Credential dumping usually precedes privilege escalation and domain takeover.",
        "steps": [
            {"cmd": "recon", "label": "Identify affected process", "points": 10},
            {"cmd": "review_logs", "label": "Check memory access events", "points": 10},
            {"cmd": "block_ioc", "label": "Block dumping tools", "points": 20},
            {"cmd": "patch_system", "label": "Patch and harden host", "points": 20},
            {"cmd": "verify", "label": "Verify credential safety", "points": 15},
        ],
    },
    {
        "level": "medium",
        "name": "Persistence via Scheduled Task",
        "technique": "T1053",
        "attack": "Attacker persists by creating hidden recurring tasks",
        "case_study": "Scheduled task abuse survives reboots and often blends into admin noise.",
        "steps": [
            {"cmd": "recon", "label": "Find persistence indicators", "points": 10},
            {"cmd": "review_logs", "label": "Review task creation logs", "points": 12},
            {"cmd": "block_ioc", "label": "Disable malicious task patterns", "points": 18},
            {"cmd": "patch_system", "label": "Harden scheduler permissions", "points": 20},
            {"cmd": "verify", "label": "Validate persistence removed", "points": 15},
        ],
    },
    {
        "level": "hard",
        "name": "Remote Execution via WMI",
        "technique": "T1047",
        "attack": "Remote WMI execution from compromised management account",
        "case_study": "WMI abuse is common for stealthy remote execution in enterprise environments.",
        "steps": [
            {"cmd": "recon", "label": "Identify suspicious remote execution source", "points": 10},
            {"cmd": "review_logs", "label": "Correlate WMI/process telemetry", "points": 12},
            {"cmd": "isolate_host", "label": "Isolate high-risk execution node", "points": 18},
            {"cmd": "rotate_creds", "label": "Rotate compromised admin credentials", "points": 22},
            {"cmd": "verify", "label": "Confirm remote execution blocked", "points": 15},
        ],
    },
    {
        "level": "hard",
        "name": "Data Exfiltration Preparation",
        "technique": "T1041",
        "attack": "Staged collection and external transfer attempt",
        "case_study": "Exfiltration often follows privilege access and cleanup, making timing critical.",
        "steps": [
            {"cmd": "recon", "label": "Identify staged data paths", "points": 10},
            {"cmd": "review_logs", "label": "Trace outbound transfer patterns", "points": 12},
            {"cmd": "block_ioc", "label": "Block exfil destinations", "points": 20},
            {"cmd": "isolate_host", "label": "Quarantine exfil source host", "points": 20},
            {"cmd": "verify", "label": "Confirm no active data leakage", "points": 15},
        ],
    },
]

MAZE_COMMAND_ALIASES = {
    "recon": "recon",
    "scan": "recon",
    "check": "recon",
    "logs": "review_logs",
    "review": "review_logs",
    "review_logs": "review_logs",
    "isolate": "isolate_host",
    "isolate_host": "isolate_host",
    "block": "block_ioc",
    "block_ioc": "block_ioc",
    "patch": "patch_system",
    "patch_system": "patch_system",
    "rotate": "rotate_creds",
    "rotate_creds": "rotate_creds",
    "verify": "verify",
    "next": "next",
    "status": "status",
    "help": "help",
    "reset": "reset",
}

MAZE_CMD_OUTPUT = {
    "recon": "Recon complete: suspicious behavior confirmed on target host.",
    "review_logs": "Logs reviewed: attack trail mapped with timestamps and source.",
    "isolate_host": "Containment applied: host moved to quarantine segment.",
    "block_ioc": "IOC blocked at endpoint and network policy layers.",
    "patch_system": "System patched and hardening baseline applied.",
    "rotate_creds": "Credentials rotated and high-risk sessions revoked.",
    "verify": "Validation checks passed. Threat progression halted.",
}


def _normalize_maze_level(value):
    v = (value or "").strip().lower()
    if v not in MAZE_LEVELS:
        return "easy"
    return v


def _scenarios_for_level(level):
    lv = _normalize_maze_level(level)
    return [s for s in MAZE_SCENARIOS if s.get("level") == lv]


def _new_maze_state(level="easy"):
    return {
        "level": _normalize_maze_level(level),
        "health": 100,
        "score": 0,
        "scenario_index": 0,
        "step_index": 0,
        "completed": 0,
        "finished": False,
        "history": ["Mission started. Use: help"],
    }


def _get_maze_state():
    state = session.get("maze_state")
    if not state:
        state = _new_maze_state()
        session["maze_state"] = state
    state["level"] = _normalize_maze_level(state.get("level"))
    return state


def _active_scenario(state):
    scenarios = _scenarios_for_level(state.get("level"))
    idx = state["scenario_index"]
    if idx >= len(scenarios):
        return None
    return scenarios[idx]


def _maze_response(state, output=None):
    scenario = _active_scenario(state)
    scenarios = _scenarios_for_level(state.get("level"))
    next_step = None
    if scenario and state["step_index"] < len(scenario["steps"]):
        next_step = scenario["steps"][state["step_index"]]
    return {
        "level": state.get("level", "easy"),
        "available_levels": list(MAZE_LEVELS),
        "total_scenarios": len(scenarios),
        "health": state["health"],
        "score": state["score"],
        "completed": state["completed"],
        "finished": state["finished"],
        "scenario_index": state["scenario_index"],
        "history": state["history"][-12:],
        "scenario": scenario,
        "next_step": next_step,
        "output": output or "",
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password", "")
        valid_user = bool(username) and (ALLOW_MULTI_USER or username == USERNAME)
        if valid_user and password == PASSWORD:
            # Store real username so CTF/maze progress and scoreboards are per user.
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/ctf/register", methods=["GET", "POST"])
def ctf_register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        if not _valid_student_username(username):
            return render_template_string(
                CTF_REGISTER_PAGE,
                error="Invalid username. Use 3-24 letters, numbers, or underscore.",
            )
        session["user"] = username
        session["role"] = "student"
        return redirect("/ctf")
    return render_template_string(CTF_REGISTER_PAGE, error="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    try:
        graph = fetch_graph_data()
        db_error = None
    except Exception:
        graph = empty_graph()
        db_error = "Unable to load graph data from Neo4j. Check DB connection."

    return render_template("index.html", graph=graph, db_error=db_error)


@app.route("/api/graph")
def api_graph():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    agent_id = request.args.get("agent") or None
    target = request.args.get("target") or None

    try:
        graph = fetch_graph_data(agent_id=agent_id, target=target)
        return jsonify(graph)
    except Exception as exc:
        payload = empty_graph()
        payload["error"] = f"Neo4j query failed: {exc}"
        return jsonify(payload), 500


@app.route("/api/defense")
def api_defense():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    agent_id = request.args.get("agent") or None
    target = request.args.get("target") or None

    try:
        graph = fetch_graph_data(agent_id=agent_id, target=target)
        techniques = [t["id"] for t in graph.get("techniques", [])]
        recommendations = generate_defense_recommendations(techniques)
        return jsonify({"techniques": techniques, "recommendations": recommendations})
    except Exception as exc:
        return jsonify({"error": str(exc), "recommendations": []}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    agent_id = data.get("agent")
    target = data.get("target")

    graph = fetch_graph_data(agent_id=agent_id, target=target)
    top_techniques = [t["id"] for t in graph.get("techniques", [])[:3]]
    risk = graph.get("summary", {}).get("risk_level", "LOW")
    top_path = (graph.get("attack_paths") or [{}])[0]
    top_path_target = top_path.get("target", "unknown")
    top_path_len = top_path.get("length", 0)
    top_path_risk = top_path.get("risk_score", 0)

    ai_reply = tutor_response(
        "soc",
        message or "Teach me how to handle this incident.",
        context_block=(
            f"Domain: SOC incident response\n"
            f"Current risk: {risk}\n"
            f"Top techniques: {', '.join(top_techniques) if top_techniques else 'none'}\n"
            f"Top attack path target: {top_path_target}\n"
            f"Top attack path depth: {top_path_len}\n"
            f"Top attack path risk: {top_path_risk}\n"
            f"Selected agent: {agent_id or 'all'}\n"
            f"Selected target: {target or 'all'}\n"
            f"Goal: explain and guide mitigation decisions."
        ),
        teaching_goal="SOC incident handling and mitigation",
    )

    if ai_reply:
        reply = ai_reply
    else:
        reply = fallback_coach("soc", message, {"risk": risk, "techniques": top_techniques})

    return jsonify(
        {
            "reply": reply,
            "risk_level": risk,
            "top_techniques": top_techniques,
            "top_attack_path": top_path,
        }
    )


@app.route("/api/tutor_mode", methods=["GET", "POST"])
def api_tutor_mode():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "GET":
        module = (request.args.get("module") or "soc").strip().lower()
        return jsonify({"module": module, "mode": _normalize_mode(session.get(f"tutor_mode_{module}", "intermediate"))})

    data = request.get_json(silent=True) or {}
    module = (data.get("module") or "soc").strip().lower()
    mode = _normalize_mode(data.get("mode"))
    _set_tutor_mode(module, mode)
    return jsonify({"module": module, "mode": mode})


@app.route("/api/tutor", methods=["POST"])
def api_tutor():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    channel = (data.get("channel") or "general").strip().lower()
    topic = (data.get("topic") or "cybersecurity").strip()
    message = (data.get("message") or "").strip()
    context = (data.get("context") or "").strip()

    ai_reply = tutor_response(
        f"tutor_{channel}",
        message or f"Teach me {topic} from basics with examples.",
        context_block=f"Topic: {topic}\n{context}",
        teaching_goal=topic,
    )
    reply = ai_reply or fallback_insight(topic)
    return jsonify({"reply": reply})


@app.route("/api/maze_insight", methods=["POST"])
def api_maze_insight():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    technique = data.get("technique", "unknown")
    task = data.get("task", "mitigate")

    ai_text = call_openai(
        "You are a cybersecurity trainer for beginners.",
        f"Explain {technique} in simple words and provide 4 step-by-step actions to {task}.",
        max_tokens=180,
    )

    return jsonify({"insight": ai_text or fallback_insight(f"{technique} / {task}")})


@app.route("/api/maze/state")
def api_maze_state():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    state = _get_maze_state()
    return jsonify(_maze_response(state))


@app.route("/api/maze/reset", methods=["POST"])
def api_maze_reset():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    current = _get_maze_state()
    session["maze_state"] = _new_maze_state(current.get("level", "easy"))
    return jsonify(_maze_response(session["maze_state"], "Environment reset. Start with: recon"))


@app.route("/api/maze/level", methods=["POST"])
def api_maze_level():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    level = _normalize_maze_level(data.get("level"))
    session["maze_state"] = _new_maze_state(level)
    return jsonify(_maze_response(session["maze_state"], f"Difficulty set to {level}. Start with: recon"))


@app.route("/api/maze/command", methods=["POST"])
def api_maze_command():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    state = _get_maze_state()
    scenarios = _scenarios_for_level(state.get("level"))
    data = request.get_json(silent=True) or {}
    raw = (data.get("command") or "").strip().lower()
    if not raw:
        return jsonify(_maze_response(state, "Enter a command. Try: help"))

    cmd = MAZE_COMMAND_ALIASES.get(raw, None)
    if cmd is None:
        return jsonify(_maze_response(state, "Unknown command. Use: help"))

    if cmd == "reset":
        session["maze_state"] = _new_maze_state()
        return jsonify(_maze_response(session["maze_state"], "Environment reset. Start with: recon"))

    if cmd == "help":
        return jsonify(_maze_response(state, "Commands: recon, logs, isolate, block, patch, rotate, verify, next, status, reset"))

    if cmd == "status":
        return jsonify(_maze_response(state, f"Level={state['level']} Health={state['health']} Score={state['score']} Completed={state['completed']}/{len(scenarios)}"))

    if state["finished"]:
        return jsonify(_maze_response(state, "All scenarios completed. Use reset to play again."))

    scenario = _active_scenario(state)
    if not scenario:
        state["finished"] = True
        session["maze_state"] = state
        return jsonify(_maze_response(state, "Mission complete."))

    # Scenario completed, require explicit next
    if state["step_index"] >= len(scenario["steps"]):
        if cmd == "next":
            state["scenario_index"] += 1
            state["step_index"] = 0
            if state["scenario_index"] >= len(scenarios):
                state["finished"] = True
                state["history"].append("All attack scenarios mitigated.")
                session["maze_state"] = state
                return jsonify(_maze_response(state, "Mission complete. Great response speed."))
            next_scn = _active_scenario(state)
            out = f"Moved to next scenario: {next_scn['name']} ({next_scn['technique']}). Start with: recon"
            state["history"].append(out)
            session["maze_state"] = state
            return jsonify(_maze_response(state, out))
        return jsonify(_maze_response(state, "Scenario finished. Type: next"))

    expected = scenario["steps"][state["step_index"]]
    expected_cmd = expected["cmd"]

    if cmd == expected_cmd:
        points = expected["points"]
        state["score"] += points
        state["step_index"] += 1
        out = f"{MAZE_CMD_OUTPUT.get(cmd, 'Step done')} (+{points})"
        state["history"].append(out)

        if state["step_index"] >= len(scenario["steps"]):
            state["completed"] += 1
            done_msg = f"Scenario '{scenario['name']}' mitigated. Type: next"
            state["history"].append(done_msg)
            out = f"{out}\n{done_msg}"
    else:
        state["health"] = max(0, state["health"] - 6)
        out = f"Action out of order. Expected: {expected_cmd}. Health -6"
        state["history"].append(out)

    session["maze_state"] = state
    return jsonify(_maze_response(state, out))


@app.route("/api/maze_chat", methods=["POST"])
def api_maze_chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    state = _get_maze_state()
    scenario = _active_scenario(state)
    technique = data.get("technique") or (scenario["technique"] if scenario else "unknown")
    active_tool = data.get("active_tool", "none")
    blocked = bool(data.get("blocked", False))

    next_step = None
    if scenario and state["step_index"] < len(scenario["steps"]):
        next_step = scenario["steps"][state["step_index"]]["cmd"]

    ai_text = tutor_response(
        "maze",
        message or "Teach me what to do in this maze scenario.",
        context_block=(
            f"Domain: SOC maze simulation\n"
            f"Difficulty level: {state.get('level', 'easy')}\n"
            f"Technique: {technique}\n"
            f"Selected tool: {active_tool}\n"
            f"Blocked: {blocked}\n"
            f"Scenario: {scenario['name'] if scenario else 'none'}\n"
            f"Expected next command: {next_step or 'next'}\n"
            f"Health: {state['health']} Score: {state['score']}\n"
            f"Goal: teach user why each terminal command matters."
        ),
        teaching_goal="terminal-based attack mitigation",
    )

    reply = ai_text or fallback_coach(
        "maze",
        message,
        {
            "scenario_name": scenario["name"] if scenario else "none",
            "expected_cmd": next_step or "next",
        },
    )
    return jsonify({"reply": reply})


@app.route("/learn/maze")
def learn_maze():
    if "user" not in session:
        return redirect("/login")
    return render_template("maze.html")


@app.route("/ctf")
def ctf_home():
    if "user" not in session:
        return redirect("/ctf/register")

    user = session["user"]
    state = get_ctf_state(user)
    show_hint = request.args.get("show_hint") == "1"

    if state["level_index"] >= len(CTF_LEVELS):
        ai_text = call_openai(
            "You are a SOC learning coach.",
            "Give a short next-step learning path after completing beginner CTF levels.",
            max_tokens=140,
        ) or fallback_insight("post-ctf growth")
        return render_template_string(CTF_DONE_PAGE, user=user, score=state["score"], ai_text=ai_text)

    level = CTF_LEVELS[state["level_index"]]
    return render_template_string(
        CTF_CHALLENGE_PAGE,
        user=user,
        level=level,
        score=state["score"],
        attempts=state["attempts"],
        show_hint=show_hint,
        message="",
        success=False,
        ai_text="",
    )


@app.route("/ctf/submit", methods=["POST"])
def ctf_submit():
    if "user" not in session:
        return redirect("/ctf/register")

    user = session["user"]
    state = get_ctf_state(user)

    if state["level_index"] >= len(CTF_LEVELS):
        return redirect("/ctf")

    level = CTF_LEVELS[state["level_index"]]
    submitted = (request.form.get("answer") or "").strip().lower()
    expected = level["answer"].strip().lower()

    state["attempts"] += 1

    if submitted == expected:
        state["score"] += 50 * level["level"]
        state["level_index"] += 1
        state["attempts"] = 0
        return redirect("/ctf")

    msg = "Not correct yet. Read hint and try again."
    return render_template_string(
        CTF_CHALLENGE_PAGE,
        user=user,
        level=level,
        score=state["score"],
        attempts=state["attempts"],
        show_hint=True,
        message=msg,
        success=False,
        ai_text="",
    )


@app.route("/ctf/insight", methods=["POST"])
def ctf_insight():
    if "user" not in session:
        return redirect("/ctf/register")

    user = session["user"]
    state = get_ctf_state(user)

    if state["level_index"] >= len(CTF_LEVELS):
        return redirect("/ctf")

    level = CTF_LEVELS[state["level_index"]]
    ai_text = call_openai(
        "You are a CTF mentor.",
        (
            f"Level topic: {level['topic']}\\n"
            f"Question: {level['question']}\\n"
            "Give guidance without revealing direct final answer."
        ),
        max_tokens=170,
    ) or fallback_insight(level["topic"])

    return render_template_string(
        CTF_CHALLENGE_PAGE,
        user=user,
        level=level,
        score=state["score"],
        attempts=state["attempts"],
        show_hint=False,
        message="AI insight generated.",
        success=True,
        ai_text=ai_text,
    )


@app.route("/ctf/chat", methods=["POST"])
def ctf_chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = session["user"]
    state = get_ctf_state(user)
    current_level_idx = min(state["level_index"], len(CTF_LEVELS) - 1)
    level = CTF_LEVELS[current_level_idx]

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    mode = _get_tutor_mode("ctf")
    level_mode = _ctf_difficulty_mode(level["name"])
    effective_mode = mode if mode != "intermediate" else level_mode

    if (effective_mode == "beginner" or level["name"].lower() == "easy") and _wants_direct_answer(message):
        direct = (
            f"Direct answer for Level {level['level']}: `{level['answer']}`.\n"
            f"Why: this level focuses on {level['topic']}."
        )
        return jsonify({"reply": direct})

    ai_text = tutor_response(
        "ctf",
        message or "Teach me this CTF topic in depth and guide my solving steps.",
        context_block=(
            f"Domain: CTF training\n"
            f"Current level: {level['level']} ({level['name']})\n"
            f"Topic: {level['topic']}\n"
            f"Question: {level['question']}\n"
            f"Hint: {level['hint']}\n"
            f"Attempts: {state['attempts']}\n"
            f"Difficulty guidance: {_ctf_difficulty_guidance(level['name'])}\n"
            f"Use effective tutor mode: {effective_mode}\n"
            f"Goal: teach concepts and solving method according to level difficulty."
        ),
        teaching_goal=level["topic"],
        mode_override=effective_mode,
    )
    reply = ai_text or fallback_coach(
        "ctf",
        message,
        {"level": level["level"], "topic": level["topic"]},
    )
    return jsonify({"reply": reply})


@app.route("/ctf/scoreboard")
def ctf_scoreboard():
    if "user" not in session:
        return redirect("/ctf/register")

    rows = []
    for user, st in ctf_progress.items():
        current_level = st["level_index"] + 1
        if st["level_index"] >= len(CTF_LEVELS):
            current_level = "Done"
        rows.append({"user": user, "score": st["score"], "level": current_level})

    rows.sort(key=lambda x: x["score"], reverse=True)
    return render_template_string(CTF_SCOREBOARD_PAGE, rows=rows)


# ---------------- FETCH GRAPH ----------------
def fetch_graph_data(agent_id=None, target=None):
    nodes = {}
    edges = []
    edge_ids = set()
    techniques = Counter()
    targets = set()

    with driver.session(database="neo4j") as db_session:
        result = db_session.run(
            """
            MATCH (a:Agent)
            WHERE ($agent_id IS NULL OR a.agent_id = $agent_id)
            OPTIONAL MATCH (a)-[:EXECUTED]->(f:Fact)
            WHERE ($target IS NULL OR f IS NULL OR properties(f)['target'] = $target)
            OPTIONAL MATCH (f)-[:NEXT]->(n:Fact)
            WHERE ($target IS NULL OR n IS NULL OR properties(n)['target'] = $target)
            RETURN a.agent_id AS agent,
                   f.fact_id AS fid,
                   f.command AS cmd,
                   f.technique_id AS tech,
                   properties(f)['target'] AS ftarget,
                   n.fact_id AS nid,
                   n.command AS ncmd,
                   n.technique_id AS ntech,
                   properties(n)['target'] AS ntarget
            """,
            agent_id=agent_id,
            target=target,
        )

        for row in result:
            agent = row["agent"]
            fid = row["fid"]
            cmd = row["cmd"]
            tech = row["tech"]
            ftarget = row["ftarget"]
            nid = row["nid"]
            ncmd = row["ncmd"]
            ntech = row["ntech"]
            ntarget = row["ntarget"]

            if agent not in nodes:
                nodes[agent] = {"data": {"id": agent, "label": agent, "type": "agent"}}

            if fid and fid not in nodes:
                nodes[fid] = {
                    "data": {
                        "id": fid,
                        "label": cmd if cmd else fid,
                        "type": "fact",
                        "technique": tech,
                        "target": ftarget,
                    }
                }

            if tech:
                techniques[tech] += 1
            if ftarget:
                targets.add(ftarget)

            if fid:
                executed_edge_id = f"{agent}-{fid}"
                if executed_edge_id not in edge_ids:
                    edge_ids.add(executed_edge_id)
                    edges.append({"data": {"id": executed_edge_id, "source": agent, "target": fid, "relation": "executed"}})

            if nid:
                if nid not in nodes:
                    nodes[nid] = {
                        "data": {
                            "id": nid,
                            "label": ncmd if ncmd else nid,
                            "type": "fact",
                            "technique": ntech,
                            "target": ntarget,
                        }
                    }

                if ntech:
                    techniques[ntech] += 1
                if ntarget:
                    targets.add(ntarget)

                if fid:
                    next_edge_id = f"{fid}-{nid}"
                    if next_edge_id not in edge_ids:
                        edge_ids.add(next_edge_id)
                        edges.append({"data": {"id": next_edge_id, "source": fid, "target": nid, "relation": "next"}})

    graph = {"nodes": list(nodes.values()), "edges": edges}
    attack_paths, target_risk = build_attack_paths(graph)
    graph["attack_paths"] = attack_paths
    graph["target_risk"] = target_risk
    graph["summary"] = build_summary(graph, techniques, target_risk)
    graph["filters"] = {
        "agents": sorted([n["data"]["id"] for n in graph["nodes"] if n["data"]["type"] == "agent"]),
        "targets": sorted(targets),
    }
    graph["techniques"] = [{"id": tech_id, "count": count} for tech_id, count in techniques.most_common(12)]

    return graph


def build_attack_paths(graph, max_depth=8, max_paths=40):
    node_map = {n["data"]["id"]: n["data"] for n in graph.get("nodes", [])}
    next_adj = {}
    incoming_next = set()
    executed_from_fact = {}

    for edge in graph.get("edges", []):
        ed = edge.get("data", {})
        src = ed.get("source")
        dst = ed.get("target")
        rel = ed.get("relation")
        if rel == "next" and src and dst:
            next_adj.setdefault(src, []).append(dst)
            incoming_next.add(dst)
        if rel == "executed" and src and dst:
            executed_from_fact.setdefault(dst, set()).add(src)

    fact_nodes = [nid for nid, nd in node_map.items() if nd.get("type") == "fact"]
    starts = [nid for nid in fact_nodes if nid not in incoming_next]
    if not starts:
        starts = fact_nodes

    collected = []

    def path_target(path):
        targets = [node_map[n].get("target") for n in path if node_map.get(n, {}).get("target")]
        if not targets:
            return "unknown"
        return Counter(targets).most_common(1)[0][0]

    def path_techniques(path):
        return [node_map[n].get("technique") for n in path if node_map.get(n, {}).get("technique")]

    def path_agents(path):
        if not path:
            return []
        return sorted(executed_from_fact.get(path[0], set()))

    def score_path(path):
        unique_tech = len(set(path_techniques(path)))
        return min(100, (len(path) * 9) + (unique_tech * 6))

    def walk(curr, path, seen):
        if len(collected) >= max_paths:
            return
        children = next_adj.get(curr, [])
        is_leaf = not children
        if is_leaf or len(path) >= max_depth:
            collected.append(path[:])
            return
        for nxt in children:
            if nxt in seen:
                continue
            seen.add(nxt)
            path.append(nxt)
            walk(nxt, path, seen)
            path.pop()
            seen.remove(nxt)

    for start in starts:
        walk(start, [start], {start})
        if len(collected) >= max_paths:
            break

    seen_chain = set()
    ranked = []
    for p in collected:
        sig = tuple(p)
        if sig in seen_chain:
            continue
        seen_chain.add(sig)
        ranked.append(
            {
                "agents": path_agents(p),
                "target": path_target(p),
                "length": len(p),
                "nodes": p,
                "commands": [node_map[n].get("label") for n in p if node_map.get(n)],
                "techniques": path_techniques(p),
                "risk_score": score_path(p),
            }
        )

    ranked.sort(key=lambda x: (x["risk_score"], x["length"]), reverse=True)
    ranked = ranked[:10]

    target_risk = {}
    for item in ranked:
        t = item["target"]
        if t == "unknown":
            continue
        current = target_risk.get(t, {"max_path_risk": 0, "path_count": 0})
        current["max_path_risk"] = max(current["max_path_risk"], item["risk_score"])
        current["path_count"] += 1
        target_risk[t] = current

    return ranked, target_risk


def build_summary(graph, techniques, target_risk=None):
    fact_count = sum(1 for n in graph["nodes"] if n["data"]["type"] == "fact")
    agent_count = sum(1 for n in graph["nodes"] if n["data"]["type"] == "agent")
    chain_count = sum(1 for e in graph["edges"] if e["data"].get("relation") == "next")
    technique_count = len(techniques)
    risk_score = min(100, (fact_count * 3) + (chain_count * 8) + (technique_count * 5))

    if risk_score >= 70:
        risk_level = "CRITICAL"
    elif risk_score >= 40:
        risk_level = "ELEVATED"
    else:
        risk_level = "LOW"

    hottest_target = None
    if target_risk:
        hottest_target = max(target_risk.items(), key=lambda kv: (kv[1].get("max_path_risk", 0), kv[1].get("path_count", 0)))[0]

    return {
        "agent_count": agent_count,
        "fact_count": fact_count,
        "chain_count": chain_count,
        "technique_count": technique_count,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "hottest_target": hottest_target,
    }


def generate_defense_recommendations(technique_ids):
    recommendations = []
    for tid in technique_ids:
        recommendations.extend(TECHNIQUE_DEFENSES.get(tid, []))

    if not recommendations:
        recommendations = [
            "Enforce least privilege across all agent hosts.",
            "Enable endpoint detection for command execution and credential access.",
            "Segment critical systems and restrict east-west traffic.",
            "Apply patching and hardening baselines for exposed services.",
        ]

    seen = set()
    unique = []
    for item in recommendations:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique[:8]


def empty_graph():
    return {
        "nodes": [],
        "edges": [],
        "summary": {
            "agent_count": 0,
            "fact_count": 0,
            "chain_count": 0,
            "technique_count": 0,
            "risk_score": 0,
            "risk_level": "LOW",
            "hottest_target": None,
        },
        "filters": {"agents": [], "targets": []},
        "techniques": [],
        "attack_paths": [],
        "target_risk": {},
    }


if __name__ == "__main__":
    app.run(debug=False)
