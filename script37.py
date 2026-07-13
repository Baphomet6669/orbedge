import os
import smtplib
import imaplib
import email
import re
import time
import dns.resolver
import pandas as pd
import threading
import concurrent.futures
import matplotlib
# Render/Linux Container compatibility ke liye headless state engine optimization
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from flask import Blueprint, render_template_string, request, jsonify

# 1. DEFINE THE BLUEPRINT THAT THE CORE APP ROUTER IS EXPECTING
script37_bp = Blueprint('script37', __name__, static_folder='static')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Delta Agency Suite')
db_lock = threading.Lock()

class ZeroApiEmailEngine:
    def __init__(self, smtp_host, smtp_port, imap_host, imap_port, email_user, email_pass):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.user = email_user
        self.password = email_pass
        self.blocklist = set()

    def check_spam_score(self, subject, body):
        spam_words = ['free', 'click here', 'buy now', 'make money', 'earn cash', 
                      '100% free', 'guaranteed', 'urgent', 'winner', 'lottery', 'offer']
        score = 0
        text_to_check = (subject + " " + body).lower()
        found_triggers = []
        for word in spam_words:
            if word in text_to_check:
                score += 2
                found_triggers.append(word)
        if subject.isupper():
            score += 3
            found_triggers.append("ALL CAPS SUBJECT")
        status = "Safe" if score < 4 else ("Risky" if score < 7 else "High Spam Risk")
        return {"score": score, "status": status, "triggers": found_triggers}

    def verify_email_dns(self, email_address):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(regex, email_address):
            return False
        domain = email_address.split('@')[1]
        try:
            records = dns.resolver.resolve(domain, 'MX')
            return len(records) > 0
        except Exception:
            return False

    def sync_bounces(self):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port, timeout=10)
            mail.login(self.user, self.password)
            mail.select("inbox")
            status, messages = mail.search(None, '(OR SUBJECT "Delivery Status Notification" SUBJECT "unsubscribe")')
            if status == "OK" and messages[0]:
                for num in messages[0].split():
                    _, data = mail.fetch(num, '(RFC822)')
                    if data and data[0]:
                        msg = email.message_from_bytes(data[0][1])
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body += str(part.get_payload(decode=True))
                        else:
                            body = str(msg.get_payload(decode=True))
                        found_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body)
                        for e in found_emails:
                            if e.lower() != self.user.lower():
                                self.blocklist.add(e.lower())
            mail.close()
            mail.logout()
        except Exception:
            pass  # Fail gracefully in sandboxed environment if connection times out
        return len(self.blocklist)

    def process_single_email(self, lead, subject, template_str, index, logs, tracking_id):
        email_addr = lead.get('email', '').strip().lower()
        if not email_addr:
            return
        
        if email_addr in self.blocklist:
            with db_lock: logs.append({"email": email_addr, "status": "Suppressed (Blocklisted)"})
            return
            
        if not self.verify_email_dns(email_addr):
            with db_lock: logs.append({"email": email_addr, "status": "Failed (Invalid MX)"})
            return
            
        # Throttling algorithm based on pacing sequence to evade system limits
        base_delay = 1.5
        if index > 0 and index % 10 == 0:
            base_delay += 2.5
        time.sleep(base_delay)
        
        try:
            template = Template(template_str)
            html_body = template.render(name=lead.get('name', 'Subscriber'))
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = lead['email']
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=8) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, lead['email'], msg.as_string())
                
            with db_lock: logs.append({"email": email_addr, "status": "Success"})
        except Exception as err:
            with db_lock: logs.append({"email": email_addr, "status": f"SMTP Error: {str(err)}"})

def generate_analytics_chart(tracking_id, success, failed, blocked):
    if success == 0 and failed == 0 and blocked == 0:
        success = 1 # Fallback safeguard
        
    labels = ['Delivered', 'Failed/SMTP', 'Suppressed']
    sizes = [success, failed, blocked]
    colors = ['#10b981', '#ef4444', '#f59e0b']
    
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
        startangle=140, textprops=dict(color="w", weight="bold")
    )
    
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')
    
    for text in texts: text.set_color('#94a3b8')
    for autotext in autotexts: autotext.set_color('#0f172a')
        
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    graph_path = os.path.join(static_dir, f"{tracking_id}_delivery_report.png")
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return f"static/{tracking_id}_delivery_report.png"

