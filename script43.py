import os
import json
import time
import csv
import smtplib
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread, Lock
from flask import Flask, Blueprint, render_template_string, request, jsonify, session, redirect, url_for

# =========================================================================
# INITIALIZE FLASK CORE & BLUEPRINT
# =========================================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

script43_bp = Blueprint('script43', __name__)

CONFIG_FILE = 'email_config.json'
db_lock = Lock()

# Dispatch Global Engine State Parameters
broadcast_state = {
    'is_running': False,
    'total_records': 0,
    'processed_count': 0,
    'success_count': 0,
    'failed_count': 0,
    'logs': []
}

# =========================================================================
# CONFIGURATION ENGINE STORAGE LOGIC
# =========================================================================
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "use_tls": True
    }

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

# =========================================================================
# CORE EMAIL TRANSMISSION WORKFLOW ENGINE
# =========================================================================
def async_email_executor(targets, subject, template_body, config):
    global broadcast_state
    
    try:
        # SMTP initialization validation rules
        if config['use_tls']:
            server = smtplib.SMTP(config['smtp_server'], int(config['smtp_port']), timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], int(config['smtp_port']), timeout=15)
            
        server.login(config['smtp_user'], config['smtp_pass'])
    except Exception as e:
        with db_lock:
            broadcast_state['is_running'] = False
            broadcast_state['logs'].insert(0, f"🛑 CRITICAL SMTP AUTH AUTHENTICATION FAILED: {str(e)}")
        return

    for item in targets:
        if not broadcast_state['is_running']:
            break
            
        email = item.get('email', '').strip()
        name = item.get('name', 'Valued Client').strip()
        company = item.get('company', 'Enterprise Global').strip()
        
        if not email or "@" not in email:
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['failed_count'] += 1
                broadcast_state['logs'].insert(0, f"⚠️ SKIPPED: Invalid email configuration pattern parsed for '{name}'")
            continue

        try:
            # Token Dynamic Translation Processing
            custom_body = template_body.replace('[Name]', name).replace('[Company]', company)
            
            # Injection into Executive Professional Shell Base Wrapper Layout
            professional_html_shell = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f5f7; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
                    .wrapper {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eef2f5; }}
                    .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 35px 40px; text-align: center; }}
                    .header h1 {{ color: #ffffff; font-size: 24px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }}
                    .content {{ padding: 40px; color: #334155; font-size: 16px; line-height: 1.6; }}
                    .footer {{ background-color: #f8fafc; padding: 25px 40px; text-align: center; border-top: 1px solid #f1f5f9; }}
                    .footer p {{ color: #94a3b8; font-size: 12px; margin: 0; }}
                </style>
            </head>
            <body>
                <div class="wrapper">
                    <div class="header">
                        <h1>Corporate Communication Portal</h1>
                    </div>
                    <div class="content">
                        {custom_body}
                    </div>
                    <div class="footer">
                        <p>© 2026 Executive Enterprise. All rights secured configuration systems.</p>
                        <p style="margin-top: 5px; font-size: 10px; color: #cbd5e1;">If you wish to opt-out, please contact data operations matrix directly.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config['smtp_user']
            msg['To'] = email
            
            msg.attach(MIMEText(professional_html_shell, 'html'))
            
            server.sendmail(config['smtp_user'], email, msg.as_string())
            
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['success_count'] += 1
                broadcast_state['logs'].insert(0, f"✅ DISPATCHED SUCCESS: Secured delivery frame transmitted to {email}")
                
        except Exception as ex:
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['failed_count'] += 1
                broadcast_state['logs'].insert(0, f"❌ DISPATCH FAILURE: Routing failure toward {email} -> {str(ex)}")
                
        time.sleep(0.8)  # Anti-Spam protection throttle delay rule

    try:
        server.quit()
    except:
        pass

    with db_lock:
        broadcast_state['is_running'] = False
        broadcast_state['logs'].insert(0, "🏁 OPERATION COMPLETION: Bulk transmission engine has safely decoupled.")

# =========================================================================
# FLASK ROUTING GATEWAYS
# =========================================================================
@script43_bp.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_LAYOUT, config=load_config())

# =========================================================================
# ASYNC API CONTROLLERS
# =========================================================================
@script43_bp.route('/api/save_settings', methods=['POST'])
def save_settings():
    config = {
        "smtp_server": request.form.get('smtp_server', ''),
        "smtp_port": int(request.form.get('smtp_port', 587)),
        "smtp_user": request.form.get('smtp_user', ''),
        "smtp_pass": request.form.get('smtp_pass', ''),
        "use_tls": request.form.get('use_tls') == 'true'
    }
    save_config(config)
    return jsonify({"success": True, "message": "SMTP parameters successfully updated."})

@script43_bp.route('/api/parse_csv', methods=['POST'])
def parse_csv():
    if 'csv_file' not in request.files:
        return jsonify({"success": False, "message": "No file container detected."})
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Empty document context structure."})

    try:
        stream = StringIO(file.stream.read().decode("UTF-8"), newline=None)
        reader = csv.reader(stream)
        
        rows = list(reader)
        if not rows:
            return jsonify({"success": False, "message": "No data items detected inside sheet profile."})
            
        # Validate or parse column locations dynamically
        targets = []
        for row in rows:
            if not row or len(row) < 1: continue
            email = row[0]
            name = row[1] if len(row) > 1 else "Valued Client"
            company = row[2] if len(row) > 2 else "Enterprise Corp"
            if "@" in email:
                targets.append({"email": email, "name": name, "company": company})
                
        return jsonify({"success": True, "count": len(targets), "data": targets})
    except Exception as e:
        return jsonify({"success": False, "message": f"CSV structure configuration crash: {str(e)}"})

@script43_bp.route('/api/start_broadcast', methods=['POST'])
def start_broadcast():
    global broadcast_state
    if broadcast_state['is_running']:
        return jsonify({"success": False, "message": "An active delivery process layout is already running."})
        
    subject = request.form.get('subject', 'Operational Broadcast Bulletin')
    message_body = request.form.get('message_body', '')
    targets_json = request.form.get('targets', '[]')
    
    try:
        targets = json.loads(targets_json)
    except:
        return jsonify({"success": False, "message": "Target list array validation array structure broken."})
        
    if not targets:
        return jsonify({"success": False, "message": "No functional ingestion records designated to process."})
        
    config = load_config()
    if not config['smtp_user'] or not config['smtp_pass']:
        return jsonify({"success": False, "message": "Configure active SMTP parameters first before executing."})

    # Reset Broadcast Engine States
    with db_lock:
        broadcast_state['is_running'] = True
        broadcast_state['total_records'] = len(targets)
        broadcast_state['processed_count'] = 0
        broadcast_state['success_count'] = 0
        broadcast_state['failed_count'] = 0
        broadcast_state['logs'] = ["🚀 ENGINE INITIALIZATION: Dispatched background telemetry threading loops..."]

    thread = Thread(target=async_email_executor, args=(targets, subject, message_body, config))
    thread.start()
    
    return jsonify({"success": True})

@script43_bp.route('/api/stop_broadcast', methods=['POST'])
def stop_broadcast():
    global broadcast_state
    with db_lock:
        if broadcast_state['is_running']:
            broadcast_state['is_running'] = False
            broadcast_state['logs'].insert(0, "🛑 HALT SIGNAL RECEIVED: Forcing thread cancellation layers...")
    return jsonify({"success": True})

@script43_bp.route('/api/get_status', methods=['GET'])
def get_status():
    global broadcast_state
    with db_lock:
        return jsonify(broadcast_state)

app.register_blueprint(script43_bp, url_prefix='/')

# =========================================================================
# DYNAMIC RESPONSIVE EXECUTIVE HTML TEMPLATE DESIGN
# =========================================================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdge Media | Intelligent Mass Email Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #090d16; color: #f1f5f9; }
    </style>
</head>
<body class="antialiased selection:bg-indigo-600 selection:text-white min-h-screen">

    <header class="border-b border-gray-800 bg-gray-950/70 backdrop-blur px-6 py-4 sticky top-0 z-50 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="p-2.5 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl shadow-lg shadow-indigo-500/20">
                <i class="fa-solid fa-paper-plane text-lg text-white"></i>
            </div>
            <div>
                <h1 class="text-base font-bold tracking-tight text-white leading-none">OrbitEdge Media</h1>
                <span class="text-[10px] uppercase text-gray-400 tracking-widest mt-1 block">Mass Email Engine v4.3</span>
            </div>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 px-3.5 py-1.5 rounded-xl text-indigo-400">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> Engine Live
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- COLUMN 1: SMTP GATEWAY INTERACTION -->
        <div class="space-y-6">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h3 class="text-sm font-bold uppercase text-indigo-400 tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-server"></i> SMTP Gateway Config
                </h3>
                <form id="smtp-form" onsubmit="saveSMTPSettings(event)" class="space-y-3.5 text-xs">
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">SMTP Host Relay</label>
                        <input type="text" id="smtp_server" value="{{ config.smtp_server }}" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Port</label>
                            <input type="number" id="smtp_port" value="{{ config.smtp_port }}" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Security Mode</label>
                            <select id="use_tls" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                                <option value="true" {% if config.use_tls %}selected{% endif %}>STARTTLS (587)</option>
                                <option value="false" {% if not config.use_tls %}selected{% endif %}>SSL/TLS (465)</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">Username / Email ID</label>
                        <input type="email" id="smtp_user" value="{{ config.smtp_user }}" required placeholder="user@gmail.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">App Password</label>
                        <input type="password" id="smtp_pass" value="{{ config.smtp_pass }}" required placeholder="••••••••••••••••" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition cursor-pointer shadow-md">
                        Commit Configuration Entry
                    </button>
                </form>
            </div>

            <!-- INGEST TARGET SHEET CONTEXT -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h3 class="text-sm font-bold uppercase text-emerald-400 tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-file-csv"></i> Target Ingestion (.csv)
                </h3>
                <p class="text-[11px] text-gray-400 leading-relaxed"> ingests files perfectly. Layout required map sequence formatting layout: <code class="text-emerald-400 font-mono">email, name, company</code> as rows.</p>
                <div class="border border-dashed border-gray-800 rounded-xl p-4 bg-gray-950/50 text-center relative cursor-pointer hover:border-gray-700 transition">
                    <input type="file" id="csv_file" accept=".csv" onchange="uploadTargetCSV()" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
                    <i class="fa-solid fa-cloud-arrow-up text-xl text-gray-500 mb-1"></i>
                    <p class="text-xs font-semibold text-gray-300">Ingest Target Spreadsheet</p>
                </div>
                <div id="target-counter-pane" class="hidden text-xs bg-gray-950 border border-gray-800 p-3 rounded-xl flex items-center justify-between">
                    <span class="text-gray-400">Parsed Targets Stack:</span>
                    <span id="target-badge-count" class="bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded border border-emerald-500/20">0 Loaded</span>
                </div>
            </div>
        </div>

        <!-- COLUMN 2 & 3: COMPOSER & MONITOR ECOSYSTEM -->
        <div class="lg:col-span-2 space-y-6">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h3 class="text-sm font-bold uppercase text-white tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-pen-nib text-indigo-500"></i> Corporate Broadcast Composer Engine
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div class="space-y-3.5">
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Email Subject Header</label>
                            <input type="text" id="email_subject" value="Executive Strategic Bulletin" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Message Shell HTML Body Editor</label>
                            <p class="text-[10px] text-gray-500 mb-1">Placeholder tokens allowed: <span class="text-indigo-400 font-mono">[Name]</span>, <span class="text-indigo-400 font-mono">[Company]</span></p>
                            <textarea id="email_body" rows="8" onkeyup="updateLivePreview()" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white font-mono focus:outline-none focus:border-indigo-500 resize-none" placeholder="&lt;p&gt;Dear [Name],&lt;/p&gt;&#10;&lt;p&gt;We are pleased to introduce custom services built for [Company].&lt;/p&gt;"></textarea>
                        </div>
                        <div class="flex gap-3">
                            <button onclick="triggerBroadcastSequence()" id="start-btn" class="flex-1 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold py-3 rounded-xl transition cursor-pointer text-center shadow-lg shadow-indigo-500/10 flex items-center justify-center gap-2">
                                <i class="fa-solid fa-rocket"></i> Launch Transmission
                            </button>
                            <button onclick="terminateBroadcastSequence()" id="stop-btn" disabled class="bg-rose-600/20 text-rose-500 border border-rose-500/20 hover:bg-rose-500/30 font-bold px-4 rounded-xl transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                                <i class="fa-solid fa-hand"></i> Halt
                            </button>
                        </div>
                    </div>

                    <!-- INTERACTIVE LIVE PREVIEW RENDER SHELL FRAME -->
                    <div class="flex flex-col border border-gray-800 rounded-xl overflow-hidden bg-gray-950">
                        <div class="bg-gray-900 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-800 flex items-center gap-1.5">
                            <i class="fa-solid fa-eye text-indigo-400"></i> Executive Corporate Shell Live Preview
                        </div>
                        <div class="flex-1 p-4 bg-white text-gray-800 overflow-y-auto max-h-[295px]" id="live-render-frame" style="min-height: 250px;">
                            <div style="text-align: center; color: #94a3b8; padding-top: 60px;">
                                <i class="fa-solid fa-code text-2xl mb-2 block"></i>
                                Waiting for content structure inputs...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TRANSMISSION METRICS TRACKER & REALTIME LOG ARCHIVE -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div class="flex justify-between items-center">
                    <h3 class="text-sm font-bold uppercase text-white tracking-wider flex items-center gap-2">
                        <i class="fa-solid fa-satellite-dish text-emerald-500"></i> Real-time Process Grid Monitor
                    </h3>
                    <div id="status-spinner" class="hidden text-xs text-indigo-400 font-semibold items-center gap-1.5">
                        <i class="fa-solid fa-circle-notch animate-spin"></i> Processing Pipelines...
                    </div>
                </div>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Progress Index</span>
                        <h4 id="progress-text" class="text-xl font-extrabold text-white">0 / 0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Success Clearances</span>
                        <h4 id="success-text" class="text-xl font-extrabold text-emerald-500">0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Failed Dispatches</span>
                        <h4 id="failed-text" class="text-xl font-extrabold text-rose-500">0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Completion Rate</span>
                        <h4 id="rate-text" class="text-xl font-extrabold text-indigo-400">0%</h4>
                    </div>
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-wide"><i class="fa-solid fa-terminal text-xs"></i> Chronological Telemetry Logging</label>
                    <div id="log-terminal" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3.5 h-44 overflow-y-auto text-[11px] font-mono text-gray-400 space-y-1.5">
                        <div class="text-gray-600">Terminal awaiting operational instructions context hooks...</div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let ingestedTargets = [];
        let synchronizationLoopInterval = null;

        function updateLivePreview() {
            let bodyContent = document.getElementById('email_body').value || "<p style='color:#94a3b8;'>Draft communication body summary mapping content arrays...</p>";
            let processedPreview = bodyContent.replace('[Name]', 'Rahul Sharma').replace('[Company]', 'Sharma Tech');
            
            let structuralShell = `
                <div style="font-family:'Helvetica Neue',Arial,sans-serif; background-color:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #eef2f5;">
                    <div style="background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding:20px; text-align:center; color:#ffffff; font-weight:bold; font-size:16px;">
                        Corporate Communication Portal
                    </div>
                    <div style="padding:25px; color:#334155; font-size:14px; line-height:1.5;">
                        ${processedPreview}
                    </div>
                    <div style="background-color:#f8fafc; padding:15px; text-align:center; border-top:1px solid #f1f5f9; color:#94a3b8; font-size:10px;">
                        © 2026 Executive Enterprise. Live Preview Rendering Node.
                    </div>
                </div>`;
            document.getElementById('live-render-frame').innerHTML = structuralShell;
        }

        async function saveSMTPSettings(e) {
            e.preventDefault();
            let fd = new FormData();
            fd.append('smtp_server', document.getElementById('smtp_server').value);
            fd.append('smtp_port', document.getElementById('smtp_port').value);
            fd.append('smtp_user', document.getElementById('smtp_user').value);
            fd.append('smtp_pass', document.getElementById('smtp_pass').value);
            fd.append('use_tls', document.getElementById('use_tls').value);

            let response = await fetch('/api/save_settings', { method: 'POST', body: fd });
            let res = await response.json();
            if(res.success) alert(res.message);
        }

        async function uploadTargetCSV() {
            let fileInput = document.getElementById('csv_file');
            if(fileInput.files.length === 0) return;
            
            let fd = new FormData();
            fd.append('csv_file', fileInput.files[0]);

            let response = await fetch('/api/parse_csv', { method: 'POST', body: fd });
            let res = await response.json();
            
            if(res.success) {
                ingestedTargets = res.data;
                document.getElementById('target-counter-pane').classList.remove('hidden');
                document.getElementById('target-badge-count').innerText = `${res.count} Loaded`;
            } else {
                alert(res.message);
            }
        }

        async function triggerBroadcastSequence() {
            if(ingestedTargets.length === 0) return alert("Ingest target CSV list parameters first.");
            
            let fd = new FormData();
            fd.append('subject', document.getElementById('email_subject').value);
            fd.append('message_body', document.getElementById('email_body').value);
            fd.append('targets', JSON.stringify(ingestedTargets));

            let response = await fetch('/api/start_broadcast', { method: 'POST', body: fd });
            let res = await response.json();
            
            if(res.success) {
                document.getElementById('start-btn').disabled = true;
                document.getElementById('stop-btn').disabled = false;
                document.getElementById('status-spinner').classList.remove('hidden');
                document.getElementById('status-spinner').classList.add('flex');
                
                // Engage looping verification intervals
                synchronizationLoopInterval = setInterval(fetchEcosystemTelemetry, 1000);
            } else {
                alert(res.message);
            }
        }

        async function terminateBroadcastSequence() {
            await fetch('/api/stop_broadcast', { method: 'POST' });
        }

        async function fetchEcosystemTelemetry() {
            let response = await fetch('/api/get_status');
            let data = await response.json();

            document.getElementById('progress-text').innerText = `${data.processed_count} / ${data.total_records}`;
            document.getElementById('success-text').innerText = data.success_count;
            document.getElementById('failed-text').innerText = data.failed_count;
            
            let rate = data.total_records > 0 ? Math.round((data.processed_count / data.total_records) * 100) : 0;
            document.getElementById('rate-text').innerText = `${rate}%`;

            let term = document.getElementById('log-terminal');
            term.innerHTML = '';
            if(data.logs.length === 0) {
                term.innerHTML = `<div class="text-gray-600">Awaiting runtime logging execution paths...</div>`;
            } else {
                data.logs.forEach(log => {
                    term.innerHTML += `<div class="py-0.5 border-b border-gray-900/50 truncate">${log}</div>`;
                });
            }

            if(!data.is_running) {
                clearInterval(synchronizationLoopInterval);
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
                document.getElementById('status-spinner').classList.remove('flex');
                document.getElementById('status-spinner').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)

