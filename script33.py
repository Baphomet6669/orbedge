from flask import Blueprint, render_template_string, request, jsonify
import urllib.request
import urllib.parse
import json
import socket
import time
import ssl
import re
from datetime import datetime

script33_bp = Blueprint('script33', __name__)

ULTIMATE_WHOIS_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADVANCED OMNI DOMAIN & ASSET AUDITOR</title>
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
        --neon-amber: #f59e0b;
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
    .matrix-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.03); word-break: break-all; vertical-align: middle; }

    .terminal-screen {
        background: var(--terminal-bg);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 6px;
        padding: 15px;
        flex: 1;
        min-height: 480px;
        max-height: 750px;
        overflow-y: auto;
        font-size: 11px;
        line-height: 1.5;
        color: #34d399;
        white-space: pre-wrap;
    }

    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        display: inline-block;
        text-transform: uppercase;
    }
    .badge-interactive {
        cursor: pointer;
        transition: transform 0.1s, filter 0.2s;
    }
    .badge-interactive:hover {
        filter: brightness(1.3);
        transform: scale(1.03);
    }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
    .badge-danger { background: rgba(239, 68, 68, 0.2); color: var(--neon-red); border: 1px solid var(--neon-red); }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: var(--neon-amber); border: 1px solid var(--neon-amber); }
    .badge-info { background: rgba(6, 182, 212, 0.2); color: var(--neon-cyan); border: 1px solid var(--neon-cyan); }

    .favicon-img {
        width: 24px;
        height: 24px;
        vertical-align: middle;
        margin-right: 8px;
        border-radius: 4px;
        background: #fff;
        padding: 2px;
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

    /* Modal Styling */
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85);
        z-index: 9999;
        justify-content: center;
        align-items: center;
    }
    .modal-box {
        background: var(--panel-bg);
        border: 1px solid var(--neon-cyan);
        width: 85%;
        max-width: 850px;
        max-height: 85vh;
        border-radius: 8px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
    }
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
    }
    .modal-title { font-size: 14px; font-weight: bold; color: var(--neon-cyan); }
    .modal-close {
        background: var(--neon-red);
        color: #fff;
        border: none;
        padding: 4px 10px;
        font-weight: bold;
        border-radius: 4px;
        cursor: pointer;
    }
    .modal-body {
        overflow-y: auto;
        flex: 1;
        font-size: 11px;
        background: var(--terminal-bg);
        padding: 12px;
        border-radius: 4px;
        line-height: 1.6;
    }
    .modal-body a { color: var(--neon-green); word-break: break-all; display: block; margin-bottom: 6px; text-decoration: none; }
    .modal-body a:hover { text-decoration: underline; color: var(--neon-cyan); }
    
    .explanation-box {
        background: rgba(6, 182, 212, 0.08);
        border-left: 3px solid var(--neon-cyan);
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 4px;
        color: var(--text-bright);
    }
  </style>
