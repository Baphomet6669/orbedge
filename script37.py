import os
import time
import re
import json
from flask import Blueprint, render_template_string, request, jsonify
import requests

script37_bp = Blueprint('script37', __name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resend Bulk Email Engine - Script37</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #f9fafb; }
        .dashboard-card { background-color: #111827; border: 1px solid #1f2937; }
        .inner-input { background-color: #0b0f19; border: 1px solid #1f2937; color: #f9fafb; }
        .inner-input:focus { border-color: #38bdf8; outline: none; }
    </style>
</head>
<body class="min-h-screen antialiased font-sans">

    <!-- Header UI -->
    <header class="dashboard-card border-b px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4 shadow-2xl">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-sky-600 rounded-xl text-white shadow-lg shadow-sky-600/30">
                <i class="fa-solid fa-paper-plane text-xl"></i>
            </div>
            <div>
                <h1 class="font-extrabold text-sm tracking-widest uppercase">Script37 Engine</h1>
                <span class="text-[9px] block text-sky-400 font-mono font-bold tracking-wider">RESEND BULK EMAIL DISPATCHER</span>
            </div>
        </div>
        <div class="text-xs font-mono text-emerald-400">
            <i class="fa-solid fa-circle-check animate-pulse"></i> RESEND API v1 READY
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        
        <!-- Main Form Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            <!-- Left Panel: Configurations -->
            <div class="lg:col-span-7 space-y-6">
                <div class="dashboard-card p-6 rounded-2xl shadow-xl space-y-4">
                    <h3 class="text-xs font-mono uppercase tracking-wider text-gray-400 font-bold">
                        <i class="fa-solid fa-key text-sky-500 mr-2"></i> API & Sender Settings
                    </h3>
                    
                    <div class="space-y-3 font-mono text-xs">
                        <div>
                            <label class="block text-gray-400 mb-1">Resend API Key</label>
                            <input type="password" id="apiKey" value="re_LxwV9AWo_H4Y6q5pc2E1YMCSygn7xZQSY" 
                                   class="w-full px-4 py-2.5 rounded-xl inner-input font-bold text-sky-400" placeholder="re_...">
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label class="block text-gray-400 mb-1">Sender Email</label>
                                <input type="text" id="fromEmail" placeholder="onboarding@resend.dev" value="onboarding@resend.dev"
                                       class="w-full px-4 py-2.5 rounded-xl inner-input">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">Sender Display Name</label>
                                <input type="text" id="fromName" placeholder="Shivam Singh" value="Shivam Singh"
                                       class="w-full px-4 py-2.5 rounded-xl inner-input">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dashboard-card p-6 rounded-2xl shadow-xl space-y-4">
                    <h3 class="text-xs font-mono uppercase tracking-wider text-gray-400 font-bold">
                        <i class="fa-solid fa-envelope-open-text text-sky-500 mr-2"></i> Message Content
                    </h3>
                    
                    <div class="space-y-3 font-mono text-xs">
                        <div>
                            <label class="block text-gray-400 mb-1">Subject Line</label>
                            <input type="text" id="subject" placeholder="Important Update Regarding Your Account" value="Test Subject from Script37"
                                   class="w-full px-4 py-2.5 rounded-xl inner-input font-bold text-white">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">Email Body (HTML or Plain Text)</label>
                            <textarea id="htmlBody" rows="7" placeholder="<h2>Hello!</h2><p>This is a bulk test email from Script37.</p>"
                                      class="w-full p-4 rounded-xl inner-input text-gray-200 font-sans text-sm"><h2>Hello!</h2><p>This is a bulk test email from Script37 Engine.</p></textarea>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Panel: Recipients & Control -->
            <div class="lg:col-span-5 space-y-6">
                <div class="dashboard-card p-6 rounded-2xl shadow-xl space-y-4">
                    <h3 class="text-xs font-mono uppercase tracking-wider text-gray-400 font-bold">
                        <i class="fa-solid fa-users text-sky-500 mr-2"></i> Recipients List
                    </h3>
                    
                    <div>
                        <textarea id="recipients" rows="8" placeholder="user1@example.com&#10;user2@example.com"
                                  class="w-full p-4 rounded-xl inner-input font-mono text-xs leading-relaxed"></textarea>
                        <span class="text-[10px] text-gray-500 font-mono mt-1 block">Note: onboarding@resend.dev use kar rahe ho toh sirf apne registered email par test bhejo.</span>
                    </div>

                    <button onclick="startBulkDispatch(event)" id="btnDispatch" type="button"
                            class="w-full py-3.5 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-sky-600/20 flex items-center justify-center gap-2 cursor-pointer">
                        <i class="fa-solid fa-paper-plane"></i> START BULK DISPATCH
                    </button>
                </div>

                <!-- Status Console -->
                <div class="dashboard-card p-6 rounded-2xl shadow-xl space-y-3">
                    <div class="flex justify-between items-center border-b border-gray-800 pb-2">
                        <h4 class="text-xs font-mono font-bold text-emerald-400 uppercase"><i class="fa-solid fa-terminal mr-2"></i> Live Console Output</h4>
                        <span id="badgeCount" class="text-[10px] font-mono bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded font-bold">0 SENT</span>
                    </div>
                    <div id="consoleLog" class="h-40 overflow-y-auto bg-black/50 border border-gray-800 rounded-xl p-3 font-mono text-[11px] space-y-1.5 text-gray-400">
                        <div class="text-gray-600 italic">// Console ready. Fill details & click dispatch.</div>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <script>
        async function startBulkDispatch(e) {
            if(e) e.preventDefault();

            const apiKey = document.getElementById('apiKey').value.trim();
            const fromEmail = document.getElementById('fromEmail').value.trim();
            const fromName = document.getElementById('fromName').value.trim();
            const subject = document.getElementById('subject').value.trim();
            const htmlBody = document.getElementById('htmlBody').value.trim();
            const recipientsRaw = document.getElementById('recipients').value.trim();

            if(!apiKey) return alert("Bhai, Resend API key missing hai!");
            if(!fromEmail || !subject || !htmlBody || !recipientsRaw) {
                return alert("Sabhi fields bharo (From Email, Subject, Body, Recipients)!");
            }

            // Extract Emails safely
            const emailsList = recipientsRaw.split(/[\\n,]+/).map(e => e.trim()).filter(e => e.length > 3);
            if(emailsList.length === 0) return alert("Valid email addresses enter karo!");

            const btn = document.getElementById('btnDispatch');
            const logBox = document.getElementById('consoleLog');
            logBox.innerHTML = '';
            
            btn.disabled = true;
            btn.innerText = "DISPATCHING...";
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            
            appendLog(`[INIT] Starting dispatch for ${emailsList.length} address(es)...`, 'sky');

            let successCount = 0;

            // Route relative path handling
            const targetEndpoint = window.location.pathname.replace(/\\/+$/, '') + '/send-single-email';

            for (let i = 0; i < emailsList.length; i++) {
                const targetEmail = emailsList[i];
                appendLog(`[SENDING] (${i+1}/${emailsList.length}) to ${targetEmail}...`, 'gray');

                try {
                    const payload = {
                        api_key: apiKey,
                        from_email: fromEmail,
                        from_name: fromName,
                        to_email: targetEmail,
                        subject: subject,
                        html_body: htmlBody
                    };

                    const response = await fetch(targetEndpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const resData = await response.json();

                    if (response.ok && resData.success) {
                        successCount++;
                        appendLog(`[SUCCESS] Sent to ${targetEmail} | Resend ID: ${resData.id}`, 'emerald');
                    } else {
                        appendLog(`[ERROR] Failed for ${targetEmail}: ${resData.error || 'API Error'}`, 'red');
                    }
                } catch (err) {
                    appendLog(`[FAIL] Network Error for ${targetEmail}: ${err.message}`, 'red');
                }

                document.getElementById('badgeCount').innerText = `${successCount}/${emailsList.length} SENT`;
                
                // Rate limit delay
                await new Promise(r => setTimeout(r, 400));
            }

            appendLog(`[COMPLETE] Bulk campaign process finished.`, 'yellow');
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> START BULK DISPATCH`;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
        }

        function appendLog(msg, color) {
            const logBox = document.getElementById('consoleLog');
            const colorClass = {
                sky: 'text-sky-400',
                emerald: 'text-emerald-400',
                red: 'text-rose-400',
                yellow: 'text-yellow-400',
                gray: 'text-gray-400'
            }[color] || 'text-gray-400';

            const item = document.createElement('div');
            item.className = `${colorClass} font-mono`;
            item.innerText = msg;
            logBox.appendChild(item);
            logBox.scrollTop = logBox.scrollHeight;
        }
    </script>
</body>
</html>
'''

@script37_bp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@script37_bp.route('/send-single-email', methods=['POST'])
def send_single_email():
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key', '').strip()
        from_email = data.get('from_email', '').strip()
        from_name = data.get('from_name', '').strip()
        to_email = data.get('to_email', '').strip()
        subject = data.get('subject', '').strip()
        html_body = data.get('html_body', '').strip()

        if not api_key or not to_email:
            return jsonify({"success": False, "error": "Missing API Key or Destination Email"}), 400

        formatted_from = f"{from_name} <{from_email}>" if from_name else from_email

        resend_url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": formatted_from,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }

        res = requests.post(resend_url, headers=headers, json=payload, timeout=12)
        res_json = res.json()

        if res.status_code in [200, 201]:
            return jsonify({"success": True, "id": res_json.get("id", "N/A")})
        else:
            error_msg = res_json.get("message") or res_json.get("name") or "Resend API Error"
            return jsonify({"success": False, "error": error_msg}), res.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
