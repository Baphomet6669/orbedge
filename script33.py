from flask import Blueprint, render_template_string, request, jsonify
import urllib.request
import urllib.parse
import json
import socket
import time

script33_bp = Blueprint('script33', __name__)

ULTIMATE_WHOIS_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADVANCED WHOIS & IP AUDIT ENGINE</title>
  <!-- html2pdf Library for PDF Export -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    :root {
        --bg-deep: #030712;
        --panel-bg: #0b1329;
        --neon-cyan: #06b6d4;
        --neon-green: #10b981;
        --neon-red: #ef4444;
        --border-color: rgba(6, 182, 212, 0.2);
        --text-bright: #f3f4f6;
        --text-gray: #9ca3af;
        --terminal-bg: #020617;
    }

    body { 
        background: var(--bg-deep); 
        color: var(--text-bright); 
        font-family: 'Consolas', 'Courier New', monospace; 
        min-height: 100vh;
        padding: 20px;
    }

    .header-panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .brand-title { font-size: 22px; font-weight: bold; letter-spacing: 2px; margin-bottom: 5px; }
    .brand-title span { color: var(--neon-cyan); }
    .brand-sub { font-size: 12px; color: var(--text-gray); margin-bottom: 20px; }

    .input-row { display: flex; gap: 15px; flex-wrap: wrap; }

    .url-input {
        flex: 1;
        min-width: 280px;
        background: #02040a;
        border: 1px solid var(--border-color);
        padding: 12px 15px;
        color: #fff;
        font-family: inherit;
        font-size: 14px;
        border-radius: 6px;
        outline: none;
    }
    .url-input:focus { border-color: var(--neon-cyan); box-shadow: 0 0 10px rgba(6, 182, 212, 0.2); }

    .btn-audit {
        background: #2563eb;
        color: white;
        border: none;
        padding: 12px 25px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 13px;
        letter-spacing: 1px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-audit:hover { background: #1d4ed8; box-shadow: 0 0 15px rgba(37, 99, 235, 0.4); }

    .btn-pdf {
        background: var(--neon-green);
        color: #000;
        border: none;
        padding: 12px 20px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 13px;
        letter-spacing: 1px;
        border-radius: 6px;
        cursor: pointer;
        display: none;
    }
    .btn-pdf:hover { background: #059669; color: #fff; }

    .studio-layout {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    @media (max-width: 1024px) { .studio-layout { grid-template-columns: 1fr; } }

    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        display: flex;
        flex-direction: column;
    }

    .panel-header {
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--neon-cyan);
        margin-bottom: 15px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 8px;
    }

    .table-container { overflow-x: auto; }
    
    .matrix-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .matrix-table th { color: var(--text-gray); padding: 10px; border-bottom: 1px solid var(--border-color); text-align: left; }
    .matrix-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.03); }

    .terminal-screen {
        background: var(--terminal-bg);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 6px;
        padding: 15px;
        flex: 1;
        min-height: 480px;
        max-height: 700px;
        overflow-y: auto;
        font-size: 11px;
        line-height: 1.5;
        color: #34d399;
        white-space: pre-wrap;
    }

    .status-footer {
        margin-top: 20px;
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 11px;
        color: var(--text-gray);
    }
  </style>