</head>
<body>

    <div class="header-panel">
        <div class="brand-title">A-Z OMNI <span>DOMAIN, SECURITY & PERFORMANCE AUDITOR</span></div>
        <div class="brand-sub">SSL Audit, Broken Links, Manifest Inspector, Page Speed, WHOIS, Contacts & PDF Export</div>
        
        <div class="input-row">
            <input type="text" id="target_url" class="url-input" placeholder="Enter Domain or IP (e.g. google.com, shikhotech.com or 8.8.8.8)...">
            <button class="btn-audit" onclick="triggerWhoisAudit()">Run 360° Deep Recon</button>
            <button class="btn-pdf" id="pdf_btn" onclick="exportReportToPDF()">📄 Export PDF Report</button>
        </div>
    </div>

    <!-- Container for PDF Export -->
    <div id="pdf_report_content">
        <div class="studio-layout">
            
            <!-- Left: Matrix -->
            <div class="panel">
                <div class="panel-header">🌐 Network, Security, Performance & Asset Matrix</div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>Parameter / Category</th>
                                <th>Resolved Status / Details</th>
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
                <div class="panel-header">📝 Detailed Multi-Vector Audit Logs</div>
                <div class="terminal-screen" id="whois_raw_terminal">[AWAITING TARGET PAYLOAD]</div>
            </div>

        </div>
    </div>

    <!-- Modal Window -->
    <div class="modal-overlay" id="assetModal">
        <div class="modal-box">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">Extracted Payload Inspector</div>
                <button class="modal-close" onclick="closeModal()">X</button>
            </div>
            <div class="modal-body" id="modalBody">
                <!-- Dynamic Content Rendered Here -->
            </div>
        </div>
    </div>

    <div class="status-footer" id="footer_log">Engine Ready.</div>

    <script>
        let currentDomain = "";
        let extractedAssetStore = {};
        let manifestData = {};

        async function triggerWhoisAudit() {
            const inputField = document.getElementById('target_url');
            let target = inputField.value.trim();
            if(!target) { alert("Bhai, valid website URL ya Domain name dalo!"); return; }

            const footer = document.getElementById('footer_log');
            const terminal = document.getElementById('whois_raw_terminal');
            const pdfBtn = document.getElementById('pdf_btn');
            
            footer.innerText = `📡 Performing SSL, Speed, Broken Links, Manifest & WHOIS Audit for ${target}...`;
            terminal.innerText = `[INITIALIZING] Running active TLS handshake, checking broken links, timing latency, and scraping manifest.json...`;
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
                extractedAssetStore = data.assets;
                manifestData = data.manifest;

                // Responsive Badge
                let respBadge = data.is_responsive 
                    ? `<span class="badge badge-success">YES (MOBILE-FRIENDLY)</span>` 
                    : `<span class="badge badge-danger">NO (NOT RESPONSIVE)</span>`;

                // Favicon Display
                let faviconHTML = data.favicon_found 
                    ? `<img src="${data.favicon_url}" class="favicon-img" onerror="this.style.display='none'"> <a href="${data.favicon_url}" target="_blank" style="color:var(--neon-cyan);">${data.favicon_url}</a>`
                    : `<span class="badge badge-warning">FAVICON NOT DETECTED</span>`;

                // SSL Status Badge
                let sslBadge = data.ssl_info.valid 
                    ? `<span class="badge badge-success">VALID SSL (${data.ssl_info.days_left} Days Left)</span>`
                    : `<span class="badge badge-danger">INVALID / NO SSL (${data.ssl_info.error || 'N/A'})</span>`;

                // Broken Links Badge
                let brokenLinksHTML = data.broken_links.count > 0 
                    ? `<span class="badge badge-danger badge-interactive" onclick="viewCategoryLinks('broken')">⚠️ ${data.broken_links.count} Broken Links Detected (Click to View)</span>`
                    : `<span class="badge badge-success">0 Broken Links Detected (All Clean)</span>`;

                // Manifest Badge
                let manifestHTML = data.manifest.found 
                    ? `<span class="badge badge-info badge-interactive" onclick="inspectManifest()">📄 Manifest.json Found (Click to Inspect & Explain)</span>`
                    : `<span class="badge badge-warning">manifest.json Not Detected</span>`;

                // Page Speed Badge
                let speedColor = data.load_speed_ms < 500 ? 'badge-success' : (data.load_speed_ms < 1500 ? 'badge-warning' : 'badge-danger');
                let speedHTML = `<span class="badge ${speedColor}">${data.load_speed_ms} ms (${data.load_speed_sec} sec)</span>`;

                // Contacts Formatting
                let emailsFormatted = data.contacts.emails.length > 0 ? data.contacts.emails.join(", ") : "None Detected";
                let phonesFormatted = data.contacts.phones.length > 0 ? data.contacts.phones.join(", ") : "None Detected";
                let socialsFormatted = data.contacts.socials.length > 0 ? data.contacts.socials.map(s => `<a href="${s}" target="_blank" style="color:var(--neon-cyan); margin-right:5px;">${new URL(s).hostname}</a>`).join(" | ") : "None Detected";

                // Render Summary Table
                const tableBody = document.getElementById('matrix_rows');
                tableBody.innerHTML = `
                    <tr><td style="color:var(--text-gray);">Target Domain</td><td style="font-weight:bold; color:#fff;">${data.domain}</td></tr>
                    <tr style="background: rgba(16, 185, 129, 0.05);"><td style="color:var(--neon-green); font-weight:bold;">Website Load Speed</td><td>${speedHTML}</td></tr>
                    <tr style="background: rgba(6, 182, 212, 0.05);"><td style="color:var(--neon-cyan); font-weight:bold;">SSL Certificate Status</td><td>${sslBadge}</td></tr>
                    <tr><td style="color:var(--text-gray);">SSL Issuer / Expiry</td><td>${data.ssl_info.issuer || 'N/A'} (Expires: ${data.ssl_info.expire_date || 'N/A'})</td></tr>
                    <tr><td style="color:var(--text-gray);">Broken Links Scan</td><td>${brokenLinksHTML}</td></tr>
                    <tr><td style="color:var(--text-gray);">manifest.json Status</td><td>${manifestHTML}</td></tr>
                    <tr><td style="color:var(--text-gray);">Mobile Responsive Status</td><td>${respBadge}</td></tr>
                    <tr><td style="color:var(--text-gray);">Favicon Icon</td><td>${faviconHTML}</td></tr>
                    
                    <!-- Extracted Contacts -->
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Extracted Emails</td><td style="color:var(--neon-green); font-weight:bold;">${emailsFormatted}</td></tr>
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Extracted Phones</td><td>${phonesFormatted}</td></tr>
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Social Profiles</td><td>${socialsFormatted}</td></tr>

                    <!-- Categorized Assets -->
                    <tr><td style="color:var(--text-gray);">Internal Domain Links</td><td><span class="badge badge-info badge-interactive" onclick="viewCategoryLinks('internal')">🔗 ${data.asset_counts.internal} Internal Links</span></td></tr>
                    <tr><td style="color:var(--text-gray);">External Domain Links</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('external')">🌐 ${data.asset_counts.external} External Links</span></td></tr>
                    <tr><td style="color:var(--text-gray);">CSS Stylesheets</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('css')">🎨 ${data.asset_counts.css} CSS Files</span></td></tr>
                    <tr><td style="color:var(--text-gray);">JavaScript Files</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('js')">📜 ${data.asset_counts.js} JS Scripts</span></td></tr>
                    <tr><td style="color:var(--text-gray);">Images Asset Links</td><td><span class="badge badge-success badge-interactive" onclick="viewCategoryLinks('images')">🖼️ ${data.asset_counts.images} Images</span></td></tr>
                    <tr><td style="color:var(--text-gray);">WOFF / Font Assets</td><td><span class="badge badge-info badge-interactive" onclick="viewCategoryLinks('fonts')">🔤 ${data.asset_counts.fonts} Fonts</span></td></tr>

                    <!-- Geolocation & WHOIS -->
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
                `;

                terminal.innerText = data.full_detailed_log;
                footer.innerText = `✅ SSL, Speed (${data.load_speed_ms}ms), Broken Links & WHOIS Audit completed for ${data.domain}`;
                pdfBtn.style.display = "inline-block";

            } catch(err) {
                terminal.innerText = `[CRITICAL ERROR] Execution pipeline timed out or failed.`;
                footer.innerText = `❌ Execution Fault.`;
            }
        }

        function viewCategoryLinks(categoryKey) {
            const modal = document.getElementById('assetModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            const links = extractedAssetStore[categoryKey] || [];
            title.innerText = `Extracted ${categoryKey.toUpperCase()} Links (${links.length} Found)`;

            if (links.length === 0) {
                body.innerHTML = `<div style="color: var(--text-gray); text-align: center; padding: 20px;">No links found in this category.</div>`;
            } else {
                body.innerHTML = links.map((link, idx) => `<a href="${link}" target="_blank" rel="noopener noreferrer">${idx + 1}. ${link}</a>`).join('');
            }

            modal.style.display = 'flex';
        }

        function inspectManifest() {
            const modal = document.getElementById('assetModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            title.innerText = `Manifest.json File Inspection & Technical Breakdown`;

            if (!manifestData.found) {
                body.innerHTML = `<div style="color: var(--neon-red);">manifest.json file was not found on this website.</div>`;
            } else {
                body.innerHTML = `
                    <div class="explanation-box">
                        <strong>📌 What is a manifest.json file & What does it do?</strong><br>
                        A <code>manifest.json</code> file is a JSON configuration file required for Progressive Web Apps (PWA). It tells the browser how your web application should behave when installed on a desktop or mobile device. It defines the app name, start URL, theme colors, icons, background color, and display mode (e.g. standalone/fullscreen without browser address bars).
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Direct File URL:</strong> <a href="${manifestData.url}" target="_blank" style="color:var(--neon-cyan); inline-block;">${manifestData.url}</a>
                    </div>
                    <div style="margin-bottom: 5px; font-weight: bold; color: var(--neon-green);">📄 Raw Code Content inside manifest.json:</div>
                    <pre style="background: #02040a; border: 1px solid var(--border-color); padding: 10px; border-radius: 4px; color: #34d399; overflow-x: auto;">${manifestData.raw_code}</pre>
                `;
            }

            modal.style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('assetModal').style.display = 'none';
        }

        function exportReportToPDF() {
            const element = document.getElementById('pdf_report_content');
            const opt = {
                margin:       [0.3, 0.3, 0.3, 0.3],
                filename:     `Full_Domain_Audit_${currentDomain || 'Target'}.pdf`,
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

    # SSL context bypass for bad/expired cert site scraping
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Advanced Browser User-Agent to bypass Cloudflare / Bot blocks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    }

    # Helper function to fetch URL with fallback
    def fetch_url_data(url, timeout=8):
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req, context=ctx, timeout=timeout)

    try:
        # 1. Measure Website Load Speed & IP Resolution
        start_speed_time = time.time()
        try:
            resolved_ip = socket.gethostbyname(target_domain)
        except Exception:
            resolved_ip = "Unable to Resolve IP"

        # 2. SSL Certificate Checker
        ssl_info = {"valid": False, "issuer": "N/A", "expire_date": "N/A", "days_left": "N/A", "error": ""}
        try:
            ssl_ctx = ssl.create_default_context()
            with socket.create_connection((target_domain, 443), timeout=5) as sock:
                with ssl_ctx.wrap_socket(sock, server_hostname=target_domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Extract Issuer
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    issuer_name = issuer.get('organizationName') or issuer.get('commonName') or "Unknown Issuer"
                    
                    # Expiry Math
                    not_after_str = cert.get('notAfter')
                    expire_dt = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                    days_left = (expire_dt - datetime.utcnow()).days

                    ssl_info = {
                        "valid": True,
                        "issuer": issuer_name,
                        "expire_date": expire_dt.strftime('%Y-%m-%d'),
                        "days_left": days_left,
                        "error": ""
                    }
        except Exception as ssl_err:
            ssl_info["error"] = str(ssl_err)

        # 3. IP Geolocation (State, City, Country, Lat, Lon, ISP)
        ip_info = {}
        if resolved_ip != "Unable to Resolve IP":
            try:
                geo_url = f"http://ip-api.com/json/{resolved_ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
                req_geo = urllib.request.Request(geo_url, headers=headers)
                with urllib.request.urlopen(req_geo, timeout=5) as resp:
                    ip_info = json.loads(resp.read().decode('utf-8', errors='ignore'))
            except Exception:
                pass

        # 4. HTML Scraping, Load Speed Measure & Asset Parsing
        is_responsive = False
        favicon_found = False
        favicon_url = ""

        emails = set()
        phones = set()
        socials = set()

        internal_links = set()
        external_links = set()
        css_links = set()
        js_links = set()
        img_links = set()
        font_links = set()

        manifest_info = {"found": False, "url": "", "raw_code": ""}

        load_speed_ms = 0
        load_speed_sec = 0

        # Attempt HTTPS first, fallback to HTTP if site rejects HTTPS
        target_schemes = [f"https://{target_domain}", f"http://{target_domain}"]
        html_code = ""
        base_url = f"https://{target_domain}"

        for try_url in target_schemes:
            try:
                with fetch_url_data(try_url, timeout=10) as html_resp:
                    load_speed_ms = round((time.time() - start_speed_time) * 1000, 2)
                    load_speed_sec = round(load_speed_ms / 1000, 2)
                    base_url = html_resp.geturl() # Get final URL after redirects
                    html_code = html_resp.read().decode('utf-8', errors='ignore')
                    if html_code:
                        break
            except Exception:
                continue

        if html_code:
            # Responsive check
            if re.search(r'<meta\s+[^>]*name=["\']viewport["\']', html_code, re.IGNORECASE) or "@media" in html_code:
                is_responsive = True

            # Favicon Extraction
            fav_match = re.search(r'<link\s+[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
            if not fav_match:
                fav_match = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut )?icon["\']', html_code, re.IGNORECASE)

            if fav_match:
                favicon_url = urllib.parse.urljoin(base_url, fav_match.group(1).strip())
                favicon_found = True

            # Manifest File Check
            manifest_match = re.search(r'<link\s+[^>]*rel=["\']manifest["\'][^>]*href=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
            if manifest_match:
                manifest_url = urllib.parse.urljoin(base_url, manifest_match.group(1).strip())
                manifest_info["found"] = True
                manifest_info["url"] = manifest_url
                try:
                    with fetch_url_data(manifest_url, timeout=5) as resp_m:
                        m_code = resp_m.read().decode('utf-8', errors='ignore')
                        try:
                            manifest_info["raw_code"] = json.dumps(json.loads(m_code), indent=2)
                        except Exception:
                            manifest_info["raw_code"] = m_code
                except Exception as me:
                    manifest_info["raw_code"] = f"Failed to fetch manifest content: {str(me)}"

            # Contact Extractor
            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_code)
            for em in found_emails:
                if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg', '.js', '.css', '.woff', '.woff2')):
                    emails.add(em.lower())

            tel_matches = re.findall(r'href=["\']tel:([^"\']+)["\']', html_code, re.IGNORECASE)
            for tm in tel_matches: phones.add(tm.strip())

            social_domains = ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com', 'x.com', 'youtube.com', 'github.com', 'telegram.me', 't.me', 'wa.me']

            # Categorized Links
            all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
            for href in all_hrefs:
                href_str = href.strip()
                if not href_str or href_str.startswith('#') or href_str.startswith('javascript:'): continue

                full_url = urllib.parse.urljoin(base_url, href_str)
                if any(sd in full_url.lower() for sd in social_domains): socials.add(full_url)

                if '.css' in full_url.lower(): css_links.add(full_url)
                elif any(ft in full_url.lower() for ft in ['.woff', '.woff2', '.ttf', '.eot']): font_links.add(full_url)
                else:
                    parsed_link = urllib.parse.urlparse(full_url)
                    if target_domain in parsed_link.netloc: internal_links.add(full_url)
                    elif parsed_link.netloc: external_links.add(full_url)

            # Script srcs
            scripts = re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
            for sc in scripts: js_links.add(urllib.parse.urljoin(base_url, sc))

            # Image srcs
            imgs = re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
            for img in imgs: img_links.add(urllib.parse.urljoin(base_url, img))

        internal_list = sorted(list(internal_links))
        external_list = sorted(list(external_links))
        css_list = sorted(list(css_links))
        js_list = sorted(list(js_links))
        img_list = sorted(list(img_links))
        font_list = sorted(list(font_links))

        # 5. Broken Links Check (Scan top internal sample links)
        broken_links_found = []
        for test_link in internal_list[:8]:
            try:
                req_chk = urllib.request.Request(test_link, headers=headers, method='HEAD')
                with urllib.request.urlopen(req_chk, context=ctx, timeout=3) as r_chk:
                    if r_chk.status >= 400: broken_links_found.append(test_link)
            except urllib.error.HTTPError as he:
                if he.code in [404, 500, 502, 503]: broken_links_found.append(test_link)
            except Exception:
                pass

        # 6. WHOIS Data Retrieval
        registrar = "N/A"
        creation_date = "N/A"
        expiration_date = "N/A"
        nameservers = []
        raw_whois_text = ""

        try:
            api_url = f"https://api.ip2whois.com/v1?key=free&domain={target_domain}"
            req_api = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req_api, context=ctx, timeout=6) as resp_api:
                data_api = json.loads(resp_api.read().decode('utf-8', errors='ignore'))
                if "registrar" in data_api:
                    registrar = data_api.get("registrar", {}).get("name", "N/A")
                    creation_date = data_api.get("create_date", "N/A")
                    expiration_date = data_api.get("expire_date", "N/A")
                    nameservers = data_api.get("nameservers", [])
                    raw_whois_text = json.dumps(data_api, indent=2)
        except Exception:
            pass

        if registrar == "N/A" or not raw_whois_text:
            try:
                rdap_url = f"https://rdap.org/domain/{target_domain}"
                req_rdap = urllib.request.Request(rdap_url, headers=headers)
                with urllib.request.urlopen(req_rdap, context=ctx, timeout=6) as resp_rdap:
                    rdap_data = json.loads(resp_rdap.read().decode('utf-8', errors='ignore'))
                    raw_whois_text = json.dumps(rdap_data, indent=2)

                    for ev in rdap_data.get('events', []):
                        action = ev.get('eventAction')
                        date_val = ev.get('eventDate', '').split('T')[0]
                        if action == 'registration': creation_date = date_val
                        elif action == 'expiration': expiration_date = date_val

                    for ent in rdap_data.get('entities', []):
                        if 'registrar' in ent.get('roles', []):
                            for item in ent.get('vcardArray', [[], []])[1]:
                                if item[0] == 'fn': registrar = item[3]

                    for ns in rdap_data.get('nameservers', []):
                        if ns.get('ldhName'): nameservers.append(ns.get('ldhName'))
            except Exception:
                raw_whois_text = f"WHOIS / RDAP Data for TLD '.{target_domain.split('.')[-1]}' is privacy-protected or restricted."

        ns_display = ", ".join(nameservers) if nameservers else "N/A"

        # --- COMPREHENSIVE DETAILED LOG GENERATOR ---
        full_detailed_log = f"""======================================================================
🛰️ OMNI RECON REPORT & ASSET AUDIT LOG FOR: {target_domain.upper()}
======================================================================

⚡ 1. PERFORMANCE & SECURITY VERDICT:
----------------------------------------------------------------------
  • Website Load Speed  : {load_speed_ms} ms ({load_speed_sec} seconds)
  • SSL Certificate     : {'VALID' if ssl_info['valid'] else 'INVALID'}
  • SSL Issuer Organization: {ssl_info['issuer']}
  • SSL Expiry Date     : {ssl_info['expire_date']} ({ssl_info['days_left']} days left)
  • Manifest.json Link  : {manifest_info['url'] if manifest_info['found'] else 'Not Found'}
  • Broken Links Count  : {len(broken_links_found)} Detected

📞 2. EXTRACTED CONTACTS & SOCIALS:
----------------------------------------------------------------------
  • Emails Found ({len(emails)})    : {', '.join(list(emails)) if emails else 'None'}
  • Phones Found ({len(phones)})    : {', '.join(list(phones)) if phones else 'None'}
  • Social Profiles ({len(socials)}):
{chr(10).join(['     - ' + s for s in list(socials)]) if socials else '     - None Detected'}

🖼️ 3. CATEGORIZED ASSET BREAKDOWN:
----------------------------------------------------------------------
🔗 Internal Domain Links ({len(internal_list)}):
{chr(10).join(['     - ' + p for p in internal_list[:10]]) if internal_list else '     - None'}

🌐 External Domain Links ({len(external_list)}):
{chr(10).join(['     - ' + e for e in external_list[:10]]) if external_list else '     - None'}

🎨 CSS Stylesheets ({len(css_list)}):
{chr(10).join(['     - ' + c for c in css_list[:10]]) if css_list else '     - None'}

📜 JavaScript Files ({len(js_list)}):
{chr(10).join(['     - ' + j for j in js_list[:10]]) if js_list else '     - None'}

🖼️ Image Assets ({len(img_list)}):
{chr(10).join(['     - ' + i for i in img_list[:10]]) if img_list else '     - None'}

🔤 WOFF / Font Assets ({len(font_list)}):
{chr(10).join(['     - ' + f for f in font_list[:10]]) if font_list else '     - None'}

======================================================================
🌐 4. GEOLOCATION & WHOIS SERVER RECORD:
======================================================================
{raw_whois_text}
"""

        return jsonify({
            "status": "success",
            "domain": target_domain,
            "load_speed_ms": load_speed_ms,
            "load_speed_sec": load_speed_sec,
            "ssl_info": ssl_info,
            "broken_links": {
                "count": len(broken_links_found),
                "list": broken_links_found
            },
            "manifest": manifest_info,
            "is_responsive": is_responsive,
            "favicon_found": favicon_found,
            "favicon_url": favicon_url,
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
            "contacts": {
                "emails": list(emails),
                "phones": list(phones),
                "socials": list(socials)
            },
            "asset_counts": {
                "internal": len(internal_list),
                "external": len(external_list),
                "css": len(css_list),
                "js": len(js_list),
                "images": len(img_list),
                "fonts": len(font_list)
            },
            "assets": {
                "internal": internal_list,
                "external": external_list,
                "css": css_list,
                "js": js_list,
                "images": img_list,
                "fonts": font_list,
                "broken": broken_links_found
            },
            "full_detailed_log": full_detailed_log
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Audit process error: {str(e)}"
        })

