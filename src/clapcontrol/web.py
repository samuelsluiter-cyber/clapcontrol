"""Lightweight Web UI companion for ClapControl."""
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from .config import load_config, save_config
from .actions import execute_action

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClapControl Dashboard</title>
    <style>
        :root {
            --bg: #0b0f19;
            --card: rgba(22, 30, 49, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --green: #22c55e;
            --text: #f8fafc;
            --text-dim: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body {
            background: radial-gradient(circle at 50% 20%, #1e293b, var(--bg));
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 520px;
            background: var(--card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 28px;
        }
        .title { display: flex; align-items: center; gap: 12px; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
        .badge {
            background: rgba(34, 197, 94, 0.15);
            color: var(--green);
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid rgba(34, 197, 94, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .badge::before {
            content: "";
            width: 6px;
            height: 6px;
            background: var(--green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }
        .card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 18px;
        }
        .card-label { font-size: 13px; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
        .slider-group { display: flex; align-items: center; gap: 16px; }
        input[type="range"] {
            flex: 1;
            height: 6px;
            border-radius: 9999px;
            background: #334155;
            outline: none;
            accent-color: var(--accent);
        }
        .slider-val { font-size: 16px; font-weight: 600; width: 40px; text-align: right; }
        .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button {
            background: #1e293b;
            color: var(--text);
            border: 1px solid var(--border);
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button:hover {
            background: #334155;
            border-color: var(--accent);
            transform: translateY(-1px);
        }
        button:active { transform: translateY(1px); }
        .btn-accent {
            background: var(--accent);
            color: #0b0f19;
            border: none;
        }
        .btn-accent:hover {
            background: #7dd3fc;
            box-shadow: 0 0 20px var(--accent-glow);
        }
        .footer { text-align: center; font-size: 12px; color: var(--text-dim); margin-top: 24px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">👏 ClapControl</div>
            <div class="badge">Aktiv</div>
        </div>

        <div class="card">
            <div class="card-label">Empfindlichkeit (Sensitivität)</div>
            <div class="slider-group">
                <input type="range" id="sens" min="10" max="95" value="70" oninput="updateSens(this.value)">
                <span class="slider-val" id="sens-val">70%</span>
            </div>
        </div>

        <div class="card">
            <div class="card-label">Aktionen testen</div>
            <div class="btn-grid">
                <button onclick="triggerAction('double')">👏 2× Klatschen<br><small style='color:var(--text-dim); font-size:11px'>Media Play/Pause</small></button>
                <button onclick="triggerAction('triple')">👏👏 3× Klatschen<br><small style='color:var(--text-dim); font-size:11px'>Display Sleep</small></button>
            </div>
        </div>

        <div class="card">
            <div class="card-label">Sound Feedback</div>
            <button style="width: 100%" onclick="triggerAction('mute')">🔈 System Mute / Unmute</button>
        </div>

        <div class="footer">Open Source • Entwickelt für Samuel Sluiter</div>
    </div>

    <script>
        function updateSens(val) {
            document.getElementById('sens-val').innerText = val + '%';
            fetch('/api/sensitivity?val=' + val, { method: 'POST' });
        }
        function triggerAction(action) {
            fetch('/api/test?action=' + action, { method: 'POST' });
        }
    </script>
</body>
</html>
"""

class WebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        cfg = load_config()

        if url.path == "/api/sensitivity":
            val = int(qs.get("val", [70])[0])
            cfg["audio"]["sensitivity"] = val
            save_config(cfg)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        elif url.path == "/api/test":
            action = qs.get("action", ["double"])[0]
            if action == "double":
                execute_action(cfg["actions"]["double_clap"])
            elif action == "triple":
                execute_action(cfg["actions"]["triple_clap"])
            elif action == "mute":
                execute_action("volume_mute")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

def run_web_server(port: int = 49152):
    server = ThreadingHTTPServer(("127.0.0.1", port), WebHandler)
    server.serve_forever()
