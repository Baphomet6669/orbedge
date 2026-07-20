import os
import re
import smtplib
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Blueprint, render_template_string, request, jsonify, session

# =========================================================================
# FLASK BLUEPRINT DEFINITION
# =========================================================================
script43_bp = Blueprint('script43', __name__)

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def send_single_email(smtp_host, smtp_port, username, password, sender_email, recipient, subject, body, use_tls=True):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject

        # Attach plain text and HTML body
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(f"<div>{body.replace('\n', '<br>')}</div>", "html"))

        # Connect to SMTP Server
        server = smtplib.SMTP(smtp_host, int(smtp_port), timeout=10)
        if use_tls:
            server.starttls()
        
        if username and password:
            server.login(username, password)

        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()

        return {"email": recipient, "status": "Success", "error": None}
    except Exception as e:
        return {"email": recipient, "status": "Failed", "error": str(e)}

# =========================================================================
# CONTROLLER ROUTING LOGIC
# =========================================================================
@script43_bp.route('/')
def index():
    if 'logged_in' not in session:
        return "<h3 style='color:white; font-family:sans-serif;'>ACCESS DENIED: Please log in from main dashboard.</h3>", 403
    return render_template_string(UI_LAYOUT)

@script43_bp.route('/api/send-bulk', methods=['POST'])
def handle_bulk_mail():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized Terminal"}), 401

    # Form parameters
    smtp_host = request.form.get('smtp_host', '').strip()
    smtp_port = request.form.get('smtp_port', '587').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    sender_email = request.form.get('sender_email', '').strip()
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '').strip()
    recipients_raw = request.form.get('recipients', '').strip()
    use_tls = request.form.get('use_tls') == 'true'

    if not all([smtp_host, smtp_port, sender_email, subject, body, recipients_raw]):
        return jsonify({"success": False, "message": "All required parameters must be provided."})

    # Parse recipients list
    raw_list = [e.strip() for e in re.split(r'[\n,;]+', recipients_raw) if e.strip()]
    valid_recipients = list(set([e for e in raw_list if validate_email(e)]))

    if not valid_recipients:
        return jsonify({"success": False, "message": "No valid recipient email addresses found."})

    results = []
    success_count = 0
    failed_count = 0

    # ThreadPool execution for fast concurrent sending
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                send_single_email,
                smtp_host,
                smtp_port,
                username,
                password,
                sender_email,
                recipient,
                subject,
                body,
                use_tls
            )
            for recipient in valid_recipients
        ]

        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            if res["status"] == "Success":
                success_count += 1
            else:
                failed_count += 1

    summary_log = f"================================================\n" \
                  f"         BULK MAIL DELIVERY REPORT             \n" \
                  f"================================================\n" \
                  f"SMTP Server     : {smtp_host}:{smtp_port}\n" \
                  f"Sender Email    : {sender_email}\n" \
                  f"Total Recipient : {len(valid_recipients)}\n" \
                  f"Successfully Sent: {success_count}\n" \
                  f"Delivery Failed : {failed_count}\n" \
                  f"Timestamp       : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n" \
                  f"================================================"

    return jsonify({
        "success": True,
        "total": len(valid_recipients),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
        "summary": summary_log
    })

