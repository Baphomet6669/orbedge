import os
import smtplib
import imaplib
import email
import re
import time
import socket
import dns.resolver
import pandas as pd
import threading
import concurrent.futures
import matplotlib
# Headless mode for server environments (Render/Linux compatibility)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from flask import Blueprint, render_template_string, request, jsonify

# 1. BLUEPRINT SETUP
script37_bp = Blueprint('script37', __name__, static_folder='static')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Delta Agency Suite')
db_lock = threading.Lock()

class EnterpriseEmailEngine:
    def __init__(self, smtp_credentials, imap_config=None):
        """
        smtp_credentials: List of dicts [{'host', 'port', 'user', 'pass'}] for rotation.
        """
        self.smtp_pool = smtp_credentials
        self.imap_config = imap_config or {}
        self.blocklist = set()
        self.smtp_index = 0

    def get_next_smtp(self):
        """Rotates through provided SMTP servers to balance load and protect reputation."""
        if not self.smtp_pool:
            return None
        with db_lock:
            config = self.smtp_pool[self.smtp_index % len(self.smtp_pool)]
            self.smtp_index += 1
            return config

    def check_spam_score(self, subject, body):
        spam_words = ['free', 'click here', 'buy now', 'make money', 'earn cash', 
                      '100% free', 'guaranteed', 'urgent', 'winner', 'lottery', 
                      'get paid', 'act fast', 'limited time', 'risk-free']
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

    def verify_dns_and_health(self, domain_or_email, check_auth=False):
        """
        Verifies MX records. If check_auth is True, it also scans SPF, DKIM, DMARC 
        records for security/delivery health.
        """
        domain = domain_or_email.split('@')[-1] if '@' in domain_or_email else domain_or_email
        result = {"valid": False, "spf": "None", "dmarc": "None", "mx": []}
        try:
            # MX verification
            mx_records = dns.resolver.resolve(domain, 'MX')
            result["mx"] = [str(r.exchange) for r in mx_records]
            result["valid"] = len(result["mx"]) > 0

            if check_auth:
                # SPF check
                try:
                    spf_records = dns.resolver.resolve(domain, 'TXT')
                    for r in spf_records:
                        txt_data = str(r)
                        if "v=spf1" in txt_data:
                            result["spf"] = txt_data
                except Exception:
                    pass
                
                # DMARC check
                try:
                    dmarc_records = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
                    for r in dmarc_records:
                        txt_data = str(r)
                        if "v=DMARC1" in txt_data:
                            result["dmarc"] = txt_data
                except Exception:
                    pass
        except Exception:
            pass
        return result

    def sync_bounces(self):
        """Scans specified IMAP folder to auto-harvest bounces/unsubscribes into blocklist."""
        if not self.imap_config or not self.imap_config.get('host'):
            return 0
        try:
            mail = imaplib.IMAP4_SSL(self.imap_config['host'], int(self.imap_config.get('port', 993)), timeout=10)
            mail.login(self.imap_config['user'], self.imap_config['pass'])
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
                            self.blocklist.add(e.lower())
            mail.close()
            mail.logout()
        except Exception:
            pass
        return len(self.blocklist)

    def process_single_email(self, lead, subject, template_str, index, logs, tracking_id):
        email_addr = lead.get('email', '').strip().lower()
        name = lead.get('name', 'Subscriber')
        if not email_addr:
            return
        
        if email_addr in self.blocklist:
            with db_lock: logs.append({"email": email_addr, "status": "Suppressed (Blocklisted)"})
            return
            
        dns_health = self.verify_dns_and_health(email_addr)
        if not dns_health["valid"]:
            with db_lock: logs.append({"email": email_addr, "status": "Failed (Invalid MX/Domain)"})
            return
            
        # Pacing throttling
        base_delay = 1.0
        if index > 0 and index % 5 == 0:
            base_delay += 2.0
        time.sleep(base_delay)
        
        # Pull rotated server
        smtp_profile = self.get_next_smtp()
        if not smtp_profile:
            with db_lock: logs.append({"email": email_addr, "status": "Failed (No Active SMTP Configuration)"})
            return

        try:
            template = Template(template_str)
            html_body = template.render(name=name, email=email_addr)
            
            # Simple embedded pixel simulation tracker
            tracking_pixel = f'<img src="https://{COMPANY_NAME.lower().replace(" ", "")}.com/track/{tracking_id}?u={email_addr}" width="1" height="1" style="display:none;" />'
            html_body += tracking_pixel

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_profile['user']
            msg['To'] = lead['email']
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(smtp_profile['host'], int(smtp_profile['port']), timeout=10) as server:
                server.starttls()
                server.login(smtp_profile['user'], smtp_profile['pass'])
                server.sendmail(smtp_profile['user'], lead['email'], msg.as_string())
                
            with db_lock: logs.append({"email": email_addr, "status": "Success", "gateway": smtp_profile['host']})
        except Exception as err:
            with db_lock: logs.append({"email": email_addr, "status": f"SMTP Error ({smtp_profile['host']}): {str(err)}"})

