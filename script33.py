from flask import Blueprint, render_template_string, request, jsonify
import urllib.request
import urllib.parse
import json
import socket
import time
import ssl
import re

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
    .matrix-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.03); word-break: break-all; }

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
            <input type="text" id="target_url" class="url-input" placeholder="Enter Domain or IP (e.g. google.com, shikhotech.com or 8.8.8.8)...">
            <button class="btn-audit" onclick="triggerWhoisAudit()">Lookup WHOIS Data</button>
            <button class="btn-pdf" id="pdf_btn" onclick="exportReportToPDF()">📄 Export PDF Report</button>
        </div>
    </div>

    <!-- Container for Export -->
    <div id="pdf_report_content">
        <div class="studio-layout">
            
            <!-- Left: Matrix -->
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

            <!-- Right: Raw Log Terminal -->
            <div class="panel">
                <div class="panel-header">📝 Full Raw WHOIS Record Data</div>
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
            
            footer.innerText = `📡 Querying WHOIS networks and resolving geolocation for ${target}...`;
            terminal.innerText = `[CONNECTING] Traversing authoritative WHOIS/RDAP endpoints...`;
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

                // Render Summary Table
                const tableBody = document.getElementById('matrix_rows');
                tableBody.innerHTML = `
                    <tr><td style="color:var(--text-gray);">Target Domain</td><td style="font-weight:bold; color:#fff;">${data.domain}</td></tr>
                    <tr><td style="color:var(--text-gray);">Resolved IP</td><td style="color:var(--neon-cyan); font-weight:bold;">${data.ip}</td></tr>
                    <tr><td style="color:var(--text-gray);">Country / Code</td><td>${data.country} (${data.country_code})</td></tr>
                    <tr><td style="color:var(--text-gray);">State / Region</td><td style="color:var(--neon-green); font-weight:bold;">${data.state}</td></tr>
                    <tr><td style="color:var(--text-gray);">City</td><td>${data.city} (PIN/ZIP: ${data.zip})</td></tr>
                    <tr><td style="color:var(--text-gray);">Latitude / Longitude</td><td>${data.lat} , ${data.lon}</td></tr>
                    <tr><td style="color:var(--text-gray);">ISP / Network Host</td><td>${data.isp}</td></tr>
                    <tr><td style="color:var(--text-gray);">Organization Owner</td><td>${data.org}</td></tr>
                    <tr><td style="color:var(--text-gray);">Registrar Name</td><td>${data.registrar}</td></tr>
                    <tr><td style="color:var(--text-gray);">Creation Date</td><td>${data.creation_date}</td></tr>
                    <tr><td style="color:var(--text-gray);">Expiration Date</td><td style="color:var(--neon-red);">${data.expiration_date}</td></tr>
                    <tr><td style="color:var(--text-gray);">Name Servers</td><td>${data.nameservers}</td></tr>
                    <tr><td style="color:var(--text-gray);">Server Latency</td><td>${data.latency}</td></tr>
                `;

                terminal.innerText = data.raw_whois;
                footer.innerText = `✅ WHOIS & Geolocation lookup successfully completed for ${data.domain}`;
                pdfBtn.style.display = "inline-block";

            } catch(err) {
                terminal.innerText = `[CRITICAL ERROR] Execution pipeline timed out or failed.`;
                footer.innerText = `❌ Execution Fault.`;
            }
        }

        function exportReportToPDF() {
            const element = document.getElementById('pdf_report_content');
            const opt = {
                margin:       [0.3, 0.3, 0.3, 0.3],
                filename:     `WHOIS_Audit_Report_${currentDomain || 'Target'}.pdf`,
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
        return jsonify({"status": "error", "message": "No target provided."})

    # Clean domain string
    raw_target = re.sub(r'^https?://', '', raw_target)
    target_domain = raw_target.split('/')[0].split(':')[0]

    # SSL Bypass context for network calls
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        # 1. IP Resolution and Ping Latency
        start_time = time.time()
        try:
            resolved_ip = socket.gethostbyname(target_domain)
            latency = f"{round((time.time() - start_time) * 1000, 2)} ms"
        except Exception:
            resolved_ip = "Unable to Resolve IP"
            latency = "N/A"

        # 2. IP Geolocation Query (City, State, Country, Lat, Lon, ISP)
        ip_info = {}
        if resolved_ip != "Unable to Resolve IP":
            try:
                geo_url = f"http://ip-api.com/json/{resolved_ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
                req_geo = urllib.request.Request(geo_url, headers=headers)
                with urllib.request.urlopen(req_geo, timeout=5) as resp:
                    ip_info = json.loads(resp.read().decode('utf-8'))
            except Exception:
                pass

        # 3. Robust Multi-Method WHOIS Retrieval
        registrar = "N/A"
        creation_date = "N/A"
        expiration_date = "N/A"
        nameservers = []
        raw_whois_text = ""

        # Primary Lookup Endpoint (Reliable WHOIS API fallback)
        try:
            api_url = f"https://api.ip2whois.com/v1?key=free&domain={target_domain}"
            req_api = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req_api, context=ctx, timeout=6) as resp_api:
                data_api = json.loads(resp_api.read().decode('utf-8'))
                if "registrar" in data_api:
                    registrar = data_api.get("registrar", {}).get("name", "N/A")
                    creation_date = data_api.get("create_date", "N/A")
                    expiration_date = data_api.get("expire_date", "N/A")
                    nameservers = data_api.get("nameservers", [])
                    raw_whois_text = json.dumps(data_api, indent=2)
        except Exception:
            pass

        # Secondary Fallback: RDAP Protocol Routing
        if registrar == "N/A" or not raw_whois_text:
            try:
                rdap_url = f"https://rdap.org/domain/{target_domain}"
                req_rdap = urllib.request.Request(rdap_url, headers=headers)
                with urllib.request.urlopen(req_rdap, context=ctx, timeout=6) as resp_rdap:
                    rdap_data = json.loads(resp_rdap.read().decode('utf-8'))
                    raw_whois_text = json.dumps(rdap_data, indent=2)

                    # Extract events
                    for ev in rdap_data.get('events', []):
                        action = ev.get('eventAction')
                        date_val = ev.get('eventDate', '').split('T')[0]
                        if action == 'registration': creation_date = date_val
                        elif action == 'expiration': expiration_date = date_val

                    # Extract registrar
                    for ent in rdap_data.get('entities', []):
                        if 'registrar' in ent.get('roles', []):
                            for item in ent.get('vcardArray', [[], []])[1]:
                                if item[0] == 'fn': registrar = item[3]

                    # Extract Nameservers
                    for ns in rdap_data.get('nameservers', []):
                        if ns.get('ldhName'): nameservers.append(ns.get('ldhName'))
            except Exception as e:
                raw_whois_text = f"WHOIS / RDAP Query Log:\n----------------------------------------\n"
                raw_whois_text += f"Target Domain: {target_domain}\nResolved IP: {resolved_ip}\n"
                raw_whois_text += f"Location: {ip_info.get('city', 'N/A')}, {ip_info.get('regionName', 'N/A')}, {ip_info.get('country', 'N/A')}\n"
                raw_whois_text += f"ISP Network: {ip_info.get('isp', 'N/A')}\n"
                raw_whois_text += f"\nNote: Detailed registrar records for TLD '{target_domain.split('.')[-1]}' are privacy-protected or restricted on public RDAP gateways."

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
            "lat": ip_info.get("lat", "N/A"),
            "lon": ip_info.get("lon", "N/A"),
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
            "message": f"WHOIS process error: {str(e)}"
        })
