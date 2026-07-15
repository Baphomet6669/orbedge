import os
import smtplib
import imaplib
import email
import re
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Blueprint, render_template_string, request, jsonify

# 1. BLUEPRINT CONFIGURATION
script38_bp = Blueprint('script38', __name__, static_folder='static')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Delta Agency Suite')
DEFAULT_MAILBOX = "shivam@yourdomain.com" # Apne actual configured custom email se badlein

class ApexEmailTerminal:
    def __init__(self, smtp_host, smtp_port, imap_host, imap_port, email_user, email_pass):
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.imap_host = imap_host
        self.imap_port = int(imap_port)
        self.user = email_user
        self.password = email_pass

    def send_mail(self, to_email, subject, html_content):
        """Sends an outgoing email using configured SMTP settings"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, to_email, msg.as_string())
            return {"success": True, "message": "Email dispatched successfully!"}
        except Exception as e:
            return {"success": False, "message": f"SMTP Error: {str(e)}"}

    def fetch_inbox(self, limit=10):
        """Connects via IMAP to read recently received emails"""
        received_mails = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port, timeout=10)
            mail.login(self.user, self.password)
            mail.select("inbox")
            
            # Fetch last 'limit' messages
            status, messages = mail.search(None, "ALL")
            if status == "OK" and messages[0]:
                mail_ids = messages[0].split()
                # Get the latest emails first
                for i in reversed(mail_ids[-limit:]):
                    res, data = mail.fetch(i, "(RFC822)")
                    if res == "OK" and data[0]:
                        msg = email.message_from_bytes(data[0][1])
                        
                        subject = msg.get("Subject", "(No Subject)")
                        sender = msg.get("From", "(Unknown)")
                        date_received = msg.get("Date", "")
                        
                        # Extract text or HTML body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain" or content_type == "text/html":
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors='ignore')
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors='ignore')
                        
                        # Clean body preview
                        body_preview = re.sub('<[^<]+?>', '', body)[:150] + "..." if "<" in body else body[:150]
                        
                        received_mails.append({
                            "id": i.decode(),
                            "from": sender,
                            "subject": subject,
                            "date": date_received,
                            "preview": body_preview.strip()
                        })
            mail.close()
            mail.logout()
        except Exception as e:
            # Fallback error response
            received_mails.append({
                "id": "error",
                "from": "System Engine",
                "subject": "Connection Timeout / Setup Incomplete",
                "date": "Now",
                "preview": f"Could not connect to IMAP. Ensure secure credentials and app-password are active. Error: {str(e)}"
            })
        return received_mails

@script38_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME, default_mail=DEFAULT_MAILBOX)

@script38_bp.route('/api/send', methods=['POST'])
def api_send():
    data = request.json or {}
    smtp_host = data.get('smtp_host', 'smtp.gmail.com')
    smtp_port = data.get('smtp_port', 587)
    imap_host = data.get('imap_host', 'imap.gmail.com')
    imap_port = data.get('imap_port', 993)
    user = data.get('email_user')
    password = data.get('email_pass')
    
    to = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    
    if not all([user, password, to, subject, body]):
        return jsonify({"success": False, "message": "Missing credentials or message fields."}), 400
        
    engine = ApexEmailTerminal(smtp_host, smtp_port, imap_host, imap_port, user, password)
    result = engine.send_mail(to, subject, f"<html><body>{body}</body></html>")
    return jsonify(result)

@script38_bp.route('/api/receive', methods=['POST'])
def api_receive():
    data = request.json or {}
    smtp_host = data.get('smtp_host', 'smtp.gmail.com')
    smtp_port = data.get('smtp_port', 587)
    imap_host = data.get('imap_host', 'imap.gmail.com')
    imap_port = data.get('imap_port', 993)
    user = data.get('email_user')
    password = data.get('email_pass')
    
    if not user or not password:
        return jsonify({"success": False, "message": "Credentials needed to poll inbox."}), 400
        
    engine = ApexEmailTerminal(smtp_host, smtp_port, imap_host, imap_port, user, password)
    emails = engine.fetch_inbox()
    return jsonify({"success": True, "emails": emails})

# BLACK-TECH MINIMAL CYBERPUNK EMAIL CLIENT UI
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Mail Terminal</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #060913; 
            color: #f1f5f9;
        }
        .cyber-card {
            background: #0f172a;
            border: 1px solid #1e293b;
        }
    </style>
</head>
<body class="antialiased selection:bg-emerald-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Configurations Sidebar -->
        <aside class="w-full lg:w-80 bg-slate-950 flex flex-col border-b lg:border-r border-slate-900 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-xl shadow-lg">
                    <i class="fa-solid fa-square-envelope text-xl text-slate-950"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">ApexMail</h2>
                    <span class="text-[10px] text-emerald-400 font-mono uppercase tracking-widest mt-1 block">Full-Duplex v38</span>
                </div>
            </div>

            <div class="space-y-4 flex-1">
                <div class="p-4 bg-slate-900/50 border border-slate-800 rounded-xl space-y-3">
                    <span class="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Authentication Setup</span>
                    
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">Custom Email Account</label>
                        <input type="text" id="emailUser" value="{{ default_mail }}" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">Password / App-Pass</label>
                        <input type="password" id="emailPass" placeholder="••••••••" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                    <hr class="border-slate-800">
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">SMTP Server Host</label>
                        <input type="text" id="smtpHost" value="smtp.gmail.com" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">SMTP Server Port</label>
                        <input type="number" id="smtpPort" value="587" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">IMAP Server Host</label>
                        <input type="text" id="imapHost" value="imap.gmail.com" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 font-mono block">IMAP Server Port</label>
                        <input type="number" id="imapPort" value="993" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono focus:outline-none">
                    </div>
                </div>
            </div>
        </aside>

        <!-- Main Area -->
        <main class="flex-1 p-6 lg:p-10 flex flex-col xl:flex-row gap-8">
            <!-- Outbound (Send Mail) -->
            <div class="flex-1 space-y-6">
                <div class="cyber-card p-6 rounded-2xl space-y-4">
                    <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-paper-plane text-emerald-400"></i> Compose Outgoing Signal
                    </h3>
                    
                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Recipient Email (To)</label>
                        <input type="email" id="sendTo" placeholder="target@client.com" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white">
                    </div>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Subject Line</label>
                        <input type="text" id="sendSubject" placeholder="Enterprise Proposition" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white">
                    </div>

                    <div>
                        <label class="text-xs text-slate-400 font-mono mb-1 block">Message Body</label>
                        <textarea id="sendBody" rows="8" placeholder="Type your dynamic payload here..." class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white font-mono"></textarea>
                    </div>

                    <button onclick="dispatchMail()" class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-xl text-xs uppercase tracking-wider transition cursor-pointer">
                        Transmit Mail Signal
                    </button>
                </div>
            </div>

            <!-- Inbound (Receive Mail Inbox) -->
            <div class="flex-1 flex flex-col space-y-6">
                <div class="cyber-card p-6 rounded-2xl flex-1 flex flex-col">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                            <i class="fa-solid fa-inbox text-emerald-400"></i> Signal Receiver Terminal
                        </h3>
                        <button onclick="refreshInbox()" class="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 cursor-pointer">
                            <i class="fa-solid fa-rotate"></i> Poll Inbox
                        </button>
                    </div>

                    <div id="inboxContainer" class="space-y-3 overflow-y-auto flex-1 max-h-[500px] pr-1">
                        <div class="text-slate-500 text-xs text-center py-10 font-mono">
                            Configure Credentials and click "Poll Inbox" to fetch incoming streams.
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function dispatchMail() {
            const payload = {
                smtp_host: document.getElementById('smtpHost').value,
                smtp_port: document.getElementById('smtpPort').value,
                email_user: document.getElementById('emailUser').value.trim(),
                email_pass: document.getElementById('emailPass').value,
                to: document.getElementById('sendTo').value.trim(),
                subject: document.getElementById('sendSubject').value.trim(),
                body: document.getElementById('sendBody').value
            };

            if(!payload.email_user || !payload.email_pass || !payload.to) {
                return alert("Error: Account and Recipient email must be defined!");
            }

            try {
                const res = await fetch('./api/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                alert(data.message);
            } catch {
                alert("Network communication interrupt.");
            }
        }

        async function refreshInbox() {
            const payload = {
                imap_host: document.getElementById('imapHost').value,
                imap_port: document.getElementById('imapPort').value,
                email_user: document.getElementById('emailUser').value.trim(),
                email_pass: document.getElementById('emailPass').value,
            };

            if(!payload.email_user || !payload.email_pass) {
                return alert("Credentials required to poll mailbox!");
            }

            const container = document.getElementById('inboxContainer');
            container.innerHTML = `<div class="text-xs text-center text-emerald-400 py-10 font-mono animate-pulse">Syncing incoming mail streams...</div>`;

            try {
                const res = await fetch('./api/receive', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if(data.success && data.emails.length > 0) {
                    container.innerHTML = '';
                    data.emails.forEach(mail => {
                        container.innerHTML += `
                            <div class="p-3 bg-slate-900/60 border border-slate-800 rounded-lg space-y-1">
                                <div class="flex justify-between text-[11px] text-slate-400">
                                    <span class="font-bold text-emerald-400 truncate w-36">\${escapeHtml(mail.from)}</span>
                                    <span>\${mail.date}</span>
                                </div>
                                <h4 class="text-xs font-bold text-white truncate">\${escapeHtml(mail.subject)}</h4>
                                <p class="text-[11px] text-slate-400 leading-normal line-clamp-2">\${escapeHtml(mail.preview)}</p>
                            </div>
                        `;
                    });
                } else {
                    container.innerHTML = `<div class="text-xs text-center text-slate-500 py-10 font-mono">No new messages found.</div>`;
                }
            } catch {
                container.innerHTML = `<div class="text-xs text-center text-red-400 py-10 font-mono">Connection Refused. Verify IMAP settings.</div>`;
            }
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""