# 2. ASSIGN PATH ROUTING TO THE BLUEPRINT
@script37_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@script37_bp.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    data = request.json or {}
    smtp_host = data.get('smtp_host')
    smtp_port = int(data.get('smtp_port', 587))
    imap_host = data.get('imap_host')
    imap_port = int(data.get('imap_port', 993))
    email_user = data.get('email_user')
    email_pass = data.get('email_pass')
    subject = data.get('subject', 'System Transmission')
    template_str = data.get('template', 'Hello {{name}}')
    raw_leads = data.get('leads', []) # Expects list of dicts [{"name":"X", "email":"Y"}]
    
    if not all([smtp_host, email_user, email_pass, raw_leads]):
        return jsonify({'success': False, 'message': 'Missing mandatory parameters or target lead vectors.'}), 400
        
    engine = ZeroApiEmailEngine(smtp_host, smtp_port, imap_host, imap_port, email_user, email_pass)
    
    # Run IMAP Sync locally before campaign launch
    blocklist_count = engine.sync_bounces()
    
    # Run local spam filter evaluation
    spam_report = engine.check_spam_score(subject, template_str)
    if spam_report['score'] >= 7:
        return jsonify({
            'success': False, 
            'message': f"Local safety engine aborted execution. Spam Rating Critical ({spam_report['score']}/10). Triggers: {', '.join(spam_report['triggers'])}"
        }), 400
        
    logs = []
    tracking_id = f"camp_{int(time.time())}"
    
    # Multi-threaded concurrent delivery system execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(engine.process_single_email, lead, subject, template_str, idx, logs, tracking_id) 
            for idx, lead in enumerate(raw_leads)
        ]
        concurrent.futures.wait(futures)
        
    # Analyze array data
    success_count = sum(1 for item in logs if item['status'] == 'Success')
    suppressed_count = sum(1 for item in logs if 'Suppressed' in item['status'])
    failed_count = len(logs) - (success_count + suppressed_count)
    
    chart_url = generate_analytics_chart(tracking_id, success_count, failed_count, suppressed_count)
    
    return jsonify({
        'success': True,
        'tracking_id': tracking_id,
        'spam_score': spam_report['score'],
        'spam_status': spam_report['status'],
        'spam_triggers': spam_report['triggers'],
        'sync_blocked_total': blocklist_count,
        'logs': logs,
        'chart_url': chart_url
    })

