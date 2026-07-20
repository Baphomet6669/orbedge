import os
import json
import time
import csv
import smtplib
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread, Lock
from flask import Flask, render_template_string, request, jsonify

# =========================================================================
# FLASK APP CORE INITIALIZATION
# =========================================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

db_lock = Lock()

# In-memory execution telemetry state
broadcast_state = {
    'is_running': False,
    'total_records': 0,
    'processed_count': 0,
    'success_count': 0,
    'failed_count': 0,
    'logs': []
}

# In-memory config persistence
current_config = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_pass": "",
    "use_tls": True
}

# =========================================================================
# ASYNC TRANSMISSION WORKFLOW ENGINE
# =========================================================================
def async_email_executor(targets, subject, template_body, config):
    global broadcast_state
    
    try:
        use_tls = config.get('use_tls', True)
        port = int(config.get('smtp_port', 587))
        server_host = config.get('smtp_server', 'smtp.gmail.com')

        if use_tls:
            server = smtplib.SMTP(server_host, port, timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(server_host, port, timeout=15)
            
        clean_pass = str(config['smtp_pass']).replace(' ', '').strip()
        server.login(str(config['smtp_user']).strip(), clean_pass)
        
        with db_lock:
            broadcast_state['logs'].insert(0, f"🔑 SMTP SUCCESS: Authenticated as {config['smtp_user']}")
    except Exception as e:
        with db_lock:
            broadcast_state['is_running'] = False
            broadcast_state['logs'].insert(0, f"🛑 CRITICAL SMTP AUTH ERROR: {str(e)}")
        return

    for item in targets:
        if not broadcast_state['is_running']:
            break
            
        email = str(item.get('email', '')).strip()
        name = str(item.get('name', 'Valued Client')).strip()
        company = str(item.get('company', 'Enterprise Global')).strip()
        
        if not email or "@" not in email:
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['failed_count'] += 1
                broadcast_state['logs'].insert(0, f"⚠️ SKIPPED: Invalid address '{email}'")
            continue

        try:
            custom_body = template_body.replace('[Name]', name).replace('[Company]', company)
            
            professional_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f4f5f7; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; border: 1px solid #eef2f5;">
        <h2 style="color: #4f46e5; margin-top: 0;">Corporate Communication</h2>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <div style="color: #334155; font-size: 15px; line-height: 1.6;">
            {custom_body}
        </div>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 11px; text-align: center;">© 2026 Executive Communications</p>
    </div>
</body>
</html>"""
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config['smtp_user']
            msg['To'] = email
            msg.attach(MIMEText(professional_html, 'html'))
            
            server.sendmail(config['smtp_user'], email, msg.as_string())
            
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['success_count'] += 1
                broadcast_state['logs'].insert(0, f"✅ DISPATCHED: Delivered to {email}")
                
        except Exception as ex:
            with db_lock:
                broadcast_state['processed_count'] += 1
                broadcast_state['failed_count'] += 1
                broadcast_state['logs'].insert(0, f"❌ FAILURE: {email} -> {str(ex)}")
                
        time.sleep(0.5)

    try:
        server.quit()
    except Exception:
        pass

    with db_lock:
        broadcast_state['is_running'] = False
        broadcast_state['logs'].insert(0, "🏁 OPERATION COMPLETE: All broadcasts finished.")

# =========================================================================
# FLASK ROUTE CONTROLLERS
# =========================================================================
@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_LAYOUT, config=current_config)

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    global current_config
    try:
        current_config["smtp_server"] = request.form.get('smtp_server', 'smtp.gmail.com').strip()
        current_config["smtp_port"] = int(request.form.get('smtp_port', 587))
        current_config["smtp_user"] = request.form.get('smtp_user', '').strip()
        current_config["smtp_pass"] = request.form.get('smtp_pass', '').strip()
        current_config["use_tls"] = (request.form.get('use_tls') == 'true')
        return jsonify({"success": True, "message": "SMTP Settings Saved Successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Save error: {str(e)}"})

@app.route('/api/parse_csv', methods=['POST'])
def parse_csv():
    if 'csv_file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."})
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Empty file uploaded."})

    try:
        stream = StringIO(file.stream.read().decode("UTF-8"), newline=None)
        reader = csv.reader(stream)
        
        rows = list(reader)
        if not rows:
            return jsonify({"success": False, "message": "CSV file is empty."})
            
        targets = []
        for row in rows:
            if not row or len(row) < 1: 
                continue
            email = row[0].strip()
            name = row[1].strip() if len(row) > 1 else "Valued Client"
            company = row[2].strip() if len(row) > 2 else "Enterprise Corp"
            if "@" in email:
                targets.append({"email": email, "name": name, "company": company})
                
        return jsonify({"success": True, "count": len(targets), "data": targets})
    except Exception as e:
        return jsonify({"success": False, "message": f"CSV parse error: {str(e)}"})

@app.route('/api/start_broadcast', methods=['POST'])
def start_broadcast():
    global broadcast_state, current_config
    if broadcast_state['is_running']:
        return jsonify({"success": False, "message": "A broadcast process is already running."})
        
    subject = request.form.get('subject', 'Operational Notice')
    message_body = request.form.get('message_body', '')
    targets_json = request.form.get('targets', '[]')
    manual_emails_raw = request.form.get('manual_emails', '').strip()
    
    try:
        targets = json.loads(targets_json)
    except Exception:
        targets = []
        
    if manual_emails_raw:
        lines = manual_emails_raw.replace('\r', '').split('\n')
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            sub_entries = line_clean.split(',')
            for entry in sub_entries:
                item = entry.strip()
                if "@" in item:
                    targets.append({"email": item, "name": "Valued Client", "company": "Enterprise Corp"})
        
    if not targets:
        return jsonify({"success": False, "message": "No valid recipient email addresses found."})

    if not current_config.get('smtp_user') or not current_config.get('smtp_pass'):
        return jsonify({"success": False, "message": "Configure SMTP Settings (Gmail & App Password) first."})

    with db_lock:
        broadcast_state['is_running'] = True
        broadcast_state['total_records'] = len(targets)
        broadcast_state['processed_count'] = 0
        broadcast_state['success_count'] = 0
        broadcast_state['failed_count'] = 0
        broadcast_state['logs'] = ["🚀 STARTING TRANSMISSION: Initializing SMTP connection..."]

    thread = Thread(target=async_email_executor, args=(targets, subject, message_body, current_config))
    thread.start()
    
    return jsonify({"success": True})

@app.route('/api/stop_broadcast', methods=['POST'])
def stop_broadcast():
    global broadcast_state
    with db_lock:
        if broadcast_state['is_running']:
            broadcast_state['is_running'] = False
            broadcast_state['logs'].insert(0, "🛑 HALT SIGNAL RECEIVED: Stopping broadcast execution...")
    return jsonify({"success": True})

@app.route('/api/get_status', methods=['GET'])
def get_status():
    global broadcast_state
    with db_lock:
        return jsonify(broadcast_state)

# =========================================================================
# UI HTML TEMPLATE & DASHBOARD FRONTEND
# =========================================================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Dispatch Studio</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #090d16; color: #f1f5f9; }
    </style>
</head>
<body class="antialiased min-h-screen">

    <header class="border-b border-gray-800 bg-gray-950/70 backdrop-blur px-6 py-4 sticky top-0 z-50 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="p-2.5 bg-indigo-600 rounded-xl shadow-lg">
                <i class="fa-solid fa-paper-plane text-lg text-white"></i>
            </div>
            <div>
                <h1 class="text-base font-bold text-white leading-none">Enterprise Mail Engine</h1>
                <span class="text-[10px] uppercase text-gray-400 tracking-widest mt-1 block">Broadcast Studio v4.3</span>
            </div>
        </div>
        <div class="text-xs font-semibold bg-emerald-500/10 border border-emerald-500/20 px-3.5 py-1.5 rounded-xl text-emerald-400 flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> Online
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div class="space-y-6">
            <!-- SMTP SETTINGS -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-3">
                <h3 class="text-sm font-bold uppercase text-indigo-400 tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-server"></i> SMTP Settings
                </h3>
                <form onsubmit="saveSMTPSettings(event)" class="space-y-3 text-xs">
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">SMTP Server</label>
                        <input type="text" id="smtp_server" value="{{ config.smtp_server }}" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Port</label>
                            <input type="number" id="smtp_port" value="{{ config.smtp_port }}" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2 text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Security</label>
                            <select id="use_tls" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-2 py-2 text-white focus:outline-none focus:border-indigo-500">
                                <option value="true" {% if config.use_tls %}selected{% endif %}>STARTTLS (587)</option>
                                <option value="false" {% if not config.use_tls %}selected{% endif %}>SSL/TLS (465)</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">Gmail / Sender Email</label>
                        <input type="email" id="smtp_user" value="{{ config.smtp_user }}" required placeholder="your.email@gmail.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <div>
                        <label class="block text-gray-400 font-medium mb-1">App Password</label>
                        <input type="password" id="smtp_pass" value="{{ config.smtp_pass }}" required placeholder="•••• •••• •••• ••••" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2 text-white focus:outline-none focus:border-indigo-500">
                    </div>
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 rounded-xl transition cursor-pointer">
                        Save SMTP Settings
                    </button>
                </form>
            </div>

            <!-- MANUAL INPUT -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-3">
                <h3 class="text-sm font-bold uppercase text-indigo-400 tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-keyboard"></i> Manual Emails
                </h3>
                <textarea id="manual_emails" rows="4" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 resize-none" placeholder="user1@gmail.com&#10;user2@gmail.com"></textarea>
            </div>

            <!-- CSV UPLOAD -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-3">
                <h3 class="text-sm font-bold uppercase text-emerald-400 tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-file-csv"></i> Target CSV Upload
                </h3>
                <div class="border border-dashed border-gray-800 rounded-xl p-3 bg-gray-950/50 text-center relative cursor-pointer hover:border-gray-700 transition">
                    <input type="file" id="csv_file" accept=".csv" onchange="uploadTargetCSV()" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
                    <i class="fa-solid fa-cloud-arrow-up text-lg text-gray-500 mb-1"></i>
                    <p class="text-xs font-semibold text-gray-300">Upload CSV File</p>
                </div>
                <div id="target-counter-pane" class="hidden text-xs bg-gray-950 border border-gray-800 p-2.5 rounded-xl flex items-center justify-between">
                    <span class="text-gray-400">CSV Targets:</span>
                    <span id="target-badge-count" class="bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded border border-emerald-500/20">0 Loaded</span>
                </div>
            </div>
        </div>

        <!-- COMPOSER & LOGS -->
        <div class="lg:col-span-2 space-y-6">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h3 class="text-sm font-bold uppercase text-white tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-pen-nib text-indigo-500"></i> Email Composer
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div class="space-y-3.5">
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Subject</label>
                            <input type="text" id="email_subject" value="Executive Strategic Update" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-gray-400 font-medium mb-1">Message Body (HTML Supported)</label>
                            <textarea id="email_body" rows="8" onkeyup="updateLivePreview()" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white font-mono focus:outline-none focus:border-indigo-500 resize-none" placeholder="<p>Dear [Name],</p><p>Welcome to [Company]!</p>"></textarea>
                        </div>
                        <div class="flex gap-3">
                            <button onclick="triggerBroadcastSequence()" id="start-btn" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl transition cursor-pointer text-center shadow-lg">
                                <i class="fa-solid fa-rocket"></i> Send Broadcast
                            </button>
                            <button onclick="terminateBroadcastSequence()" id="stop-btn" disabled class="bg-rose-600/20 text-rose-500 border border-rose-500/20 hover:bg-rose-500/30 font-bold px-4 rounded-xl transition cursor-pointer disabled:opacity-40">
                                Stop
                            </button>
                        </div>
                    </div>

                    <div class="flex flex-col border border-gray-800 rounded-xl overflow-hidden bg-gray-950">
                        <div class="bg-gray-900 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-800">
                            Live Shell Preview
                        </div>
                        <div class="flex-1 p-4 bg-white text-gray-800 overflow-y-auto max-h-[295px]" id="live-render-frame">
                            <div style="text-align: center; color: #94a3b8; padding-top: 60px;">
                                Type message to preview...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- LOG MONITOR -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-5">
                <h3 class="text-sm font-bold uppercase text-white tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-satellite-dish text-emerald-500"></i> Delivery Monitor
                </h3>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Progress</span>
                        <h4 id="progress-text" class="text-xl font-extrabold text-white">0 / 0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Delivered</span>
                        <h4 id="success-text" class="text-xl font-extrabold text-emerald-500">0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Failed</span>
                        <h4 id="failed-text" class="text-xl font-extrabold text-rose-500">0</h4>
                    </div>
                    <div class="bg-gray-950 border border-gray-800 p-3 rounded-xl">
                        <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Rate</span>
                        <h4 id="rate-text" class="text-xl font-extrabold text-indigo-400">0%</h4>
                    </div>
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-wide">Logs</label>
                    <div id="log-terminal" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3.5 h-44 overflow-y-auto text-[11px] font-mono text-gray-400 space-y-1.5">
                        <div class="text-gray-600">Awaiting dispatch operation...</div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let ingestedTargets = [];
        let synchronizationLoopInterval = null;

        function updateLivePreview() {
            let bodyContent = document.getElementById('email_body').value || "<p style='color:#94a3b8;'>Type your message...</p>";
            let processedPreview = bodyContent.replace('[Name]', 'Valued Client').replace('[Company]', 'Enterprise Corp');
            
            document.getElementById('live-render-frame').innerHTML = `
                <div style="font-family:Arial,sans-serif; background-color:#ffffff; border-radius:8px; padding:20px; border:1px solid #eef2f5;">
                    <div style="color:#4f46e5; font-weight:bold; font-size:16px; margin-bottom:10px;">Corporate Communication</div>
                    <div style="color:#334155; font-size:14px; line-height:1.5;">` + processedPreview + `</div>
                </div>`;
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
            alert(res.message);
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
            let manualEmails = document.getElementById('manual_emails').value.trim();
            if(ingestedTargets.length === 0 && !manualEmails) {
                return alert("Please enter manual email addresses or upload a CSV file.");
            }
            
            let fd = new FormData();
            fd.append('subject', document.getElementById('email_subject').value);
            fd.append('message_body', document.getElementById('email_body').value);
            fd.append('manual_emails', manualEmails);
            fd.append('targets', JSON.stringify(ingestedTargets));

            try {
                let response = await fetch('/api/start_broadcast', { method: 'POST', body: fd });
                let res = await response.json();
                
                if(res.success) {
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    
                    if(synchronizationLoopInterval) clearInterval(synchronizationLoopInterval);
                    synchronizationLoopInterval = setInterval(fetchEcosystemTelemetry, 1000);
                } else {
                    alert(res.message);
                }
            } catch(e) {
                alert("API Error: " + e.message);
            }
        }

        async function terminateBroadcastSequence() {
            await fetch('/api/stop_broadcast', { method: 'POST' });
        }

        async function fetchEcosystemTelemetry() {
            try {
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
                    term.innerHTML = `<div class="text-gray-600">Awaiting execution...</div>`;
                } else {
                    data.logs.forEach(log => {
                        term.innerHTML += `<div class="py-0.5 border-b border-gray-900/50 truncate">${log}</div>`;
                    });
                }

                if(!data.is_running) {
                    clearInterval(synchronizationLoopInterval);
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                }
            } catch(e) {}
        }
    </script>
</body>
</html>
"""

# =========================================================================
# ENTRY POINT
# =========================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