# =========================================================================
# ULTRA MODERN NEON CYBERPUNK UI LAYOUT
# =========================================================================
UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Bulk Mail Automation Suite</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f3f4f6; }
        .heading-font { font-family: 'Space Grotesk', sans-serif; }
        .cyber-card { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .terminal-box { font-family: 'Courier New', monospace; background: #050811; border: 1px solid #1f2937; }
        .glow-indigo { box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.25); }
    </style>
</head>
<body class="antialiased selection:bg-indigo-500 selection:text-white pb-12">

    <div class="max-w-[1450px] mx-auto p-4 md:p-8 space-y-6">
        
        <!-- HEADER TOP BANNER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-2xl font-bold heading-font tracking-wide text-white flex items-center gap-2">
                    <i class="fa-paper-plane text-indigo-400"></i> Enterprise Bulk Email Dispatcher
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Multi-Threaded SMTP Delivery • Logs • Diagnostics</p>
            </div>
            <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
            </a>
        </div>

        <!-- MAIN FORM AND METRICS -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- LEFT INPUT FORM PANEL -->
            <div class="lg:col-span-2 cyber-card p-6 rounded-2xl glow-indigo space-y-4">
                <form id="emailForm" onsubmit="triggerSendSequence(event)" class="space-y-4">
                    
                    <h3 class="text-sm font-bold text-white heading-font border-b border-gray-800 pb-2">SMTP Server Configuration</h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                            <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">SMTP Host</label>
                            <input type="text" id="smtp_host" required placeholder="smtp.gmail.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                        </div>
                        <div>
                            <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Port</label>
                            <input type="number" id="smtp_port" value="587" required class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                        </div>
                        <div>
                            <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Sender Email</label>
                            <input type="email" id="sender_email" required placeholder="sender@example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Username</label>
                            <input type="text" id="username" placeholder="Optional" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                        </div>
                        <div>
                            <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Password / App Password</label>
                            <input type="password" id="password" placeholder="Optional" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                        </div>
                    </div>

                    <div class="flex items-center gap-2 pt-1">
                        <input type="checkbox" id="use_tls" checked class="w-4 h-4 rounded bg-gray-950 border-gray-800 text-indigo-600 focus:ring-0">
                        <label for="use_tls" class="text-xs text-gray-300 font-medium">Use STARTTLS Encryption</label>
                    </div>

                    <h3 class="text-sm font-bold text-white heading-font border-b border-gray-800 pb-2 pt-2">Message & Recipients</h3>

                    <div>
                        <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Subject</label>
                        <input type="text" id="subject" required placeholder="Newsletter Header" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono">
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Recipient Emails (Comma or line separated)</label>
                        <textarea id="recipients" rows="4" required placeholder="user1@domain.com, user2@domain.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono"></textarea>
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Email Body Content</label>
                        <textarea id="body" rows="5" required placeholder="Write your message here..." class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white font-mono"></textarea>
                    </div>

                    <button type="submit" id="submitBtn" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider py-3.5 rounded-xl cursor-pointer transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Start Bulk Email Dispatch</span>
                    </button>
                </form>
            </div>

            <!-- RIGHT MONITORING PANEL -->
            <div class="space-y-6">
                
                <!-- SUMMARY COUNTERS -->
                <div class="grid grid-cols-3 gap-3">
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500 text-center">
                        <span class="text-[10px] uppercase text-gray-400 font-bold block">Total</span>
                        <h3 id="cnt-total" class="text-base font-bold text-white mt-1">0</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500 text-center">
                        <span class="text-[10px] uppercase text-gray-400 font-bold block">Success</span>
                        <h3 id="cnt-success" class="text-base font-bold text-emerald-400 mt-1">0</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-rose-500 text-center">
                        <span class="text-[10px] uppercase text-gray-400 font-bold block">Failed</span>
                        <h3 id="cnt-failed" class="text-base font-bold text-rose-400 mt-1">0</h3>
                    </div>
                </div>

                <!-- DETAILED LOG TERMINAL -->
                <div class="cyber-card p-6 rounded-2xl space-y-3">
                    <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-purple-400"></i> Dispatch Execution Log
                    </h3>
                    <pre id="summaryLog" class="terminal-box p-4 rounded-xl text-[11px] text-emerald-400 whitespace-pre-wrap leading-relaxed min-h-48">Waiting for job submission...</pre>
                </div>

                <!-- INDIVIDUAL RESULTS LIST -->
                <div class="cyber-card p-6 rounded-2xl space-y-3">
                    <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                        <i class="fa-solid fa-list-check text-indigo-400"></i> Recipient Status
                    </h3>
                    <div id="resultsContainer" class="space-y-2 max-h-64 overflow-y-auto font-mono text-xs">
                        <p class="text-gray-500 italic text-[11px]">No emails processed yet.</p>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <script>
        async function triggerSendSequence(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('submitBtn');
            const spinIcon = document.getElementById('spinIcon');

            submitBtn.disabled = true;
            spinIcon.classList.remove('hidden');

            let fd = new FormData();
            fd.append('smtp_host', document.getElementById('smtp_host').value);
            fd.append('smtp_port', document.getElementById('smtp_port').value);
            fd.append('sender_email', document.getElementById('sender_email').value);
            fd.append('username', document.getElementById('username').value);
            fd.append('password', document.getElementById('password').value);
            fd.append('use_tls', document.getElementById('use_tls').checked);
            fd.append('subject', document.getElementById('subject').value);
            fd.append('body', document.getElementById('body').value);
            fd.append('recipients', document.getElementById('recipients').value);

            try {
                let response = await fetch('/script43/api/send-bulk', { method: 'POST', body: fd });
                let data = await response.json();

                if (data.success) {
                    document.getElementById('cnt-total').innerText = data.total;
                    document.getElementById('cnt-success').innerText = data.success_count;
                    document.getElementById('cnt-failed').innerText = data.failed_count;
                    document.getElementById('summaryLog').innerText = data.summary;

                    const container = document.getElementById('resultsContainer');
                    container.innerHTML = '';
                    data.results.forEach(r => {
                        const statusColor = r.status === 'Success' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-rose-500/30 text-rose-400 bg-rose-500/10';
                        container.innerHTML += `
                            <div class="p-2 bg-gray-950 border ${statusColor} rounded-lg flex items-center justify-between text-[11px]">
                                <span class="truncate">${r.email}</span>
                                <span class="font-bold uppercase">${r.status}</span>
                            </div>
                        `;
                    });
                } else {
                    alert(data.message || "Bulk dispatch failed.");
                }
            } catch (err) {
                console.error("Dispatch Exception:", err);
                alert("Server execution error or timeout occurred.");
            } finally {
                submitBtn.disabled = false;
                spinIcon.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