# ULTRA PREMIUM CORROSIVE CYBERPUNK WEB UI INTERFACE
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Broadcast Engine Terminal</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #0f172a; 
            color: #f8fafc;
        }
        .cyber-card {
            background: #1e293b;
            border: 1px solid #334155;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        }
        .glow-accent {
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
        }
    </style>
</head>
<body class="antialiased selection:bg-emerald-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Control Panel Nav Sidebar -->
        <aside class="w-full lg:w-80 bg-slate-950 flex flex-col border-b lg:border-r border-slate-800 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-lg glow-accent">
                    <i class="fa-solid fa-paper-plane text-xl text-white"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">NexusMail</h2>
                    <span class="text-[10px] text-emerald-400 font-mono uppercase tracking-widest mt-1 block">ZERO-API MATRIX v37</span>
                </div>
            </div>
            
            <div class="space-y-4 flex-1">
                <div class="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                    <label class="text-[11px] font-mono text-slate-400 uppercase block mb-1">Target Distribution Status</label>
                    <div class="flex items-center gap-2 text-sm text-emerald-400 font-bold">
                        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span> Active SMTP Server Listening
                    </div>
                </div>
            </div>
            
            <div class="pt-4 border-t border-slate-800 text-center">
                <span class="text-[11px] text-slate-500 font-mono">Status: Decoupled Socket Active</span>
            </div>
        </aside>

        <!-- Configuration Main Canvas -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-800 pb-6 mb-8 gap-4">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white">{{ company }}</h1>
                    <p class="text-sm text-slate-400 mt-1">Zero-Dependency Autonomous Local Email Marketing Architecture</p>
                </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <!-- Parameters Config Panel -->
                <div class="cyber-card p-6 rounded-2xl space-y-4">
                    <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 mb-2">
                        <i class="fa-solid fa-sliders text-emerald-400"></i> Gateway Array Configurations
                    </h3>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">SMTP Host</label>
                            <input type="text" id="smtpHost" placeholder="mail.agency.com" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">SMTP Port</label>
                            <input type="number" id="smtpPort" value="587" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">IMAP Host (Bounce Clean)</label>
                            <input type="text" id="imapHost" placeholder="mail.agency.com" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">IMAP Port</label>
                            <input type="number" id="imapPort" value="993" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">Sender Email User</label>
                            <input type="email" id="emailUser" placeholder="sender@agency.com" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 font-mono mb-1 block">Sender Secure Password</label>
                            <input type="password" id="emailPass" placeholder="******" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono">
                        </div>
                    </div>

                    <hr class="border-slate-800 my-2">

                    <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-envelope-open-text text-emerald-400"></i> Content & Target Payload
                    </h3>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Subject Line</label>
                        <input type="text" id="emailSubject" placeholder="Exclusive Partnership Offer" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                    </div>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">HTML Template (Supports {{ name }})</label>
                        <textarea id="emailTemplate" rows="4" placeholder="<html><body><h2>Hello {{ name }}</h2></body></html>" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"></textarea>
                    </div>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Target JSON Batch Matrix</label>
                        <textarea id="emailLeads" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-emerald-400 focus:outline-none focus:border-emerald-500 font-mono">[{"name": "Rajesh Kumar", "email": "rajesh@gmail.com"}, {"name": "Test Frame", "email": "deadmail@fake-domain-xyz.com"}]</textarea>
                    </div>

                    <button onclick="launchCampaignPipeline()" class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-xl text-xs transition shadow-lg hover:shadow-emerald-500/20 cursor-pointer uppercase tracking-wider">
                        Deploy System Pulse
                    </button>
                </div>

                <!-- Display Terminal Dashboard Logs -->
                <div class="space-y-6 flex flex-col">
                    <div id="loader" class="hidden text-center py-20 cyber-card rounded-2xl flex-1 flex flex-col justify-center items-center">
                        <i class="fa-solid fa-circle-notch fa-spin text-4xl text-emerald-400"></i>
                        <p class="text-xs text-slate-400 mt-4 font-mono animate-pulse">Running IMAP cleansing & executing delivery loops...</p>
                    </div>

                    <div id="outputContainer" class="hidden space-y-6 flex-1">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="cyber-card p-4 rounded-xl text-center">
                                <span class="text-[10px] font-mono uppercase text-slate-400 block">Local Spam Audit</span>
                                <span id="spamScore" class="text-lg font-bold block mt-1">0/10</span>
                            </div>
                            <div class="cyber-card p-4 rounded-xl text-center">
                                <span class="text-[10px] font-mono uppercase text-slate-400 block">IMAP Blocked Vector</span>
                                <span id="syncBlocked" class="text-lg font-bold text-amber-400 block mt-1">0</span>
                            </div>
                        </div>

                        <div class="cyber-card p-4 rounded-2xl flex justify-center items-center">
                            <img id="deliveryChart" src="" alt="Live Stream Performance Analytics" class="max-h-52 object-contain rounded-xl">
                        </div>

                        <div class="cyber-card p-4 rounded-2xl flex-1 flex flex-col">
                            <h4 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 font-mono">Real-time Stream Logs</h4>
                            <div id="logTerminal" class="bg-slate-950 border border-slate-800 p-3 rounded-xl font-mono text-[11px] overflow-y-auto max-h-44 space-y-1 flex-1"></div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function launchCampaignPipeline() {
            const payload = {
                smtp_host: document.getElementById('smtpHost').value.trim(),
                smtp_port: document.getElementById('smtpPort').value,
                imap_host: document.getElementById('imapHost').value.trim(),
                imap_port: document.getElementById('imapPort').value,
                email_user: document.getElementById('emailUser').value.trim(),
                email_pass: document.getElementById('emailPass').value,
                subject: document.getElementById('emailSubject').value.trim(),
                template: document.getElementById('emailTemplate').value,
                leads: JSON.parse(document.getElementById('emailLeads').value)
            };

            if(!payload.smtp_host || !payload.email_user || !payload.email_pass) {
                return alert("System Error: Mandatory transmission vector objects missing.");
            }

            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('outputContainer').classList.add('hidden');

            try {
                const response = await fetch('./api/dispatch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                document.getElementById('loader').classList.add('hidden');
                
                if(data.success) {
                    document.getElementById('spamScore').innerText = `${data.spam_score}/10 (${data.spam_status})`;
                    document.getElementById('syncBlocked').innerText = data.sync_blocked_total;
                    document.getElementById('deliveryChart').src = './' + data.chart_url + '?cache=' + new Date().getTime();
                    
                    const logTerminal = document.getElementById('logTerminal');
                    logTerminal.innerHTML = '';
                    data.logs.forEach(log => {
                        const isSuccess = log.status === 'Success';
                        const colorClass = isSuccess ? 'text-emerald-400' : 'text-rose-400';
                        logTerminal.innerHTML += `<div class="${colorClass}">[>>>] Target: ${log.email} | Status: ${log.status}</div>`;
                    });
                    
                    document.getElementById('outputContainer').classList.remove('hidden');
                } else {
                    alert("Pipeline Failure: " + data.message);
                }
            } catch(err) {
                document.getElementById('loader').classList.add('hidden');
                alert("Critical Signal Interruption: Verify structural parameters.");
            }
        }
    </script>
</body>
</html>
"""