def generate_analytics_chart(tracking_id, success, failed, blocked):
    if success == 0 and failed == 0 and blocked == 0:
        success = 1  # Fallback
        
    labels = ['Delivered', 'Failed/SMTP', 'Suppressed']
    sizes = [success, failed, blocked]
    colors = ['#10b981', '#ef4444', '#f59e0b']
    
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
        startangle=140, textprops=dict(color="w", weight="bold")
    )
    
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    for text in texts: text.set_color('#94a3b8')
    for autotext in autotexts: autotext.set_color('#0f172a')
        
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    graph_path = os.path.join(static_dir, f"{tracking_id}_delivery_report.png")
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return f"static/{tracking_id}_delivery_report.png"

# 2. ENDPOINTS
@script37_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@script37_bp.route('/api/verify-domain', methods=['POST'])
def api_verify_domain():
    data = request.json or {}
    domain = data.get('domain')
    if not domain:
        return jsonify({'success': False, 'message': 'Domain is required'}), 400
    engine = EnterpriseEmailEngine([])
    health = engine.verify_dns_and_health(domain, check_auth=True)
    return jsonify({'success': True, 'health': health})

@script37_bp.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    data = request.json or {}
    
    # Extract multiple SMTP profiles for rotation
    smtp_servers = data.get('smtp_servers', [])
    imap_host = data.get('imap_host')
    imap_port = int(data.get('imap_port', 993))
    email_user = data.get('email_user')
    email_pass = data.get('email_pass')
    
    subject = data.get('subject', 'System Transmission')
    template_str = data.get('template', 'Hello {{name}}')
    raw_leads = data.get('leads', [])
    
    if not smtp_servers or not raw_leads:
        return jsonify({'success': False, 'message': 'Missing SMTP configurations or target lead data.'}), 400
        
    imap_config = {
        'host': imap_host,
        'port': imap_port,
        'user': email_user,
        'pass': email_pass
    } if imap_host and email_user else None

    engine = EnterpriseEmailEngine(smtp_servers, imap_config)
    
    # Run IMAP Sync
    blocklist_count = engine.sync_bounces()
    
    # Run Spam Evaluator
    spam_report = engine.check_spam_score(subject, template_str)
    if spam_report['score'] >= 9:
        return jsonify({
            'success': False, 
            'message': f"Aborted: High risk of spam blocklist. Rating: ({spam_report['score']}/14). Triggers: {', '.join(spam_report['triggers'])}"
        }), 400
        
    logs = []
    tracking_id = f"camp_{int(time.time())}"
    
    # Threaded delivery execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(engine.process_single_email, lead, subject, template_str, idx, logs, tracking_id) 
            for idx, lead in enumerate(raw_leads)
        ]
        concurrent.futures.wait(futures)
        
    success_count = sum(1 for item in logs if item['status'] == 'Success')
    suppressed_count = sum(1 for item in logs if 'Suppressed' in item['status'])
    failed_count = len(logs) - (success_count + suppressed_count)
    
    chart_url = generate_analytics_chart(tracking_id, success_count, failed_count, suppressed_count)
    
    return jsonify({
        'success': True,
        'tracking_id': tracking_id,
        'spam_score': f"{spam_report['score']}/14",
        'spam_status': spam_report['status'],
        'spam_triggers': spam_report['triggers'],
        'sync_blocked_total': blocklist_count,
        'logs': logs,
        'chart_url': chart_url
    })

# UPPER PREMIUM MODERN BLACK-HAT TERMINAL UI
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Enterprise Broadcast Suite</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #090d16; 
            color: #f1f5f9;
        }
        .cyber-card {
            background: #0f172a;
            border: 1px solid #1e293b;
            box-shadow: 0 4px 24px 0 rgba(0, 0, 0, 0.6);
        }
        .glow-green {
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
        }
    </style>
