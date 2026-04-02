import os
import sys
import re
import ipaddress
import time
from collections import Counter
from datetime import datetime, timezone

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
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "replace_with_neo4j_password")
CALDERA_URL = os.getenv("CALDERA_URL", "http://caldera:8888").rstrip("/")
CALDERA_API_KEY = os.getenv("CALDERA_API_KEY", "").strip()
CALDERA_TIMEOUT = int(os.getenv("CALDERA_TIMEOUT", "10"))
GEOIP_URL = os.getenv("GEOIP_URL", "https://ipapi.co/{ip}/json/").strip()
GEOIP_API_KEY = os.getenv("GEOIP_API_KEY", "").strip()
GEOIP_PROVIDER_LABEL = os.getenv("GEOIP_PROVIDER_LABEL", "ipapi.co").strip() or "GeoIP"
GEOIP_CACHE_SECONDS = int(os.getenv("GEOIP_CACHE_SECONDS", "1800"))
PUBLIC_IP_LOOKUP_URL = os.getenv("PUBLIC_IP_LOOKUP_URL", "https://api.ipify.org?format=json").strip()
ANALYST_LOCATION_QUERY = os.getenv("ANALYST_LOCATION_QUERY", "").strip()
ANALYST_LATITUDE = os.getenv("ANALYST_LATITUDE", "").strip()
ANALYST_LONGITUDE = os.getenv("ANALYST_LONGITUDE", "").strip()
GEOCODE_URL = os.getenv("GEOCODE_URL", "https://nominatim.openstreetmap.org/search").strip()
GEOCODE_USER_AGENT = os.getenv("GEOCODE_USER_AGENT", "cloud-attack-lab-dashboard/1.0").strip()

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)
geo_cache = {}