</head>
<body>

    <div class="header-panel">
        <div class="brand-title">A-Z WHOIS <span>& NETWORK GEOLOCATION AUDITOR</span></div>
        <div class="brand-sub">Domain Ownership, Server IP, State/City Geolocation, Registrar Logs & PDF Export</div>
        
        <div class="input-row">
            <input type="text" id="target_url" class="url-input" placeholder="Enter Domain or IP (e.g. example.com or 8.8.8.8)...">
            <button class="btn-audit" onclick="triggerWhoisAudit()">Lookup WHOIS Data</button>
            <button class="btn-pdf" id="pdf_btn" onclick="exportReportToPDF()">📄 Export PDF Report</button>
        </div>
    </div>

    <!-- Wrap Content for PDF Exporting -->
    <div id="pdf_report_content">
        <div class="studio-layout">
            
            <!-- Left: Quick Summary Matrix -->
            <div class="panel">
                <div class="panel-header">🌐 IP & Domain Network Profile</div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Resolved Value</th>
                            </tr>
                        </thead>
                        <tbody id="matrix_rows">
                            <tr><td colspan="2" style="color: var(--text-gray); text-align: center; padding: 30px;">[Idle] Enter a domain to start lookup...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Right: Detailed WHOIS Raw Terminal -->
            <div class="panel">
                <div class="panel-header">📝 Full Raw WHOIS Record & Server Headers</div>
                <div class="terminal-screen" id="whois_raw_terminal">[AWAITING TARGET PAYLOAD]</div>
            </div>

        </div>
    </div>

    <div class="status-footer" id="footer_log">Engine Ready.</div>

    <script>
        let currentDomain = "";

        async function triggerWhoisAudit() {
            const inputField = document.getElementById('target_url');
            let target = inputField.value.trim();
            if(!target) { alert("Bhai, valid website URL ya Domain name dalo!"); return; }

            const footer = document.getElementById('footer_log');
            const terminal = document.getElementById('whois_raw_terminal');
            const pdfBtn = document.getElementById('pdf_btn');
            
            footer.innerText = `📡 Fetching WHOIS data & Geolocation for ${target}...`;
            terminal.innerText = `[CONNECTING] Querying RDAP and WHOIS registries...`;
            pdfBtn.style.display = "none";

            try {
                const response = await fetch(`${window.location.pathname.replace(/\/$/, "")}/run_whois_lookup?target=${encodeURIComponent(target)}`);
                const data = await response.json();

                if (data.status === "error") {
                    terminal.innerText = `[ERROR] ${data.message}`;
                    footer.innerText = `❌ Lookup Failed.`;
                    return;
                }

                currentDomain = data.domain;

                // Render Table Matrix
                const tableBody = document.getElementById('matrix_rows');
                tableBody.innerHTML = `
                    <tr><td style="color:var(--text-gray);">Target Domain</td><td style="font-weight:bold; color:#fff;">${data.domain}</td></tr>
                    <tr><td style="color:var(--text-gray);">Resolved IP</td><td style="color:var(--neon-cyan); font-weight:bold;">${data.ip}</td></tr>
                    <tr><td style="color:var(--text-gray);">Country / Flag</td><td>${data.country} (${data.country_code})</td></tr>
                    <tr><td style="color:var(--text-gray);">State / Region</td><td style="color:var(--neon-green); font-weight:bold;">${data.state}</td></tr>
                    <tr><td style="color:var(--text-gray);">City</td><td>${data.city} (Postal: ${data.zip})</td></tr>
                    <tr><td style="color:var(--text-gray);">ISP / Host</td><td>${data.isp}</td></tr>
                    <tr><td style="color:var(--text-gray);">Organization</td><td>${data.org}</td></tr>
                    <tr><td style="color:var(--text-gray);">Registrar Name</td><td>${data.registrar}</td></tr>
                    <tr><td style="color:var(--text-gray);">Creation Date</td><td>${data.creation_date}</td></tr>
                    <tr><td style="color:var(--text-gray);">Expiration Date</td><td style="color:var(--neon-red);">${data.expiration_date}</td></tr>
                    <tr><td style="color:var(--text-gray);">Name Servers</td><td>${data.nameservers}</td></tr>
                    <tr><td style="color:var(--text-gray);">Server Response Latency</td><td>${data.latency}</td></tr>
                `;

                terminal.innerText = data.raw_whois;
                footer.innerText = `✅ WHOIS & Geolocation lookup successfully completed for ${data.domain}`;
                pdfBtn.style.display = "inline-block";

            } catch(err) {
                terminal.innerText = `[CRITICAL ERROR] Failed to perform WHOIS lookup.`;
                footer.innerText = `❌ Execution Fault.`;
            }
        }

        function exportReportToPDF() {
            const element = document.getElementById('pdf_report_content');
            const opt = {
                margin:       [0.3, 0.3, 0.3, 0.3],
                filename:     `WHOIS_Report_${currentDomain || 'Audit'}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, backgroundColor: '#030712' },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'landscape' }
            };
            html2pdf().set(opt).from(element).save();
        }
    </script>
</body>
</html>
"""

@script33_bp.route('/')
def index():
    return render_template_string(ULTIMATE_WHOIS_UI)

@script33_bp.route('/run_whois_lookup')
def run_whois_lookup():
    raw_target = request.args.get('target', '').strip()
    if not raw_target:
        return jsonify({"status": "error", "message": "No target specified."})

    # Cleaning target domain/URL
    raw_target = re.sub(r'^https?://', '', raw_target)
    target_domain = raw_target.split('/')[0].split(':')[0]

    try:
        # 1. Resolve IP Address & Measure Ping/Latency
        start_time = time.time()
        try:
            resolved_ip = socket.gethostbyname(target_domain)
            latency = f"{round((time.time() - start_time) * 1000, 2)} ms"
        except Exception:
            resolved_ip = "Unable to Resolve IP"
            latency = "N/A"

        # 2. Fetch Detailed IP & Location Data (City, State, Country, ISP)
        ip_info = {}
        if resolved_ip != "Unable to Resolve IP":
            try:
                geo_req = urllib.request.Request(f"http://ip-api.com/json/{resolved_ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query")
                with urllib.request.urlopen(geo_req, timeout=5) as resp:
                    ip_info = json.loads(resp.read().decode('utf-8'))
            except Exception:
                pass

        # 3. Query RDAP / WHOIS Data from Global Registry
        rdap_data = {}
        raw_whois_text = "WHOIS Record Log:\n----------------------------------------\n"
        try:
            rdap_req = urllib.request.Request(f"https://rdap.org/domain/{target_domain}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(rdap_req, timeout=6) as rdap_resp:
                rdap_data = json.loads(rdap_resp.read().decode('utf-8'))
                raw_whois_text += json.dumps(rdap_data, indent=2)
        except Exception as e:
            raw_whois_text += f"\n[RDAP Fetch Fallback Note]: {str(e)}\n"
            raw_whois_text += f"\nDomain: {target_domain}\nResolved IP: {resolved_ip}\n"
            raw_whois_text += f"Geolocation: {ip_info.get('city', 'N/A')}, {ip_info.get('regionName', 'N/A')}, {ip_info.get('country', 'N/A')}\n"

        # Parsing RDAP WHOIS attributes
        registrar = "N/A"
        creation_date = "N/A"
        expiration_date = "N/A"
        nameservers = []

        if rdap_data:
            # Events parsing (Registration/Expiration)
            events = rdap_data.get('events', [])
            for ev in events:
                action = ev.get('eventAction')
                date_str = ev.get('eventDate', '').split('T')[0]
                if action == 'registration':
                    creation_date = date_str
                elif action == 'expiration':
                    expiration_date = date_str

            # Entities (Registrar)
            entities = rdap_data.get('entities', [])
            for ent in entities:
                roles = ent.get('roles', [])
                if 'registrar' in roles:
                    vcard = ent.get('vcardArray', [])
                    if len(vcard) > 1:
                        for item in vcard[1]:
                            if item[0] == 'fn':
                                registrar = item[3]

            # Nameservers
            ns_list = rdap_data.get('nameservers', [])
            for ns in ns_list:
                ns_name = ns.get('ldhName')
                if ns_name:
                    nameservers.append(ns_name)

        ns_display = ", ".join(nameservers) if nameservers else "N/A"

        return jsonify({
            "status": "success",
            "domain": target_domain,
            "ip": resolved_ip,
            "country": ip_info.get("country", "N/A"),
            "country_code": ip_info.get("countryCode", "N/A"),
            "state": ip_info.get("regionName", "N/A"),
            "city": ip_info.get("city", "N/A"),
            "zip": ip_info.get("zip", "N/A"),
            "isp": ip_info.get("isp", "N/A"),
            "org": ip_info.get("org", "N/A"),
            "registrar": registrar,
            "creation_date": creation_date,
            "expiration_date": expiration_date,
            "nameservers": ns_display,
            "latency": latency,
            "raw_whois": raw_whois_text
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"WHOIS lookup failed. Details: {str(e)}"
        })