</head>
<body class="antialiased selection:bg-emerald-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar -->
        <aside class="w-full lg:w-80 bg-slate-950 flex flex-col border-b lg:border-r border-slate-900 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-xl shadow-lg glow-green">
                    <i class="fa-solid fa-bolt text-xl text-slate-950"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">ApexMail</h2>
                    <span class="text-[10px] text-emerald-400 font-mono uppercase tracking-widest mt-1 block">V37 ENTERPRISE</span>
                </div>
            </div>
            
            <div class="space-y-4 flex-1">
                <div class="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                    <label class="text-[11px] font-mono text-slate-400 uppercase block mb-1">Domain Health Check</label>
                    <div class="flex gap-2">
                        <input type="text" id="domainVerifyInput" placeholder="agency.com" class="bg-slate-950 text-xs border border-slate-700 rounded p-1 w-full text-white font-mono">
                        <button onclick="verifyDomainHealth()" class="bg-emerald-500 text-slate-950 text-xs px-2 py-1 rounded font-bold cursor-pointer"><i class="fa-solid fa-magnifying-glass"></i></button>
                    </div>
                    <div id="domainReport" class="text-[10px] text-slate-400 font-mono mt-2 space-y-1 hidden"></div>
                </div>
            </div>
            
            <div class="pt-4 border-t border-slate-900 text-center">
                <span class="text-[10px] text-slate-500 font-mono">Status: Decoupled Multi-Server Port Active</span>
            </div>
        </aside>

        <!-- Main Area -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-900 pb-6 mb-8">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white">{{ company }}</h1>
                    <p class="text-sm text-slate-400 mt-1">Industrial-Grade Rotator Email System with DNS Auth validation</p>
                </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <!-- Inputs -->
                <div class="cyber-card p-6 rounded-2xl space-y-4">
                    <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 mb-2">
                        <i class="fa-solid fa-server text-emerald-400"></i> SMTP Rotator Pools
                    </h3>
                    
                    <div id="smtpContainer" class="space-y-3">
                        <!-- Default SMTP inputs inside an array wrapper -->
                        <div class="smtp-row grid grid-cols-12 gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800">
                            <input type="text" placeholder="smtp.host.com" class="col-span-5 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono" value="">
                            <input type="number" placeholder="587" class="col-span-2 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono" value="587">
                            <input type="email" placeholder="user@domain.com" class="col-span-3 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono" value="">
                            <input type="password" placeholder="pass" class="col-span-2 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono">
                        </div>
                    </div>
                    <button onclick="addSmtpRow()" class="text-xs text-emerald-400 hover:text-emerald-300 font-mono flex items-center gap-1 cursor-pointer"><i class="fa-solid fa-plus-circle"></i> Add Server to Rotator Pool</button>

                    <hr class="border-slate-800">

                    <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-envelope text-emerald-400"></i> Content & Target Data
                    </h3>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Subject Line</label>
                        <input type="text" id="emailSubject" value="Special Strategic Update for {{ name }}" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white">
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="text-xs text-slate-400 font-mono block">HTML Body (Supports Jinja: {{ name }}, {{ email }})</label>
                            <button onclick="loadSampleTemplate()" class="text-[10px] text-emerald-400 hover:underline">Insert High-Converting HTML</button>
                        </div>
                        <textarea id="emailTemplate" rows="5" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white font-mono"><html><body><h3>Hi {{ name }},</h3><p>Let's scale your operations.</p></body></html></textarea>
                    </div>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Target JSON Batch Matrix</label>
                        <textarea id="emailLeads" rows="3" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-emerald-400 font-mono">[{"name": "Shivam", "email": "test@example.com"}]</textarea>
                    </div>

                    <button onclick="launchPipeline()" class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-xl text-xs transition shadow-lg glow-green cursor-pointer uppercase tracking-wider">
                        Deploy System Pulse
                    </button>
                </div>

                <!-- Display Logs -->
                <div class="space-y-6 flex flex-col">
                    <div id="loader" class="hidden text-center py-20 cyber-card rounded-2xl flex-1 flex flex-col justify-center items-center border border-slate-800">
                        <i class="fa-solid fa-circle-notch fa-spin text-4xl text-emerald-400"></i>
                        <p class="text-xs text-slate-400 mt-4 font-mono animate-pulse">Filtering spam triggers, verifying MX records & starting sending pool...</p>
                    </div>

                    <div id="outputContainer" class="hidden space-y-6 flex-1">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="cyber-card p-4 rounded-xl text-center border border-slate-800">
                                <span class="text-[10px] font-mono uppercase text-slate-400 block">System Spam Rating</span>
                                <span id="spamScore" class="text-lg font-bold block mt-1">0/14</span>
                            </div>
                            <div class="cyber-card p-4 rounded-xl text-center border border-slate-800">
                                <span class="text-[10px] font-mono uppercase text-slate-400 block">Bounced Blocklist Size</span>
                                <span id="syncBlocked" class="text-lg font-bold text-amber-400 block mt-1">0</span>
                            </div>
                        </div>

                        <div class="cyber-card p-4 rounded-2xl flex justify-center items-center border border-slate-800">
                            <img id="deliveryChart" src="" alt="Campaign performance analytical visualization" class="max-h-52 object-contain rounded-xl">
                        </div>

                        <div class="cyber-card p-4 rounded-2xl flex-1 flex flex-col border border-slate-800">
                            <h4 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 font-mono">Real-time Stream Logs</h4>
                            <div id="logTerminal" class="bg-slate-950 border border-slate-900 p-3 rounded-xl font-mono text-[11px] overflow-y-auto max-h-44 space-y-1 flex-1"></div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function addSmtpRow() {
            const container = document.getElementById('smtpContainer');
            const newRow = document.createElement('div');
            newRow.className = "smtp-row grid grid-cols-12 gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800";
            newRow.innerHTML = `
                <input type="text" placeholder="smtp.host.com" class="col-span-5 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono">
                <input type="number" placeholder="587" class="col-span-2 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono" value="587">
                <input type="email" placeholder="user@domain.com" class="col-span-3 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono">
                <input type="password" placeholder="pass" class="col-span-2 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono">
            `;
            container.appendChild(newRow);
        }

        function loadSampleTemplate() {
            document.getElementById('emailTemplate').value = `<!DOCTYPE html>
<html>
<body style="background-color: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; padding: 30px; border-radius: 10px; border: 1px solid #334155;">
    <h2 style="color: #10b981;">Hi \x7b\x7b name \x7d\x7d,</h2>
    <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1;">We have generated a custom security diagnosis report for your associated domain.</p>
    <a href="#" style="background-color: #10b981; color: #0f172a; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 15px;">Unlock Access Portfolio</a>
  </div>
</body>
</html>`;
        }

        async function verifyDomainHealth() {
            const domain = document.getElementById('domainVerifyInput').value.trim();
            if(!domain) return alert("Enter domain to inspect");
            const reportDiv = document.getElementById('domainReport');
            reportDiv.innerHTML = "Checking...";
            reportDiv.classList.remove('hidden');

            try {
                const res = await fetch('./api/verify-domain', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ domain })
                });
                const data = await res.json();
                if(data.success) {
                    const health = data.health;
                    reportDiv.innerHTML = `
                        <div class="text-emerald-400">MX Verified: \x7b\x7b health.valid ? 'Active ✓' : 'Failed ✗' \x7d\x7d</div>
                        <div class="truncate">SPF: \x7b\x7b health.spf \x7d\x7d</div>
                        <div class="truncate">DMARC: \x7b\x7b health.dmarc \x7d\x7d</div>
                    `;
                } else {
                    reportDiv.innerHTML = "Error analyzing domain";
                }
            } catch {
                reportDiv.innerHTML = "Network connection failed";
            }
        }

        async function launchPipeline() {
            const rows = document.querySelectorAll('.smtp-row');
            const smtp_servers = [];
            rows.forEach(row => {
                const inputs = row.querySelectorAll('input');
                if (inputs[0].value.trim() && inputs[2].value.trim()) {
                    smtp_servers.push({
                        host: inputs[0].value.trim(),
                        port: inputs[1].value,
                        user: inputs[2].value.trim(),
                        pass: inputs[3].value
                    });
                }
            });

            if(smtp_servers.length === 0) {
                return alert("Please configure at least one valid SMTP profile.");
            }

            const payload = {
                smtp_servers: smtp_servers,
                subject: document.getElementById('emailSubject').value.trim(),
                template: document.getElementById('emailTemplate').value,
                leads: JSON.parse(document.getElementById('emailLeads').value)
            };

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
                    document.getElementById('spamScore').innerText = `${data.spam_score} (${data.spam_status})`;
                    document.getElementById('syncBlocked').innerText = data.sync_blocked_total;
                    document.getElementById('deliveryChart').src = './' + data.chart_url + '?cache=' + new Date().getTime();
                    
                    const logTerminal = document.getElementById('logTerminal');
                    logTerminal.innerHTML = '';
                    data.logs.forEach(log => {
                        const isSuccess = log.status === 'Success';
                        const colorClass = isSuccess ? 'text-emerald-400' : 'text-rose-400';
                        logTerminal.innerHTML += `<div class="\x7b\x7bcolorClass\x7d\x7d">[>>>] Target: \x7b\x7b log.email \x7d\x7d | Status: \x7b\x7b log.status \x7d\x7d | Gateway: \x7b\x7b log.gateway || 'None' \x7d\x7d</div>`;
                    });
                    
                    document.getElementById('outputContainer').classList.remove('hidden');
                } else {
                    alert("Pipeline Failure: " + data.message);
                }
            } catch(err) {
                document.getElementById('loader').classList.add('hidden');
                alert("Critical System Interruption: Verify structural parameters.");
            }
        }
    </script>
</body>
</html>
"""