# ---------------- LOGIN ----------------
USERNAME = os.getenv("DASHBOARD_USER", "socadmin")
PASSWORD = os.getenv("DASHBOARD_PASS", "replace_with_dashboard_password")
ALLOW_MULTI_USER = os.getenv("ALLOW_MULTI_USER", "1").strip().lower() in {"1", "true", "yes", "on"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")

# ---------------- GEMINI ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
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
GREETING_TOKENS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "yo"}
THANKS_TOKENS = {"thanks", "thank you", "thx"}

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
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
body{margin:0;background:#070b12;color:#d6e9ff;font-family:'Space Grotesk',sans-serif;overflow-x:hidden}
.fx-grid{position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,247,176,.08) 1px, transparent 1px),linear-gradient(90deg, rgba(79,247,176,.08) 1px, transparent 1px);background-size:26px 26px;opacity:.25}
.fx-scan{position:fixed;inset:0;pointer-events:none;background:linear-gradient(180deg,transparent 0%,rgba(79,247,176,.09) 50%,transparent 100%);background-size:100% 6px;mix-blend-mode:screen;animation:scan 6s linear infinite}
@keyframes scan{from{transform:translateY(-12%)}to{transform:translateY(12%)}}
.wrap{max-width:980px;margin:26px auto;padding:16px;position:relative;z-index:2}
.card{background:rgba(12,20,34,.92);border:1px solid #2d4b73;padding:18px;border-radius:18px;box-shadow:0 0 22px rgba(88,170,255,.18)}
h2{margin-top:0;color:#4ff7b0;text-shadow:0 0 8px rgba(79,247,176,.45)}
input,select{width:100%;padding:10px;background:#08111f;color:#d6e9ff;border:1px solid #2a4260;border-radius:10px;font-family:'IBM Plex Mono',monospace}
button{margin-top:10px;padding:10px;background:#102741;color:#d6e9ff;border:1px solid #2f5f95;cursor:pointer;border-radius:10px;font-family:'IBM Plex Mono',monospace}
button:hover{box-shadow:0 0 14px rgba(79,247,176,.25)}
a{color:#7fe6ff}
small{color:#9ec7e6}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:8px;border-bottom:1px solid #223650;text-align:left}
.ok{color:#84f6b6}
.bad{color:#ff8a8a}
.ai{margin-top:12px;border:1px solid #2a4260;background:#08111f;padding:12px;white-space:pre-line;border-radius:14px}
.switcher{display:flex;justify-content:flex-end;margin-bottom:8px;gap:8px}
.switcher button{margin-top:0;padding:6px 8px;font-size:12px}
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:14px}
.section{border:1px solid rgba(88,170,255,.18);background:rgba(8,17,31,.75);padding:14px;border-radius:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chip{border:1px solid rgba(88,170,255,.25);background:rgba(16,39,65,.6);padding:6px 8px;border-radius:999px;font-size:11px;font-family:'IBM Plex Mono',monospace}
.cta{display:flex;gap:8px;flex-wrap:wrap}
.chat-log{display:flex;flex-direction:column;gap:8px;max-height:210px;overflow:auto;margin-top:10px}
.msg{max-width:92%;padding:10px 12px;border-radius:14px;line-height:1.6;white-space:pre-line}
.msg.user{align-self:flex-end;background:rgba(79,247,176,.12);border:1px solid rgba(79,247,176,.25)}
.msg.bot{align-self:flex-start;background:rgba(88,170,255,.12);border:1px solid rgba(88,170,255,.22)}
.speaker{display:block;margin-bottom:6px;color:#ffcb65;font-size:10px;text-transform:uppercase;letter-spacing:.5px;font-family:'IBM Plex Mono',monospace}
.quick-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.quick-row button{margin-top:0;padding:8px 10px;font-size:11px}
.answer-form{display:flex;gap:8px;align-items:center}
.answer-form input{flex:1}
@media (max-width: 860px){.hero{grid-template-columns:1fr}.answer-form{flex-direction:column;align-items:stretch}}
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
<div class="chips">
  <div class="chip">Operator: {{ user }}</div>
  <div class="chip">Score: {{ score }}</div>
  <div class="chip">Attempts: {{ attempts }}</div>
  <div class="chip">Topic: {{ level.topic }}</div>
</div>
<div class="hero">
  <div class="section">
    <p><b>Mission brief:</b> {{ level.question }}</p>
    <small>Answer in simple words. The assistant can coach you without spoiling the flow unless you push for a direct answer.</small>
    <div class="chips">
      <div class="chip">Recon</div>
      <div class="chip">Detect</div>
      <div class="chip">Contain</div>
      <div class="chip">Recover</div>
    </div>
    <form method="post" action="/ctf/submit" class="answer-form">
      <input name="answer" placeholder="Enter your answer">
      <button type="submit">Submit</button>
    </form>
    <div class="cta">
      <form method="get" action="/ctf">
        <input type="hidden" name="show_hint" value="1">
        <button type="submit">Show Hint</button>
      </form>
      <form method="post" action="/ctf/insight">
        <button type="submit">Get AI Insight</button>
      </form>
    </div>
    {% if show_hint %}<p><b>Hint:</b> {{ level.hint }}</p>{% endif %}
    {% if message %}<p class="{{ 'ok' if success else 'bad' }}">{{ message }}</p>{% endif %}
    {% if ai_text %}<div class="ai"><b>AI Insight:</b> {{ ai_text }}</div>{% endif %}
  </div>
  <div class="section">
    <b>CTF Chatbot</b>
    <div style="margin-top:8px;">
      <select id="ctfTutorMode">
        <option value="beginner">Tutor: Beginner</option>
        <option value="intermediate" selected>Tutor: Intermediate</option>
        <option value="expert">Tutor: Expert</option>
      </select>
    </div>
  <div class="quick-row">
    <button type="button" onclick="sendPreset('Hi')">Hi</button>
    <button type="button" onclick="sendPreset('Explain this challenge in plain English')">Explain</button>
    <button type="button" onclick="sendPreset('Give me a safe hint for the next step')">Hint</button>
  </div>
  <div id="ctfChatLog" class="chat-log"></div>
  <div style="display:flex;gap:6px;margin-top:8px;">
    <input id="ctfChatInput" placeholder="Ask: how to solve this level safely?">
    <button type="button" onclick="sendCtcChat()">Ask</button>
  </div>
</div>
</div>
<a href="/ctf/scoreboard">View scoreboard</a> |
<a href="/learn/maze">Back to maze</a>
</div></div>
<script>
function esc(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
function appendCtfMessage(speaker, text, role) {
  const log = document.getElementById('ctfChatLog');
  const entry = document.createElement('div');
  entry.className = `msg ${role}`;
  entry.innerHTML = `<span class="speaker">${esc(speaker)}</span><div>${esc(text)}</div>`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}
function initCtfChat() {
  const log = document.getElementById('ctfChatLog');
  if (!log) return;
  log.innerHTML = '';
  appendCtfMessage('Bot', 'Ask me about the challenge, the technique, or the safest reasoning path to the answer.', 'bot');
}
async function sendCtcChat() {
  const input = document.getElementById('ctfChatInput');
  const msg = (input.value || '').trim();
  if (!msg) return;
  appendCtfMessage('You', msg, 'user');
  input.value = "";
  const res = await fetch('/ctf/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg})
  });
  const data = await res.json();
  appendCtfMessage('Bot', data.reply || 'No response', 'bot');
}
function sendPreset(text) {
  document.getElementById('ctfChatInput').value = text;
  sendCtcChat();
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
  initCtfChat();
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

TECHNIQUE_KNOWLEDGE = {
    "T1059": {
        "name": "Command and Scripting Interpreter",
        "telemetry": "Process creation logs, command-line arguments, parent-child process lineage.",
        "detection": "Flag unusual interpreter parents and encoded/obfuscated script execution.",
        "response": "Terminate malicious script trees and block unsigned interpreter usage where feasible.",
    },
    "T1003": {
        "name": "OS Credential Dumping",
        "telemetry": "EDR memory access, LSASS access alerts, privileged token usage.",
        "detection": "Detect non-standard LSASS memory reads and known dump-tool behavior.",
        "response": "Isolate impacted host, rotate exposed credentials, and enforce LSASS protection.",
    },
    "T1021": {
        "name": "Remote Services",
        "telemetry": "Remote logon events, RDP/SMB/WMI auth logs, east-west flow metadata.",
        "detection": "Identify abnormal admin logon spread and service creation from pivot hosts.",
        "response": "Cut lateral channels, revoke active sessions, and restrict remote admin paths.",
    },
    "T1041": {
        "name": "Exfiltration Over C2 Channel",
        "telemetry": "Egress network logs, DNS/proxy logs, data transfer volume baselines.",
        "detection": "Alert on unusual outbound destinations, timing, and transfer spikes.",
        "response": "Block destination, isolate exfil source, and preserve transfer evidence.",
    },
    "T1047": {
        "name": "Windows Management Instrumentation",
        "telemetry": "WMI event logs, remote process creation, admin account activity.",
        "detection": "Look for WMI execution from atypical hosts/accounts and suspicious parent commands.",
        "response": "Disable abusive WMI channels, rotate compromised admin accounts, tighten WMI ACLs.",
    },
    "T1053": {
        "name": "Scheduled Task/Job",
        "telemetry": "Task scheduler create/update logs and startup persistence deltas.",
        "detection": "Alert on hidden/new recurring tasks with uncommon command payloads.",
        "response": "Remove malicious tasks, block re-creation vectors, and validate startup integrity.",
    },
    "T1078": {
        "name": "Valid Accounts",
        "telemetry": "Identity provider sign-ins, MFA events, session token usage.",
        "detection": "Detect unusual geolocation, impossible travel, and atypical admin behavior.",
        "response": "Revoke sessions/tokens, force credential reset, enforce conditional access.",
    },
    "T1078.004": {
        "name": "Valid Accounts: Cloud Accounts",
        "telemetry": "Cloud control plane auth logs, API key usage, IAM changes.",
        "detection": "Detect sign-ins from rare ASNs/devices and high-risk API activity.",
        "response": "Disable compromised cloud principals and rotate key material immediately.",
    },
    "T1098": {
        "name": "Account Manipulation",
        "telemetry": "IAM policy change logs, role assignments, mailbox/app permissions.",
        "detection": "Flag privilege grants and persistence changes outside approved windows.",
        "response": "Rollback unauthorized IAM changes and review all derived access paths.",
    },
    "T1110": {
        "name": "Brute Force",
        "telemetry": "Authentication failure bursts, lockout events, source IP patterns.",
        "detection": "Correlate repeated failures across accounts and protocol endpoints.",
        "response": "Apply rate limits/lockouts, block offending sources, increase MFA enforcement.",
    },
    "T1190": {
        "name": "Exploit Public-Facing Application",
        "telemetry": "WAF logs, HTTP error spikes, unusual request payload patterns.",
        "detection": "Detect exploit-like request sequences and post-exploit command execution.",
        "response": "Block exploit path, patch vulnerable service, rotate service credentials.",
    },
    "T1486": {
        "name": "Data Encrypted for Impact",
        "telemetry": "Mass file rename/write events, shadow copy deletion, backup tamper logs.",
        "detection": "Alert on rapid encryption-like IO behavior and ransomware precursor commands.",
        "response": "Immediate host isolation, kill encryption process, protect/air-gap backup channels.",
    },
    "T1566": {
        "name": "Phishing",
        "telemetry": "Email security logs, URL click telemetry, attachment detonation results.",
        "detection": "Detect suspicious sender/domain patterns and malicious payload execution chain.",
        "response": "Quarantine campaign emails, block indicators, and reset compromised identities.",
    },
    "T1567": {
        "name": "Exfiltration Over Web Service",
        "telemetry": "Proxy/SaaS logs, cloud upload events, abnormal external sharing.",
        "detection": "Detect high-volume uploads to rare external services and abnormal sharing changes.",
        "response": "Revoke sharing links/tokens, block destination service, and preserve transfer evidence.",
    },
}

ATTACK_PLAYBOOKS = [
    {
        "id": "wsl_multi_system_burst",
        "name": "WSL Multi-System Burst",
        "required": ["T1059", "T1078", "T1021", "T1041"],
        "min_match": 2,
        "severity": "HIGH",
        "why": "WSL command execution combined with valid-account reuse, lateral movement, and outbound transfer suggests a red user fanning out across multiple systems.",
        "telemetry": "Windows wsl.exe launches, Linux shell history, remote service auth logs, east-west flow logs, and egress monitoring.",
        "detection": "Correlate WSL or bash activity with multi-host admin access, concurrent remote sessions, and unusual outbound transfer patterns.",
        "response": "Contain the WSL-linked endpoint first, revoke reused credentials, restrict remote administration paths, and validate segmentation between affected systems.",
    },
    {
        "id": "ransomware_chain",
        "name": "Ransomware Progression",
        "required": ["T1059", "T1003", "T1021", "T1486"],
        "min_match": 2,
        "severity": "CRITICAL",
        "why": "Execution + credential access + lateral movement + encryption strongly indicate ransomware staging.",
        "telemetry": "EDR process lineage, LSASS access events, remote admin logons, mass file write anomalies.",
        "detection": "Correlate script execution -> credential dumping -> remote service spread -> encryption behavior.",
        "response": "Isolate impacted hosts, disable compromised admin accounts, block lateral protocols, protect backups.",
    },
    {
        "id": "cloud_account_takeover",
        "name": "Cloud Account Takeover",
        "required": ["T1078.004", "T1098", "T1567"],
        "min_match": 2,
        "severity": "HIGH",
        "why": "Compromised cloud identity plus permission changes and outbound web transfer indicates takeover + theft risk.",
        "telemetry": "Cloud sign-ins, IAM policy drift, token issuance, SaaS upload/sharing logs.",
        "detection": "Detect risky sign-in -> IAM manipulation -> unusual data movement sequence.",
        "response": "Revoke sessions/keys, rollback IAM changes, enforce conditional access, investigate shared resources.",
    },
    {
        "id": "phishing_to_identity_abuse",
        "name": "Phishing-Led Identity Compromise",
        "required": ["T1566", "T1078", "T1098"],
        "min_match": 2,
        "severity": "HIGH",
        "why": "Phishing followed by account abuse and persistence changes reflects active identity compromise.",
        "telemetry": "Email gateway events, sign-in telemetry, MFA change logs, account modification logs.",
        "detection": "Chain suspicious email interaction with high-risk sign-ins and identity configuration changes.",
        "response": "Contain mailbox/session abuse, reset credentials, remove unauthorized account persistence changes.",
    },
    {
        "id": "external_app_exploit",
        "name": "Public-Facing App Exploitation",
        "required": ["T1190", "T1059", "T1041"],
        "min_match": 2,
        "severity": "HIGH",
        "why": "Service exploit followed by command execution and outbound transfer suggests active post-exploit intrusion.",
        "telemetry": "WAF and web server logs, process creation on app hosts, outbound egress logs.",
        "detection": "Correlate exploit signatures with new shell execution and abnormal destination traffic.",
        "response": "Block exploit vectors, patch affected service, isolate app host, rotate service credentials/tokens.",
    },
    {
        "id": "remote_admin_abuse",
        "name": "Remote Administration Abuse",
        "required": ["T1047", "T1021", "T1078"],
        "min_match": 2,
        "severity": "MEDIUM",
        "why": "Remote management execution plus lateral access patterns indicate operator-driven intrusion movement.",
        "telemetry": "WMI activity, privileged auth events, remote service creation, endpoint command logs.",
        "detection": "Identify unusual management account behavior across hosts and remote execution chains.",
        "response": "Restrict admin channels, rotate privileged credentials, enforce just-in-time and MFA controls.",
    },
]

WSL_MULTI_SYSTEM_ADVERSARY = {
    "id": "9e5ec39b-c0f8-4f65-a7f3-6d8d7f1a9a31",
    "name": "WSL Red User Multi-System Adversary",
    "platform": "WSL / Linux",
    "operation_mode": "Concurrent multi-agent operation",
    "summary": "Lab-safe adversary model for a red user operating from a WSL foothold and simulating coordinated attacks across multiple systems in the same CALDERA operation.",
    "caldera_file": "data/adversaries/9e5ec39b-c0f8-4f65-a7f3-6d8d7f1a9a31.yml",
    "phases": [
        {
            "name": "WSL execution foothold",
            "goal": "Simulate operator command execution from WSL with full telemetry enabled.",
            "techniques": ["T1059"],
        },
        {
            "name": "Credential or session reuse",
            "goal": "Emulate controlled access expansion with approved lab identities.",
            "techniques": ["T1078", "T1078.004"],
        },
        {
            "name": "Multi-system fan-out",
            "goal": "Run concurrent remote admin or lateral movement actions against more than one agent.",
            "techniques": ["T1021", "T1047"],
        },
        {
            "name": "Collection and controlled egress",
            "goal": "Generate safe exfiltration-style telemetry for blue-team response practice.",
            "techniques": ["T1041", "T1567"],
        },
    ],
    "operation_steps": [
        "Register or reuse a WSL-backed agent and group it with the Windows/Linux lab systems you want in the same operation.",
        "Create one red-team operation that targets multiple agents so behaviors appear in parallel instead of one host at a time.",
        "Keep abilities simulation-safe: discovery, credential-use simulation, lateral movement emulation, and controlled exfiltration signals only.",
        "Use the dashboard to track per-target risk, likely attack chains, and chatbot guidance for the selected attack focus.",
    ],
    "defense_priorities": [
        "Monitor both Windows and WSL process chains, especially wsl.exe launching bash or Python with network follow-on activity.",
        "Apply least privilege, MFA, and just-in-time admin access for accounts that can touch multiple systems.",
        "Segment east-west traffic so one compromised WSL workstation cannot freely reach application and database tiers.",
        "Alert on unusual remote administration bursts, credential reuse, and new outbound destinations from dual-use admin hosts.",
    ],
}


def get_ctf_state(user):
    seed = ctf_progress.get(user, {"level_index": 0, "score": 0, "attempts": 0, "chat_attempts": 0})
    owner = session.get("ctf_state_user")
    state = session.get("ctf_state")
    if owner != user or not isinstance(state, dict):
        state = dict(seed)
        session["ctf_state_user"] = user
        session["ctf_state"] = state
        session.modified = True
    if "chat_attempts" not in state:
        state["chat_attempts"] = 0
    ctf_progress[user] = dict(state)
    return state


def save_ctf_state(user, state):
    session["ctf_state_user"] = user
    session["ctf_state"] = state
    session.modified = True
    ctf_progress[user] = dict(state)


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


def _caldera_headers():
    if not CALDERA_API_KEY:
        return {}
    return {"KEY": CALDERA_API_KEY, "Content-Type": "application/json"}


from functools import wraps


def unwrap_items(payload, preferred_keys=("agents", "operations", "items", "data")):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in preferred_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

        for value in payload.values():
            if isinstance(value, list):
                return value

    return []


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _agent_status(agent, now=None):
    now = now or datetime.now(timezone.utc)
    last_seen = _parse_iso_datetime(agent.get("last_seen"))
    if not last_seen:
        return "unknown"

    sleep_min = int(agent.get("sleep_min") or 0)
    sleep_max = int(agent.get("sleep_max") or 0)
    watchdog = int(agent.get("watchdog") or 0)
    elapsed_ms = max(0, int((now - last_seen).total_seconds() * 1000))
    is_alive = elapsed_ms < (sleep_max * 1000)

    if elapsed_ms <= 60000 and sleep_min == 3 and sleep_max == 3 and watchdog == 1:
        return "pending kill"
    return "alive" if (elapsed_ms <= 60000 or is_alive) else "dead"


def _caldera_request(path):
    res = requests.get(
        f"{CALDERA_URL}{path}",
        headers=_caldera_headers(),
        timeout=CALDERA_TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def get_caldera_agents():
    payload = _caldera_request("/api/v2/agents")
    agents = unwrap_items(payload, ("agents", "items", "data"))
    now = datetime.now(timezone.utc)
    enriched = []

    for agent in agents:
        if not isinstance(agent, dict) or not agent.get("paw"):
            continue
        agent_copy = dict(agent)
        status = _agent_status(agent_copy, now=now)
        agent_copy["status"] = status
        agent_copy["is_alive"] = status in {"alive", "pending kill"}
        agent_copy["display_name"] = agent_copy.get("display_name") or agent_copy.get("paw")
        enriched.append(agent_copy)

    enriched.sort(
        key=lambda item: (
            {"alive": 0, "pending kill": 1, "dead": 2}.get(item.get("status"), 3),
            item.get("last_seen") or "",
        ),
        reverse=False,
    )
    return enriched


def get_caldera_operations():
    payload = _caldera_request("/api/v2/operations")
    operations = unwrap_items(payload, ("operations", "items", "data"))
    return [item for item in operations if isinstance(item, dict)]


def _is_public_ip(ip_value):
    try:
        parsed = ipaddress.ip_address(str(ip_value))
    except ValueError:
        return False

    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_reserved
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_unspecified
    )


def _extract_agent_ips(agent):
    values = []
    for raw in agent.get("host_ip_addrs") or []:
        value = str(raw).strip()
        if value and value not in values:
            values.append(value)
    return values


def _parse_geo_payload(ip_address_value, payload):
    if not isinstance(payload, dict):
        return None

    lat = payload.get("latitude", payload.get("lat"))
    lon = payload.get("longitude", payload.get("lon"))
    if lat in (None, "") or lon in (None, ""):
        return None

    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError):
        return None

    return {
        "ip": ip_address_value,
        "latitude": latitude,
        "longitude": longitude,
        "city": payload.get("city") or payload.get("town") or "",
        "region": payload.get("region") or payload.get("region_name") or payload.get("state_prov") or "",
        "country": payload.get("country_name") or payload.get("country") or payload.get("country_code") or "",
        "postal": payload.get("postal") or payload.get("zip") or "",
        "provider": GEOIP_PROVIDER_LABEL,
    }


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_analyst_location(latitude, longitude, label="", source="manual", accuracy=None, approximate=False, query=""):
    latitude = _parse_float(latitude)
    longitude = _parse_float(longitude)
    if latitude is None or longitude is None:
        return None

    return {
        "latitude": latitude,
        "longitude": longitude,
        "label": label or "Analyst console",
        "source": source or "manual",
        "accuracy": _parse_float(accuracy),
        "approximate": bool(approximate),
        "query": query or "",
    }


def geolocate_ip(ip_value):
    ip_value = str(ip_value or "").strip()
    if not ip_value:
        return None
    if not _is_public_ip(ip_value):
        return {
            "ip": ip_value,
            "private": True,
            "reason": "Private or internal address",
        }

    now = time.time()
    cached = geo_cache.get(ip_value)
    if cached and (now - cached["cached_at"]) < GEOIP_CACHE_SECONDS:
        return cached["value"]

    try:
        url = GEOIP_URL.format(ip=ip_value, api_key=GEOIP_API_KEY)
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        parsed = _parse_geo_payload(ip_value, res.json())
    except Exception:
        parsed = None

    geo_cache[ip_value] = {"cached_at": now, "value": parsed}
    return parsed


def geocode_place(query):
    query = str(query or "").strip()
    if not query:
        return None

    cache_key = f"__geocode__::{query.lower()}"
    now = time.time()
    cached = geo_cache.get(cache_key)
    if cached and (now - cached["cached_at"]) < GEOIP_CACHE_SECONDS:
        return cached["value"]

    result = None
    try:
        res = requests.get(
            GEOCODE_URL,
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": GEOCODE_USER_AGENT},
            timeout=8,
        )
        res.raise_for_status()
        payload = res.json()
        if isinstance(payload, list) and payload:
            item = payload[0]
            result = _build_analyst_location(
                item.get("lat"),
                item.get("lon"),
                label=item.get("display_name") or query,
                source="place_search",
                approximate=False,
                query=query,
            )
    except Exception:
        result = None

    geo_cache[cache_key] = {"cached_at": now, "value": result}
    return result


def lookup_public_ip():
    cache_key = "__public_ip__"
    now = time.time()
    cached = geo_cache.get(cache_key)
    if cached and (now - cached["cached_at"]) < GEOIP_CACHE_SECONDS:
        return cached["value"]

    try:
        res = requests.get(PUBLIC_IP_LOOKUP_URL, timeout=8)
        res.raise_for_status()
        payload = res.json()
        public_ip = str(payload.get("ip") or "").strip()
    except Exception:
        public_ip = ""

    geo_cache[cache_key] = {"cached_at": now, "value": public_ip}
    return public_ip


def get_saved_analyst_location():
    payload = session.get("analyst_location")
    if not isinstance(payload, dict):
        return None
    return _build_analyst_location(
        payload.get("latitude"),
        payload.get("longitude"),
        label=payload.get("label") or "Analyst console",
        source=payload.get("source") or "manual",
        accuracy=payload.get("accuracy"),
        approximate=payload.get("approximate"),
        query=payload.get("query") or "",
    )


def resolve_analyst_location():
    saved = get_saved_analyst_location()
    if saved:
        return saved

    env_lat = _parse_float(ANALYST_LATITUDE)
    env_lon = _parse_float(ANALYST_LONGITUDE)
    if env_lat is not None and env_lon is not None:
        return _build_analyst_location(
            env_lat,
            env_lon,
            label="Configured analyst location",
            source="env_coordinates",
            approximate=False,
        )

    if ANALYST_LOCATION_QUERY:
        return geocode_place(ANALYST_LOCATION_QUERY)

    return None


def build_live_overview():
    raw_agents = get_caldera_agents()
    operations = get_caldera_operations()
    operation_summaries = []
    map_markers = []
    agents = []
    analyst_location = resolve_analyst_location()

    for op in operations:
        chain = op.get("chain") or []
        completed_links = sum(1 for link in chain if isinstance(link, dict) and link.get("status") == 0)
        failed_links = sum(1 for link in chain if isinstance(link, dict) and link.get("status") not in (0, None))
        operation_summaries.append(
            {
                "id": op.get("id"),
                "name": op.get("name") or op.get("adversary", {}).get("name") or "Operation",
                "state": op.get("state") or "unknown",
                "adversary": (op.get("adversary") or {}).get("name") or "unknown",
                "agent_count": len(op.get("agents") or []),
                "host_group": op.get("group") or "unknown",
                "chain_count": len(chain),
                "completed_links": completed_links,
                "failed_links": failed_links,
                "start": op.get("start"),
                "finish": op.get("finish"),
            }
        )

    for agent in raw_agents:
        candidate_ips = _extract_agent_ips(agent)
        geo = None
        geo_source = ""
        for ip_value in candidate_ips:
            geo = geolocate_ip(ip_value)
            if geo and not geo.get("private"):
                geo_source = "agent_ip"
                break
        if (not geo or geo.get("private")) and candidate_ips and analyst_location:
            geo = {
                "ip": candidate_ips[0],
                "latitude": analyst_location["latitude"],
                "longitude": analyst_location["longitude"],
                "city": analyst_location.get("label") or "Analyst console",
                "region": "",
                "country": "",
                "postal": "",
                "provider": analyst_location.get("source") or "analyst_console",
                "approximate": bool(analyst_location.get("approximate")),
                "reason": "Private or WSL agent mapped to the analyst console location for local-lab visibility.",
            }
            geo_source = "analyst_console"
        if (not geo or geo.get("private")) and candidate_ips:
            public_ip = lookup_public_ip()
            public_geo = geolocate_ip(public_ip) if public_ip else None
            if public_geo and not public_geo.get("private"):
                geo = dict(public_geo)
                geo["approximate"] = True
                geo["reason"] = "Agent only exposed private/WSL IPs, so this uses the host public egress location."
                geo_source = "host_public_ip"
        if geo and not geo.get("private"):
            marker = dict(geo)
            marker["paw"] = agent.get("paw")
            marker["host"] = agent.get("host")
            marker["status"] = agent.get("status")
            marker["display_name"] = agent.get("display_name")
            marker["username"] = agent.get("username")
            marker["platform"] = agent.get("platform")
            marker["group"] = agent.get("group")
            marker["privilege"] = agent.get("privilege")
            marker["trusted"] = bool(agent.get("trusted"))
            marker["last_seen"] = agent.get("last_seen")
            marker["candidate_ips"] = candidate_ips
            marker["source"] = geo_source or "agent_ip"
            map_markers.append(marker)
        agents.append(
            {
                "paw": agent.get("paw"),
                "display_name": agent.get("display_name"),
                "host": agent.get("host"),
                "username": agent.get("username"),
                "platform": agent.get("platform"),
                "group": agent.get("group"),
                "trusted": bool(agent.get("trusted")),
                "status": agent.get("status"),
                "privilege": agent.get("privilege"),
                "last_seen": agent.get("last_seen"),
                "link_count": len(agent.get("links") or []),
                "candidate_ips": candidate_ips,
                "geolocation": geo,
                "geolocation_source": geo_source,
            }
        )

    alive_count = sum(1 for agent in agents if agent.get("status") in {"alive", "pending kill"})
    dead_count = sum(1 for agent in agents if agent.get("status") == "dead")
    untrusted_count = sum(1 for agent in agents if not agent.get("trusted"))

    return {
        "agents": agents,
        "operations": operation_summaries,
        "stats": {
            "agent_total": len(agents),
            "agent_alive": alive_count,
            "agent_dead": dead_count,
            "agent_untrusted": untrusted_count,
            "operation_total": len(operation_summaries),
            "operation_running": sum(1 for op in operation_summaries if str(op.get("state", "")).lower() not in {"finished", "cleanup", "out_of_time", "closed", "archived"}),
            "mapped_attackers": len(map_markers),
        },
        "map_markers": map_markers,
        "analyst_location": analyst_location,
    }

def retry_on_failure(max_retries=3, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt == max_retries - 1:
                        raise
                    wait = backoff ** attempt
                    time.sleep(wait)
                    print(f"[RETRY] {func.__name__} attempt {attempt+1}/{max_retries} after {wait}s: {exc}")
            raise last_exc
        return wrapper
    return decorator


@retry_on_failure(max_retries=3, backoff=1.5)
def fetch_caldera_status():
    status = {
        "configured": bool(CALDERA_URL and CALDERA_API_KEY),
        "connected": False,
        "url": CALDERA_URL,
        "operations": 0,
        "agents": 0,
        "alive_agents": 0,
        "dead_agents": 0,
        "untrusted_agents": 0,
        "neo4j_agents": 0,
        "abilities": 0,
        "error": None,
        "sync_warning": None,
        "cache_bust": int(time.time()),
        "retry_count": 0
    }

    if not status["configured"]:
        status["error"] = "Missing CALDERA_URL or CALDERA_API_KEY."
        status["retry_count"] = 0
        return status

    try:
        operations = get_caldera_operations()
        agents = get_caldera_agents()
        abilities_res = requests.get(
            f"{CALDERA_URL}/api/v2/abilities",
            headers=_caldera_headers(),
            timeout=CALDERA_TIMEOUT,
        )

        abilities_res.raise_for_status()

        status["connected"] = True
        status["operations"] = len(operations)
        status["agents"] = len(agents)
        status["alive_agents"] = sum(1 for agent in agents if agent.get("status") in {"alive", "pending kill"})
        status["dead_agents"] = sum(1 for agent in agents if agent.get("status") == "dead")
        status["untrusted_agents"] = sum(1 for agent in agents if not agent.get("trusted"))
        status["abilities"] = len(abilities_res.json() or [])
        status["retry_count"] = 0
    except requests.exceptions.Timeout:
        status["error"] = "Caldera API timeout. Check connectivity."
        status["retry_count"] = 3
    except requests.exceptions.RequestException as exc:
        status["error"] = f"Caldera API error ({exc.response.status_code if hasattr(exc, 'response') else 'unknown'}): {str(exc)[:100]}"
        status["retry_count"] = 3
    except Exception as exc:
        status["error"] = f"Unexpected Caldera error: {str(exc)}"
        status["retry_count"] = 3

    # Count Neo4j agents
    try:
        with driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (a:Agent)
                RETURN COUNT(a) AS count
            """)
            neo4j_count = result.single()["count"] or 0
        status["neo4j_agents"] = int(neo4j_count)

        if status["neo4j_agents"] > status["agents"]:
            status["sync_warning"] = f"Stale data detected! Neo4j: {status['neo4j_agents']} agents vs Caldera: {status['agents']}. Check sync_worker/graph_writer."
    except Exception as neo_exc:
        status["neo4j_error"] = f"Neo4j count failed: {str(neo_exc)}"

    return status



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
        if role == "assistant":
            gemini_role = "model"
        else:
            gemini_role = "user"
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


def call_gemini_messages(messages, max_tokens=220, temperature=0.35):
    if not GEMINI_API_KEY:
        return None
    try:
        payload = {
            "contents": _messages_to_gemini_payload(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "x-goog-api-client": "cloud-attack-lab/1.0",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        res.raise_for_status()
        payload = res.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            return None
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        reply = "".join(text_parts).strip()
        return reply or None
    except Exception:
        return None


def call_gemini(system_prompt, user_prompt, max_tokens=220):
    return call_gemini_messages(
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

    reply = call_gemini_messages(messages, max_tokens=max_tokens)
    if reply:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        _set_chat_history(channel, history)
    return reply


def _smalltalk_reply(message, context=None):
    msg = (message or "").strip().lower()
    if not msg:
        return None

    context = context or {}
    risk = context.get("risk") or "LOW"
    techniques = ", ".join((context.get("techniques") or [])[:3]) or "no mapped techniques yet"

    if any(token == msg or token in msg for token in GREETING_TOKENS):
        return (
            "Hello. I’m your security copilot for this lab. "
            f"Right now I’m seeing risk at {risk}, with {techniques}. "
            "I can help you read the graph, explain attacks, suggest containment steps, and summarize what CALDERA is doing."
        )

    if any(token in msg for token in THANKS_TOKENS):
        return "You’re welcome. If you want, ask me to summarize the current attack path, explain a technique, or suggest the next containment step."

    if "who are you" in msg or "what can you do" in msg or msg == "help":
        return (
            "I’m an AI security assistant connected to your dashboard context. "
            "I can explain agent activity, attack paths, MITRE techniques, defensive actions, and the live CALDERA state in simple language."
        )

    return None


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
    smalltalk = _smalltalk_reply(msg, context)
    if smalltalk:
        return smalltalk
    if domain == "soc":
        risk = context.get("risk", "LOW")
        techniques = context.get("techniques", [])
        top = ", ".join(techniques[:3]) if techniques else "No mapped techniques yet"
        agent_total = context.get("agent_total", 0)
        operation_total = context.get("operation_total", 0)
        return (
            f"Topic: SOC Incident Tutoring\n"
            f"Question: {msg or 'How do I handle this incident?'}\n\n"
            f"What this means:\n"
            f"- Current risk is {risk}.\n"
            f"- CALDERA currently shows {agent_total} agent(s) and {operation_total} operation(s).\n"
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
    if domain == "defense":
        risk = context.get("risk", "LOW")
        focus_title = context.get("focus_title", "current incident")
        focus_summary = context.get("focus_summary", "No specific attack focus selected.")
        recommendation = context.get("recommendation", "Start with containment and evidence preservation.")
        scenario = context.get("scenario", "No strong scenario match yet")
        techniques = context.get("techniques", [])
        top = ", ".join(techniques[:4]) if techniques else "No mapped techniques yet"
        return (
            f"Topic: Interactive Defense Advisor\n"
            f"Question: {msg or 'How should I defend against this attack?'}\n\n"
            f"Selected focus: {focus_title}\n"
            f"Context: {focus_summary}\n"
            f"Likely scenario: {scenario}\n"
            f"Risk: {risk}\n"
            f"Observed techniques: {top}\n\n"
            "Suggested defense flow:\n"
            "1) Contain the most exposed host, account, or path first.\n"
            "2) Pull the exact telemetry that proves scope and impact.\n"
            "3) Block the attacker path without destroying forensic evidence.\n"
            "4) Harden the weak control that allowed the movement.\n"
            "5) Validate by checking that the same path cannot be replayed.\n\n"
            f"Priority recommendation:\n- {recommendation}"
        )
    return (
        f"Topic: Security Tutor\nQuestion: {msg or 'Explain this topic'}\n\n"
        "Use this flow: Understand objective -> Contain risk -> Collect evidence -> Fix root cause -> Validate controls."
    )


def tutor_response(channel, user_message, context_block="", teaching_goal="security operations", mode_override=None):
    system_prompt = (
        "You are an expert cybersecurity tutor and incident-response copilot. "
        "Sound warm, natural, and conversational, like an LLM assistant talking directly to the user. "
        "If the user greets you, greet them back naturally and briefly explain how you can help. "
        "Teach thoroughly but clearly. Explain concepts from basics to advanced, define terms, give examples, and provide practical steps. "
        "When useful, include: What, Why, How, Common Mistakes, and Quick Checklist. "
        "If the user asks a direct action question, still teach the reasoning behind the action."
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


def _ctf_required_attempts(mode, level_number):
    mode = _normalize_mode(mode)
    if mode == "beginner":
        return 1
    if mode == "expert":
        return 6
    return 4


def _ctf_small_hint(level, attempts, mode):
    topic = level.get("topic", "the core command intent")
    base_hint = level.get("hint", "Think about the exact command this task is testing.")
    answer = (level.get("answer") or "").strip()
    prefix = answer[:1] if answer else ""
    length = len(answer) if answer else 0

    mode = _normalize_mode(mode)
    if mode == "expert":
        if attempts <= 2:
            return (
                f"Twisted hint: this level is about {topic}; pick the tiniest command "
                "that reveals identity, location, or state without changing anything."
            )
        if attempts <= 4:
            return (
                "Twisted hint: think of the command defenders run first in triage "
                "before touching logs, processes, or network flows."
            )
        return f"Twisted hint: first letter is `{prefix}`, length is {length}."

    if mode == "intermediate":
        if attempts <= 1:
            return f"Direct hint: focus on {topic}."
        if attempts == 2:
            return f"Direct hint: {base_hint}"
        return f"Direct hint: answer starts with `{prefix}` and has {length} characters."

    return f"Hint: {base_hint}"


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
        "history": ["Mission started. Review the objective card and launch the first mitigation action."],
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
        "mission_state": "complete" if state["finished"] else ("active" if scenario else "idle"),
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

    backend_status = fetch_caldera_status()
    try:
        live_overview = build_live_overview()
    except Exception:
        live_overview = {"agents": [], "operations": [], "stats": {}, "map_markers": [], "analyst_location": resolve_analyst_location()}
    try:
        graph = fetch_graph_data()
        db_error = None
    except Exception:
        graph = empty_graph()
        db_error = "Unable to load graph data from Neo4j. Check DB connection."

    return render_template(
        "index.html",
        graph=graph,
        db_error=db_error,
        backend_status=backend_status,
        live_overview=live_overview,
    )


@app.route("/api/backend_status")
def api_backend_status():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(fetch_caldera_status())


@app.route("/api/live_overview")
def api_live_overview():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(build_live_overview())
    except Exception as exc:
        return jsonify({"error": str(exc), "agents": [], "operations": [], "stats": {}, "map_markers": [], "analyst_location": resolve_analyst_location()}), 503


@app.route("/api/analyst_location", methods=["GET", "POST", "DELETE"])
def api_analyst_location():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "GET":
        return jsonify({"location": resolve_analyst_location()})

    if request.method == "DELETE":
        session.pop("analyst_location", None)
        session.modified = True
        return jsonify({"success": True, "location": resolve_analyst_location()})

    payload = request.get_json(silent=True) or {}
    location = None

    if payload.get("query"):
        location = geocode_place(payload.get("query"))
        if location:
            location["source"] = "place_search"

    if not location:
        location = _build_analyst_location(
            payload.get("latitude"),
            payload.get("longitude"),
            label=payload.get("label") or "Analyst console",
            source=payload.get("source") or "manual",
            accuracy=payload.get("accuracy"),
            approximate=payload.get("approximate"),
            query=payload.get("query") or "",
        )

    if not location:
        return jsonify({"error": "Provide valid coordinates or a place query."}), 400

    session["analyst_location"] = location
    session.modified = True
    return jsonify({"success": True, "location": location})


@app.route("/api/sync_status")
def api_sync_status():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    status = fetch_caldera_status()
    
    # Agent activity check
    try:
        with driver.session(database="neo4j") as db_session:
            active_query = """
            MATCH (a:Agent)
            WHERE coalesce(a.status, CASE WHEN coalesce(a.active, true) THEN 'alive' ELSE 'dead' END) IN ['alive', 'pending kill']
            RETURN COUNT(a) AS active_count
            """
            result = db_session.run(active_query)
            active_neo4j = result.single()["active_count"] or 0
            
            stale_query = """
            MATCH (a:Agent)
            WHERE coalesce(a.status, CASE WHEN coalesce(a.active, true) THEN 'alive' ELSE 'dead' END) = 'dead'
            RETURN COUNT(a) AS stale_count
            """
            result = db_session.run(stale_query)
            stale_neo4j = result.single()["stale_count"] or 0
    except Exception as exc:
        return jsonify({
            "error": f"Neo4j query failed: {str(exc)}",
            "neo4j_agents": 0,
            "active_neo4j": 0,
            "stale_neo4j": 0
        })
    
    return jsonify({
        "caldera_agents": status["agents"],
        "alive_caldera_agents": status.get("alive_agents", 0),
        "neo4j_agents": status["neo4j_agents"],
        "active_neo4j": int(active_neo4j),
        "stale_neo4j": int(stale_neo4j),
        "sync_healthy": status["agents"] == status["neo4j_agents"] and active_neo4j == status.get("alive_agents", 0),
        "diagnosis": "Neo4j count does not currently match CALDERA agent state" if status["neo4j_agents"] != status["agents"] or active_neo4j != status.get("alive_agents", 0) else "Sync appears healthy",
        "needs_cleanup": status["neo4j_agents"] != status["agents"]
    })


@app.route("/api/clean_neo4j", methods=["POST"])
def api_clean_neo4j():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        current_agent_ids = [agent.get("paw") for agent in get_caldera_agents() if agent.get("paw")]
        with driver.session(database="neo4j") as session:
            session.run("""
            MATCH (a:Agent)
            WHERE NOT a.agent_id IN $current_agent_ids
            DETACH DELETE a
            """, current_agent_ids=current_agent_ids)
            
            session.run("""
            MATCH (f:Fact)
            WHERE NOT (:Agent)-[:EXECUTED]->(f)
            DETACH DELETE f
            """)
            
            session.run("""
            MATCH (t:Technique)
            WHERE NOT (:Fact)-[:USES]->(t)
            DETACH DELETE t
            """)
            
            session.run("""
            MATCH (ta:Tactic)
            WHERE NOT (:Technique)-[:PART_OF]->(ta)
            DETACH DELETE ta
            """)
        
        return jsonify({
            "success": True,
            "message": "Neo4j cleaned: inactive agents, orphaned facts/techniques removed"
        })
    except Exception as exc:
        return jsonify({
            "error": f"Cleanup failed: {str(exc)}"
        }), 500



@app.route("/api/graph")
def api_graph():
    demo = request.args.get("demo") == "1"
    if demo:
        return jsonify({
            "nodes": [
                {"data": {"id": "agent1", "label": "wsl-operator", "type": "agent", "status": "alive"}},
                {"data": {"id": "fact1", "label": "whoami", "type": "fact", "technique": "T1059"}},
                {"data": {"id": "fact2", "label": "netstat -an", "type": "fact", "technique": "T1049"}}
            ],
            "edges": [
                {"data": {"id": "e1", "source": "agent1", "target": "fact1", "relation": "executed"}},
                {"data": {"id": "e2", "source": "fact1", "target": "fact2", "relation": "next"}}
            ],
            "summary": {"agent_count": 1, "fact_count": 2, "risk_score": 45, "risk_level": "ELEVATED"},
            "attack_paths": [{"target": "identity", "length": 2, "risk_score": 45}],
            "filters": {"agents": ["agent1"], "targets": ["identity"]},
            "techniques": [{"id": "T1059", "count": 1}, {"id": "T1049", "count": 1}],
            "meta": {"demo": True}
        })
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    agent_id = request.args.get("agent") or None
    target = request.args.get("target") or None
    agent_state = request.args.get("agent_state") or "all"
    cache_bust = request.args.get("t", int(time.time()))

    try:
        graph = fetch_graph_data(agent_id=agent_id, target=target, agent_state=agent_state)
        graph["meta"]["request_cache_bust"] = cache_bust
        return jsonify(graph)
    except Exception as exc:
        payload = empty_graph()
        payload["error"] = f"Neo4j query failed after retries: {str(exc)}"
        payload["error_type"] = "NEO4J_UNAVAILABLE"
        payload["retry_status"] = "exhausted"
        return jsonify(payload), 503


@app.route("/api/defense")
def api_defense():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    agent_id = request.args.get("agent") or None
    target = request.args.get("target") or None

    try:
        graph = fetch_graph_data(agent_id=agent_id, target=target)
        analysis = generate_defense_recommendations(graph)
        agent_profiles = build_agent_defense_profiles(graph)
        return jsonify(
            {
                "techniques": analysis.get("observed_techniques", []),
                "risk_level": analysis.get("risk_level", "LOW"),
                "matched_scenarios": analysis.get("matched_scenarios", []),
                "recommendations": analysis.get("recommendations", []),
                "agent_profiles": agent_profiles,
                "adversary_model": build_wsl_adversary_model(graph, analysis),
            }
        )
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
    incoming_agent_profile = data.get("agentProfile") or {}
    focus = data.get("focus") or {}
    focus_type = (focus.get("type") or "").strip() or "general"
    focus_title = (focus.get("title") or focus.get("name") or "").strip() or "General incident view"
    focus_summary = (focus.get("summary") or "").strip()
    focus_guidance = (focus.get("guidance") or "").strip()
    focus_target = (focus.get("target") or "").strip()
    focus_techniques = focus.get("techniques") or []

    smalltalk = _smalltalk_reply(message)
    if smalltalk:
        return jsonify(
            {
                "reply": smalltalk,
                "risk_level": "LOW",
                "top_techniques": [],
                "top_attack_path": {},
                "matched_scenarios": [],
            }
        )

    graph = fetch_graph_data(agent_id=agent_id, target=target)
    live_overview = build_live_overview()
    top_techniques = [t["id"] for t in graph.get("techniques", [])[:3]]
    risk = graph.get("summary", {}).get("risk_level", "LOW")
    top_path = (graph.get("attack_paths") or [{}])[0]
    top_path_target = top_path.get("target", "unknown")
    top_path_len = top_path.get("length", 0)
    top_path_risk = top_path.get("risk_score", 0)
    defense_analysis = generate_defense_recommendations(graph)
    agent_profiles = build_agent_defense_profiles(graph)
    selected_agent_profile = find_agent_profile(agent_profiles, agent_id or incoming_agent_profile.get("agent_id"))
    top_scenario = (defense_analysis.get("matched_scenarios") or [{}])[0]

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
            f"Likely scenario: {top_scenario.get('name', 'none')}\n"
            f"Scenario confidence: {int(top_scenario.get('confidence', 0) * 100)}\n"
            f"Scenario response focus: {top_scenario.get('response', 'N/A')}\n"
            f"Selected agent: {agent_id or 'all'}\n"
            f"Selected target: {target or 'all'}\n"
            f"Selected attack focus type: {focus_type}\n"
            f"Selected attack focus title: {focus_title}\n"
            f"Selected attack focus summary: {focus_summary or 'none'}\n"
            f"Selected attack focus guidance: {focus_guidance or 'none'}\n"
            f"Selected attack focus target: {focus_target or 'none'}\n"
            f"Selected attack focus techniques: {', '.join(focus_techniques) if focus_techniques else 'none'}\n"
            f"Selected agent profile: {(selected_agent_profile or {}).get('agent_id', 'none')}\n"
            f"Selected agent risk: {(selected_agent_profile or {}).get('risk_level', 'LOW')} {(selected_agent_profile or {}).get('risk_score', 0)}\n"
            f"Selected agent techniques: {', '.join((selected_agent_profile or {}).get('techniques', [])) if selected_agent_profile else 'none'}\n"
            f"Selected agent defenses: {' | '.join((selected_agent_profile or {}).get('recommendations', [])[:2]) if selected_agent_profile else 'none'}\n"
            f"Goal: explain and guide mitigation decisions."
        ),
        teaching_goal="SOC incident handling and mitigation",
    )

    if ai_reply:
        reply = ai_reply
    else:
        reply = fallback_coach(
            "soc",
            message,
            {
                "risk": risk,
                "techniques": top_techniques,
                "agent_total": (live_overview.get("stats") or {}).get("agent_total", 0),
                "operation_total": (live_overview.get("stats") or {}).get("operation_total", 0),
            },
        )

    return jsonify(
        {
            "reply": reply,
            "risk_level": risk,
            "top_techniques": top_techniques,
            "top_attack_path": top_path,
            "matched_scenarios": defense_analysis.get("matched_scenarios", []),
        }
    )


@app.route("/api/defense/advisor", methods=["POST"])
def api_defense_advisor():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    agent_id = data.get("agent")
    target = data.get("target")
    incoming_agent_profile = data.get("agentProfile") or {}
    focus = data.get("focus") or {}
    recommendation = (data.get("recommendation") or "").strip()

    focus_title = (focus.get("title") or focus.get("name") or "").strip() or "Current incident"
    focus_summary = (focus.get("summary") or "").strip() or "No specific attack focus selected."
    focus_guidance = (focus.get("guidance") or "").strip()
    focus_target = (focus.get("target") or "").strip()
    focus_techniques = focus.get("techniques") or []

    smalltalk = _smalltalk_reply(message)
    if smalltalk:
        return jsonify(
            {
                "reply": smalltalk,
                "risk_level": "LOW",
                "matched_scenarios": [],
                "recommendations": [],
            }
        )

    graph = fetch_graph_data(agent_id=agent_id, target=target)
    analysis = generate_defense_recommendations(graph)
    agent_profiles = build_agent_defense_profiles(graph)
    selected_agent_profile = find_agent_profile(agent_profiles, agent_id or incoming_agent_profile.get("agent_id"))
    top_scenario = (analysis.get("matched_scenarios") or [{}])[0]
    summary = graph.get("summary", {})
    top_techniques = analysis.get("observed_techniques", [])[:6]
    attack_paths = graph.get("attack_paths", [])

    ai_reply = tutor_response(
        "defense",
        message or "How should I defend against this attack right now?",
        context_block=(
            f"Domain: Interactive defense planning\n"
            f"Current risk: {summary.get('risk_level', 'LOW')} ({summary.get('risk_score', 0)}/100)\n"
            f"Selected focus title: {focus_title}\n"
            f"Selected focus summary: {focus_summary}\n"
            f"Selected focus guidance: {focus_guidance or 'none'}\n"
            f"Selected focus target: {focus_target or 'all'}\n"
            f"Selected focus techniques: {', '.join(focus_techniques) if focus_techniques else 'none'}\n"
            f"Selected recommendation: {recommendation or 'none'}\n"
            f"Likely scenario: {top_scenario.get('name', 'none')}\n"
            f"Scenario response: {top_scenario.get('response', 'N/A')}\n"
            f"Observed techniques: {', '.join(top_techniques) if top_techniques else 'none'}\n"
            f"Parallel attack paths: {len(attack_paths)}\n"
            f"Selected agent: {agent_id or 'all'}\n"
            f"Selected target filter: {target or 'all'}\n"
            f"Selected agent profile: {(selected_agent_profile or {}).get('agent_id', 'none')}\n"
            f"Selected agent recommendations: {' | '.join((selected_agent_profile or {}).get('recommendations', [])[:3]) if selected_agent_profile else 'none'}\n"
            "Answer as a defense advisor with practical sections for containment, detection, hardening, and validation."
        ),
        teaching_goal="interactive attack defense",
    )

    if ai_reply:
        reply = ai_reply
    else:
        reply = fallback_coach(
            "defense",
            message,
            {
                "risk": summary.get("risk_level", "LOW"),
                "focus_title": focus_title,
                "focus_summary": focus_summary,
                "recommendation": recommendation,
                "scenario": top_scenario.get("name", "none"),
                "techniques": top_techniques,
            },
        )

    return jsonify(
        {
            "reply": reply,
            "risk_level": summary.get("risk_level", "LOW"),
            "matched_scenarios": analysis.get("matched_scenarios", []),
            "recommendations": analysis.get("recommendations", []),
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

    ai_text = call_gemini(
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
    return jsonify(_maze_response(session["maze_state"], "Mission reset. Review the new incident brief and begin with reconnaissance."))


@app.route("/api/maze/level", methods=["POST"])
def api_maze_level():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    level = _normalize_maze_level(data.get("level"))
    session["maze_state"] = _new_maze_state(level)
    return jsonify(_maze_response(session["maze_state"], f"Difficulty set to {level}. A new incident is ready for triage."))


@app.route("/api/maze/command", methods=["POST"])
def api_maze_command():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    state = _get_maze_state()
    scenarios = _scenarios_for_level(state.get("level"))
    data = request.get_json(silent=True) or {}
    raw = (data.get("command") or "").strip().lower()
    if not raw:
        return jsonify(_maze_response(state, "Select a mission action from the deck or open the advanced console if you need it."))

    cmd = MAZE_COMMAND_ALIASES.get(raw, None)
    if cmd is None:
        return jsonify(_maze_response(state, "That action is not available in this mission. Use the action deck for the safest next move."))

    if cmd == "reset":
        session["maze_state"] = _new_maze_state()
        return jsonify(_maze_response(session["maze_state"], "Mission reset. Review the objective card and start with reconnaissance."))

    if cmd == "help":
        return jsonify(_maze_response(state, "Mitigation tools available: recon, logs, isolate, block, patch, rotate, verify, next, status, reset. The action deck shows the best move for the current incident."))

    if cmd == "status":
        return jsonify(_maze_response(state, f"Mission status: level {state['level']}, health {state['health']}, score {state['score']}, incidents contained {state['completed']} of {len(scenarios)}."))

    if state["finished"]:
        return jsonify(_maze_response(state, "All incidents have been contained. Reset the mission to run the exercise again."))

    scenario = _active_scenario(state)
    if not scenario:
        state["finished"] = True
        session["maze_state"] = state
        return jsonify(_maze_response(state, "Mission complete. Every incident in this run has been stabilized."))

    # Scenario completed, require explicit next
    if state["step_index"] >= len(scenario["steps"]):
        if cmd == "next":
            state["scenario_index"] += 1
            state["step_index"] = 0
            if state["scenario_index"] >= len(scenarios):
                state["finished"] = True
                state["history"].append("All attack scenarios mitigated.")
                session["maze_state"] = state
                return jsonify(_maze_response(state, "Mission complete. Great response speed and solid mitigation discipline."))
            next_scn = _active_scenario(state)
            out = f"New incident opened: {next_scn['name']} ({next_scn['technique']}). Begin with reconnaissance and evidence review."
            state["history"].append(out)
            session["maze_state"] = state
            return jsonify(_maze_response(state, out))
        return jsonify(_maze_response(state, "This incident is contained. Advance to the next incident when you are ready."))

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
            done_msg = f"Incident '{scenario['name']}' contained. Advance when you are ready."
            state["history"].append(done_msg)
            out = f"{out}\n{done_msg}"
    else:
        state["health"] = max(0, state["health"] - 6)
        out = f"That move is too early. First complete: {expected.get('label') or expected_cmd}. Health -6"
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
        ai_text = call_gemini(
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
    mode = _get_tutor_mode("ctf")

    state["attempts"] += 1

    if submitted == expected:
        state["score"] += 50 * level["level"]
        state["level_index"] += 1
        state["attempts"] = 0
        state["chat_attempts"] = 0
        save_ctf_state(user, state)
        return redirect("/ctf")

    msg = f"Not correct yet. {_ctf_small_hint(level, state['attempts'], mode)}"
    save_ctf_state(user, state)
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
    ai_text = call_gemini(
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
    msg_l = message.lower()
    mode = _get_tutor_mode("ctf")
    effective_mode = mode

    if msg_l in {"next", "hint", "help"}:
        required_attempts = _ctf_required_attempts(effective_mode, level.get("level"))
        current_attempts = state.get("chat_attempts", 0)
        return jsonify(
            {
                "reply": (
                    f"Mode: {effective_mode}. Progress: {current_attempts}/{required_attempts} tries.\n"
                    f"{_ctf_small_hint(level, max(1, current_attempts + 1), effective_mode)}\n"
                    "Try your best guess in the answer box, then ask again if needed."
                )
            }
        )

    if _wants_direct_answer(message):
        required_attempts = _ctf_required_attempts(effective_mode, level.get("level"))
        if effective_mode == "beginner":
            direct = (
                f"Direct answer for Level {level['level']}: `{level['answer']}`.\n"
                f"Why: this level focuses on {level['topic']}."
            )
            return jsonify({"reply": direct})
        state["chat_attempts"] = state.get("chat_attempts", 0) + 1
        save_ctf_state(user, state)
        if state["chat_attempts"] >= required_attempts:
            direct = (
                f"Direct answer unlocked after {state['chat_attempts']} tries in {effective_mode} mode:\n"
                f"`{level['answer']}`"
            )
            return jsonify({"reply": direct})
        hint_reply = _ctf_small_hint(level, state["chat_attempts"], effective_mode)
        return jsonify(
            {
                "reply": (
                    f"Exact answer is disabled in {effective_mode} mode.\n"
                    f"Need {required_attempts} tries (current: {state['chat_attempts']}).\n"
                    f"{hint_reply}"
                )
            }
        )

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
@retry_on_failure(max_retries=3, backoff=2)
def fetch_graph_data(agent_id=None, target=None, agent_state="all"):
    nodes = {}
    edges = []
    edge_ids = set()
    techniques = Counter()
    targets = set()
    cache_bust = int(time.time())
    caldera_agents = []
    live_agent_lookup = {}
    agent_ids_for_query = None
    agent_state = str(agent_state or "all").strip().lower()
    if agent_state not in {"all", "alive", "dead"}:
        agent_state = "all"

    if CALDERA_API_KEY:
        try:
            caldera_agents = get_caldera_agents()
            if agent_state == "alive":
                caldera_agents = [
                    agent for agent in caldera_agents
                    if str(agent.get("status") or "").lower() in {"alive", "pending kill"}
                ]
            elif agent_state == "dead":
                caldera_agents = [
                    agent for agent in caldera_agents
                    if str(agent.get("status") or "").lower() == "dead"
                ]
            live_agent_lookup = {agent["paw"]: agent for agent in caldera_agents if agent.get("paw")}
            agent_ids_for_query = list(live_agent_lookup.keys())
        except Exception:
            caldera_agents = []
            live_agent_lookup = {}
            agent_ids_for_query = None

    if agent_id and live_agent_lookup:
        caldera_agents = [agent for agent in caldera_agents if agent.get("paw") == agent_id]
        live_agent_lookup = {agent["paw"]: agent for agent in caldera_agents if agent.get("paw")}
        agent_ids_for_query = list(live_agent_lookup.keys())

    with driver.session(database="neo4j") as db_session:
        result = db_session.run(
            """
            MATCH (a:Agent)
            WHERE ($agent_id IS NULL OR a.agent_id = $agent_id)
              AND ($agent_ids IS NULL OR a.agent_id IN $agent_ids)
            OPTIONAL MATCH (a)-[:EXECUTED]->(f:Fact)
            WHERE ($target IS NULL OR f IS NULL OR coalesce(f.target, '') = $target)
            OPTIONAL MATCH (f)-[:NEXT]->(n:Fact)
            WHERE ($target IS NULL OR n IS NULL OR coalesce(n.target, '') = $target)
            RETURN a.agent_id AS agent,
                   a.host AS host,
                   a.platform AS platform,
                   a.group AS agroup,
                   a.trusted AS atrusted,
                   a.active AS aactive,
                   a.last_seen AS last_seen,
                   a.username AS username,
                   a.display_name AS display_name,
                   a.privilege AS privilege,
                   f.fact_id AS fid,
                   f.command AS cmd,
                   f.technique_id AS tech,
                   f.target AS ftarget,
                   f.operation_id AS operation_id,
                   f.timestamp AS fact_time,
                   n.fact_id AS nid,
                   n.command AS ncmd,
                   n.technique_id AS ntech,
                   n.target AS ntarget,
                   n.operation_id AS noperation_id,
                   n.timestamp AS nfact_time
            """,
            agent_id=agent_id,
            agent_ids=agent_ids_for_query,
            target=target,
        )

        for row in result:
            agent = row["agent"]
            if not agent:
                continue

            live_agent = live_agent_lookup.get(agent, {})
            agent_status = live_agent.get("status")
            if not agent_status:
                agent_status = "active" if bool(row["aactive"]) else "inactive"

            if agent not in nodes:
                display_name = live_agent.get("display_name") or row["display_name"] or agent
                nodes[agent] = {
                    "data": {
                        "id": agent,
                        "label": agent,
                        "display_name": display_name,
                        "type": "agent",
                        "status": agent_status,
                        "trusted": bool(live_agent.get("trusted", row["atrusted"])),
                        "host": live_agent.get("host") or row["host"],
                        "platform": live_agent.get("platform") or row["platform"],
                        "group": live_agent.get("group") or row["agroup"],
                        "username": live_agent.get("username") or row["username"],
                        "privilege": live_agent.get("privilege") or row["privilege"],
                        "last_seen": live_agent.get("last_seen") or row["last_seen"],
                        "cache_bust": cache_bust,
                    }
                }

            fid = row["fid"]
            cmd = row["cmd"]
            tech = row["tech"]
            ftarget = row["ftarget"]
            if fid and fid not in nodes:
                nodes[fid] = {
                    "data": {
                        "id": fid,
                        "label": cmd if cmd else fid[:24],
                        "type": "fact",
                        "technique": tech,
                        "target": ftarget,
                        "operation_id": row["operation_id"],
                        "timestamp": row["fact_time"],
                        "cache_bust": cache_bust,
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
                    edges.append({"data": {"id": executed_edge_id, "source": agent, "target": fid, "relation": "executed", "cache_bust": cache_bust}})

            nid = row["nid"]
            ncmd = row["ncmd"]
            ntech = row["ntech"]
            ntarget = row["ntarget"]
            if nid:
                if nid not in nodes:
                    nodes[nid] = {
                        "data": {
                            "id": nid,
                            "label": ncmd if ncmd else nid[:24],
                            "type": "fact",
                            "technique": ntech,
                            "target": ntarget,
                            "operation_id": row["noperation_id"],
                            "timestamp": row["nfact_time"],
                            "cache_bust": cache_bust,
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
                        edges.append({"data": {"id": next_edge_id, "source": fid, "target": nid, "relation": "next", "cache_bust": cache_bust}})

    if caldera_agents and not target:
        for agent in caldera_agents:
            paw = agent.get("paw")
            if not paw or paw in nodes:
                continue
            nodes[paw] = {
                "data": {
                    "id": paw,
                    "label": paw,
                    "display_name": agent.get("display_name") or paw,
                    "type": "agent",
                    "status": agent.get("status") or "unknown",
                    "trusted": bool(agent.get("trusted")),
                    "host": agent.get("host"),
                    "platform": agent.get("platform"),
                    "group": agent.get("group"),
                    "username": agent.get("username"),
                    "privilege": agent.get("privilege"),
                    "last_seen": agent.get("last_seen"),
                    "cache_bust": cache_bust,
                }
            }

    graph = {"nodes": list(nodes.values()), "edges": edges}
    attack_paths, target_risk = build_attack_paths(graph)
    graph["attack_paths"] = attack_paths
    graph["target_risk"] = target_risk
    graph["summary"] = build_summary(graph, techniques, target_risk)
    agent_filter_options = []
    for node in graph["nodes"]:
        data = node.get("data", {})
        if data.get("type") != "agent":
            continue
        agent_value = data.get("id")
        display_name = data.get("display_name") or data.get("label") or agent_value
        if not agent_value:
            continue
        agent_label = f"{display_name} ({agent_value})" if display_name and display_name != agent_value else agent_value
        agent_filter_options.append({"value": agent_value, "label": agent_label})
    agent_filter_options.sort(key=lambda item: item["label"].lower())
    graph["filters"] = {
        "agents": agent_filter_options,
        "targets": sorted(targets),
    }
    graph["techniques"] = [{"id": tech_id, "count": count} for tech_id, count in techniques.most_common(12)]
    graph["meta"] = {
        "cache_bust": cache_bust,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "timestamp": time.time(),
        "agent_state_filter": agent_state,
        "alive_agent_count": sum(1 for agent in caldera_agents if str(agent.get("status") or "").lower() in {"alive", "pending kill"}),
        "dead_agent_count": sum(1 for agent in caldera_agents if str(agent.get("status") or "").lower() == "dead"),
    }

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
        agent_ids = sorted(executed_from_fact.get(path[0], set()))
        labels = []
        for agent_id in agent_ids:
            agent_node = node_map.get(agent_id, {})
            display_name = agent_node.get("display_name") or agent_node.get("label") or agent_id
            if display_name and display_name != agent_id:
                labels.append(f"{display_name} ({agent_id})")
            else:
                labels.append(agent_id)
        return labels

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


def _normalize_tid(value):
    tid = (value or "").strip().upper()
    if re.fullmatch(r"T\d{4}(?:\.\d{3})?", tid):
        return tid
    return None


def _base_tid(value):
    tid = _normalize_tid(value)
    if not tid:
        return None
    return tid.split(".", 1)[0]


def _technique_match(observed, required):
    req = _normalize_tid(required)
    if not req:
        return False
    req_base = _base_tid(req)
    for obs in observed:
        if obs == req or _base_tid(obs) == req_base:
            return True
    return False


def _collect_observed_techniques(graph):
    observed = []
    seen = set()

    for item in graph.get("techniques", []):
        tid = _normalize_tid(item.get("id"))
        if tid and tid not in seen:
            seen.add(tid)
            observed.append(tid)

    for path in graph.get("attack_paths", []):
        for raw_tid in path.get("techniques", []):
            tid = _normalize_tid(raw_tid)
            if tid and tid not in seen:
                seen.add(tid)
                observed.append(tid)
    return observed


def _match_playbooks(observed, attack_paths):
    matched = []
    for playbook in ATTACK_PLAYBOOKS:
        required = playbook.get("required", [])
        matched_required = [tid for tid in required if _technique_match(observed, tid)]
        min_match = playbook.get("min_match", len(required))
        if len(matched_required) < min_match:
            continue

        coverage = (len(matched_required) / len(required)) if required else 0
        path_bonus = 0.0
        for path in attack_paths:
            ptech = [_normalize_tid(t) for t in path.get("techniques", [])]
            ptech = [t for t in ptech if t]
            chain_hits = sum(1 for tid in required if _technique_match(ptech, tid))
            if chain_hits >= min_match:
                path_bonus = 0.15
                break

        confidence = min(0.99, 0.55 + (coverage * 0.35) + path_bonus)
        matched.append(
            {
                "id": playbook["id"],
                "name": playbook["name"],
                "severity": playbook["severity"],
                "required": required,
                "matched": matched_required,
                "coverage": round(coverage, 2),
                "confidence": round(confidence, 2),
                "why": playbook["why"],
                "telemetry": playbook["telemetry"],
                "detection": playbook["detection"],
                "response": playbook["response"],
            }
        )

    matched.sort(key=lambda x: (x["confidence"], x["coverage"]), reverse=True)
    return matched


def _risk_priority_weight(level):
    if level == "CRITICAL":
        return 3
    if level == "ELEVATED":
        return 2
    return 1


def _score_to_risk_level(score):
    if score >= 70:
        return "CRITICAL"
    if score >= 40:
        return "ELEVATED"
    return "LOW"


def generate_defense_recommendations(graph):
    observed = _collect_observed_techniques(graph)
    attack_paths = graph.get("attack_paths", [])
    summary = graph.get("summary", {})
    risk_level = summary.get("risk_level", "LOW")

    matched_scenarios = _match_playbooks(observed, attack_paths)
    recommendations = []

    if matched_scenarios:
        for scenario in matched_scenarios[:3]:
            confidence_pct = int(scenario["confidence"] * 100)
            recommendations.append(
                f"[{scenario['severity']}] {scenario['name']} likely ({confidence_pct}% confidence) from techniques: {', '.join(scenario['matched'])}."
            )
            recommendations.append(f"Why this fits: {scenario['why']}")
            recommendations.append(f"Telemetry priority: {scenario['telemetry']}")
            recommendations.append(f"Detection priority: {scenario['detection']}")
            recommendations.append(f"Immediate response: {scenario['response']}")

    covered_bases = {_base_tid(tid) for s in matched_scenarios for tid in s["matched"]}
    for tid in observed[:6]:
        kb = TECHNIQUE_KNOWLEDGE.get(tid) or TECHNIQUE_KNOWLEDGE.get(_base_tid(tid))
        if not kb:
            continue
        if _base_tid(tid) in covered_bases:
            continue
        recommendations.append(
            f"[Technique {tid}] {kb['name']} | telemetry: {kb['telemetry']} | detect: {kb['detection']} | respond: {kb['response']}"
        )

    if not recommendations:
        recommendations = [
            "No strong ATT&CK chain match yet. Start with sequence-based detections before broad containment.",
            "Collect baseline telemetry first: process lineage, auth events, and egress traffic.",
            "Correlate by identity + host + target over time windows to reduce false positives.",
            "Contain only high-confidence entities; keep evidence intact for root-cause analysis.",
        ]

    unique = []
    seen = set()
    for line in recommendations:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)

    unique.sort(key=lambda line: 0 if line.startswith("[CRITICAL]") else (1 if line.startswith("[HIGH]") else 2))

    return {
        "risk_level": risk_level,
        "risk_weight": _risk_priority_weight(risk_level),
        "observed_techniques": observed,
        "matched_scenarios": matched_scenarios,
        "recommendations": unique[:18],
    }


def build_agent_defense_profiles(graph):
    node_map = {n["data"]["id"]: n["data"] for n in graph.get("nodes", [])}
    next_adj = {}
    agent_roots = {}

    for edge in graph.get("edges", []):
        data = edge.get("data", {})
        src = data.get("source")
        dst = data.get("target")
        rel = data.get("relation")
        if rel == "next" and src and dst:
            next_adj.setdefault(src, []).append(dst)
        elif rel == "executed" and src and dst:
            agent_roots.setdefault(src, []).append(dst)

    profiles = []

    for agent_id, agent_data in node_map.items():
        if agent_data.get("type") != "agent":
            continue

        roots = list(dict.fromkeys(agent_roots.get(agent_id, [])))
        fact_ids = set()
        path_nodes = []

        def walk(curr, path, seen):
            fact_ids.add(curr)
            children = next_adj.get(curr, [])
            if not children:
                path_nodes.append(path[:])
                return
            for nxt in children:
                if nxt in seen:
                    continue
                seen.add(nxt)
                path.append(nxt)
                walk(nxt, path, seen)
                path.pop()
                seen.remove(nxt)

        for root in roots:
            walk(root, [root], {root})

        techniques = []
        seen_techniques = set()
        targets = []
        seen_targets = set()
        commands = []

        for fid in fact_ids:
            item = node_map.get(fid, {})
            tech = _normalize_tid(item.get("technique"))
            target = item.get("target")
            command = item.get("label")
            if tech and tech not in seen_techniques:
                seen_techniques.add(tech)
                techniques.append(tech)
            if target and target not in seen_targets:
                seen_targets.add(target)
                targets.append(target)
            if command:
                commands.append(command)

        attack_paths = []
        for idx, nodes_in_path in enumerate(path_nodes[:8]):
            path_techniques = []
            seen_path_tech = set()
            for nid in nodes_in_path:
                tech = _normalize_tid(node_map.get(nid, {}).get("technique"))
                if tech and tech not in seen_path_tech:
                    seen_path_tech.add(tech)
                    path_techniques.append(tech)
            risk_score = min(100, (len(nodes_in_path) * 10) + (len(path_techniques) * 8))
            path_targets = [node_map.get(nid, {}).get("target") for nid in nodes_in_path if node_map.get(nid, {}).get("target")]
            attack_paths.append(
                {
                    "id": f"{agent_id}-path-{idx + 1}",
                    "agents": [agent_id],
                    "target": Counter(path_targets).most_common(1)[0][0] if path_targets else "unknown",
                    "length": len(nodes_in_path),
                    "nodes": nodes_in_path,
                    "commands": [node_map.get(nid, {}).get("label") for nid in nodes_in_path if node_map.get(nid, {}).get("label")],
                    "techniques": path_techniques,
                    "risk_score": risk_score,
                }
            )

        matched_scenarios = _match_playbooks(techniques, attack_paths)
        recommendations = []

        if matched_scenarios:
            for scenario in matched_scenarios[:2]:
                recommendations.append(
                    f"[{agent_id}] {scenario['name']} | contain: {scenario['response']}"
                )
                recommendations.append(
                    f"[{agent_id}] detect: {scenario['detection']}"
                )

        covered_bases = {_base_tid(tid) for item in matched_scenarios for tid in item.get("matched", [])}
        for tid in techniques[:4]:
            kb = TECHNIQUE_KNOWLEDGE.get(tid) or TECHNIQUE_KNOWLEDGE.get(_base_tid(tid))
            if not kb or _base_tid(tid) in covered_bases:
                continue
            recommendations.append(
                f"[{agent_id}] {tid} | telemetry: {kb['telemetry']} | respond: {kb['response']}"
            )

        if not recommendations:
            status = agent_data.get("status", "active")
            if roots:
                recommendations = [
                    f"[{agent_id}] Review host timeline, auth events, and outbound traffic before broad containment.",
                    f"[{agent_id}] Validate local persistence, admin sessions, and reachable targets from this {'inactive' if status == 'dead' else 'active'} agent.",
                ]
            else:
                recommendations = [
                    f"[{agent_id}] No executed links yet. Keep baseline monitoring, process lineage, and auth telemetry enabled.",
                    f"[{agent_id}] Use this agent as a comparison baseline for suspicious peers until activity appears.",
                ]

        risk_score = min(100, (len(fact_ids) * 8) + (len(techniques) * 10) + (len(roots) * 6))
        risk_level = _score_to_risk_level(risk_score)
        profiles.append(
            {
                "agent_id": agent_id,
                "status": agent_data.get("status", "active"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "techniques": techniques,
                "targets": targets,
                "commands": commands[:6],
                "matched_scenarios": matched_scenarios,
                "recommendations": recommendations[:8],
                "attack_paths": attack_paths[:4],
                "root_count": len(roots),
            }
        )

    profiles.sort(key=lambda item: (item["risk_score"], len(item.get("techniques", []))), reverse=True)
    return profiles


def find_agent_profile(agent_profiles, agent_id=None):
    if not agent_profiles:
        return None
    if agent_id:
        for profile in agent_profiles:
            if profile.get("agent_id") == agent_id:
                return profile
    return agent_profiles[0]


def build_wsl_adversary_model(graph, analysis=None):
    analysis = analysis or {}
    summary = graph.get("summary", {})
    matched_scenarios = analysis.get("matched_scenarios", [])
    observed = analysis.get("observed_techniques") or _collect_observed_techniques(graph)
    filters = graph.get("filters", {})
    active_agents = filters.get("agents", [])[:6]
    active_targets = filters.get("targets", [])[:6]
    attack_paths = graph.get("attack_paths", [])

    model = dict(WSL_MULTI_SYSTEM_ADVERSARY)
    model["phases"] = [dict(item) for item in WSL_MULTI_SYSTEM_ADVERSARY["phases"]]
    model["operation_steps"] = list(WSL_MULTI_SYSTEM_ADVERSARY["operation_steps"])
    model["defense_priorities"] = list(WSL_MULTI_SYSTEM_ADVERSARY["defense_priorities"])
    model["live_context"] = {
        "risk_level": summary.get("risk_level", "LOW"),
        "risk_score": summary.get("risk_score", 0),
        "active_agent_count": summary.get("agent_count", 0),
        "tracked_target_count": len(active_targets),
        "parallel_attack_paths": len(attack_paths),
        "active_agents": active_agents or ["wsl-operator", "app-host", "db-host"],
        "active_targets": active_targets or ["identity", "application", "database"],
        "highlighted_techniques": observed[:5] or ["T1059", "T1078", "T1021", "T1041"],
        "matched_scenarios": [item.get("name") for item in matched_scenarios[:3]],
    }
    return model


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
