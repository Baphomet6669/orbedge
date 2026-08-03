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

    /* Interactive Links Modal Styling */
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
        width: 80%;
        max-width: 800px;
        max-height: 80vh;
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
        padding: 10px;
        border-radius: 4px;
    }
    .modal-body a { color: var(--neon-green); word-break: break-all; display: block; margin-bottom: 6px; text-decoration: none; }
    .modal-body a:hover { text-decoration: underline; color: var(--neon-cyan); }
  </style>
</head>
<body>

    <div class="header-panel">
        <div class="brand-title">A-Z OMNI <span>DOMAIN & ASSET RECON ENGINE</span></div>
        <div class="brand-sub">WHOIS, Geolocation, Responsive, Favicon, Contacts, Asset Category Extraction & PDF Export</div>
        
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
                <div class="panel-header">🌐 Network, Contacts & Categorized Asset Matrix</div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>Parameter / Asset Type</th>
                                <th>Resolved Status / Click to View Links</th>
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

    <!-- Modal Window for Interactive Asset Link Lists -->
    <div class="modal-overlay" id="assetModal">
        <div class="modal-box">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">Extracted Links List</div>
                <button class="modal-close" onclick="closeModal()">X</button>
            </div>
            <div class="modal-body" id="modalBody">
                <!-- Dynamic links rendered here -->
            </div>
        </div>
    </div>

    <div class="status-footer" id="footer_log">Engine Ready.</div>

    <script>
        let currentDomain = "";
        let extractedAssetStore = {};

        async function triggerWhoisAudit() {
            const inputField = document.getElementById('target_url');
            let target = inputField.value.trim();
            if(!target) { alert("Bhai, valid website URL ya Domain name dalo!"); return; }

            const footer = document.getElementById('footer_log');
            const terminal = document.getElementById('whois_raw_terminal');
            const pdfBtn = document.getElementById('pdf_btn');
            
            footer.innerText = `📡 Deep Scanning WHOIS, Contacts, Categorized Links & Assets for ${target}...`;
            terminal.innerText = `[INITIALIZING] Scraper handshake active. Parsing domain assets and WHOIS records...`;
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
                extractedAssetStore = data.assets; // Save categorized asset lists

                // Responsive Badge Logic
                let respBadge = data.is_responsive 
                    ? `<span class="badge badge-success">YES (MOBILE-FRIENDLY)</span>` 
                    : `<span class="badge badge-danger">NO (NOT RESPONSIVE)</span>`;

                // Favicon Display Logic
                let faviconHTML = data.favicon_found 
                    ? `<img src="${data.favicon_url}" class="favicon-img" onerror="this.style.display='none'"> <a href="${data.favicon_url}" target="_blank" style="color:var(--neon-cyan);">${data.favicon_url}</a>`
                    : `<span class="badge badge-warning">FAVICON NOT DETECTED</span>`;

                // Contacts Formatting
                let emailsFormatted = data.contacts.emails.length > 0 ? data.contacts.emails.join(", ") : "None Detected";
                let phonesFormatted = data.contacts.phones.length > 0 ? data.contacts.phones.join(", ") : "None Detected";
                let socialsFormatted = data.contacts.socials.length > 0 ? data.contacts.socials.map(s => `<a href="${s}" target="_blank" style="color:var(--neon-cyan); margin-right:5px;">${new URL(s).hostname}</a>`).join(" | ") : "None Detected";

                // Render Summary Table
                const tableBody = document.getElementById('matrix_rows');
                tableBody.innerHTML = `
                    <tr><td style="color:var(--text-gray);">Target Domain</td><td style="font-weight:bold; color:#fff;">${data.domain}</td></tr>
                    <tr><td style="color:var(--text-gray);">Mobile Responsive Status</td><td>${respBadge}</td></tr>
                    <tr><td style="color:var(--text-gray);">Favicon Icon</td><td>${faviconHTML}</td></tr>
                    
                    <!-- Extracted Contacts -->
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Extracted Emails</td><td style="color:var(--neon-green); font-weight:bold;">${emailsFormatted}</td></tr>
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Extracted Phones</td><td>${phonesFormatted}</td></tr>
                    <tr style="background: rgba(6, 182, 212, 0.04);"><td style="color:var(--neon-cyan); font-weight:bold;">Social Profiles</td><td>${socialsFormatted}</td></tr>

                    <!-- Categorized Asset & Link Counts (Interactive) -->
                    <tr><td style="color:var(--text-gray);">Internal Domain Links</td><td><span class="badge badge-info badge-interactive" onclick="viewCategoryLinks('internal')">🔗 ${data.asset_counts.internal} Internal Links (Click to View)</span></td></tr>
                    <tr><td style="color:var(--text-gray);">External Domain Links</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('external')">🌐 ${data.asset_counts.external} External Links (Click to View)</span></td></tr>
                    <tr><td style="color:var(--text-gray);">CSS Stylesheets</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('css')">🎨 ${data.asset_counts.css} CSS Files (Click to View)</span></td></tr>
                    <tr><td style="color:var(--text-gray);">JavaScript Files</td><td><span class="badge badge-warning badge-interactive" onclick="viewCategoryLinks('js')">📜 ${data.asset_counts.js} JS Scripts (Click to View)</span></td></tr>
                    <tr><td style="color:var(--text-gray);">Images Asset Links</td><td><span class="badge badge-success badge-interactive" onclick="viewCategoryLinks('images')">🖼️ ${data.asset_counts.images} Images (Click to View)</span></td></tr>
                    <tr><td style="color:var(--text-gray);">WOFF / Font Assets</td><td><span class="badge badge-info badge-interactive" onclick="viewCategoryLinks('fonts')">🔤 ${data.asset_counts.fonts} Fonts Discovered (Click to View)</span></td></tr>

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
                    <tr><td style="color:var(--text-gray);">Server Latency</td><td>${data.latency}</td></tr>
                `;

                terminal.innerText = data.full_detailed_log;
                footer.innerText = `✅ WHOIS, Contacts, Categorized Asset Extractor & Geolocation completed for ${data.domain}`;
                pdfBtn.style.display = "inline-block";

            } catch(err) {
                terminal.innerText = `[CRITICAL ERROR] Execution pipeline timed out or failed.`;
                footer.innerText = `❌ Execution Fault.`;
            }
        }

        // Interactive Modal Function for Viewing Asset Category Links
        function viewCategoryLinks(categoryKey) {
            const modal = document.getElementById('assetModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            const links = extractedAssetStore[categoryKey] || [];
            title.innerText = `Extracted ${categoryKey.toUpperCase()} Assets / Links (${links.length} Found)`;

            if (links.length === 0) {
                body.innerHTML = `<div style="color: var(--text-gray); text-align: center; padding: 20px;">No links found in this category.</div>`;
            } else {
                body.innerHTML = links.map((link, idx) => `<a href="${link}" target="_blank" rel="noopener noreferrer">${idx + 1}. ${link}</a>`).join('');
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
    base_url = f"https://{target_domain}"

    # SSL Bypass context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        # 1. IP Resolution & Latency
        start_time = time.time()
        try:
            resolved_ip = socket.gethostbyname(target_domain)
            latency = f"{round((time.time() - start_time) * 1000, 2)} ms"
        except Exception:
            resolved_ip = "Unable to Resolve IP"
            latency = "N/A"

        # 2. IP Geolocation (State, City, Country, Lat, Lon, ISP)
        ip_info = {}
        if resolved_ip != "Unable to Resolve IP":
            try:
                geo_url = f"http://ip-api.com/json/{resolved_ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
                req_geo = urllib.request.Request(geo_url, headers=headers)
                with urllib.request.urlopen(req_geo, timeout=5) as resp:
                    ip_info = json.loads(resp.read().decode('utf-8'))
            except Exception:
                pass

        # 3. HTML Scraping for Contacts, Favicon, Responsiveness & Categorized Assets
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

        try:
            req_html = urllib.request.Request(base_url, headers=headers)
            with urllib.request.urlopen(req_html, context=ctx, timeout=7) as html_resp:
                html_code = html_resp.read().decode('utf-8', errors='ignore')

                # Responsive check
                if re.search(r'<meta\s+[^>]*name=["\']viewport["\']', html_code, re.IGNORECASE) or "@media" in html_code:
                    is_responsive = True

                # Favicon Extraction
                fav_match = re.search(r'<link\s+[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
                if not fav_match:
                    fav_match = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut )?icon["\']', html_code, re.IGNORECASE)

                if fav_match:
                    extracted_fav = fav_match.group(1).strip()
                    favicon_url = urllib.parse.urljoin(base_url, extracted_fav)
                    favicon_found = True
                else:
                    fallback_fav = f"{base_url}/favicon.ico"
                    try:
                        req_fav = urllib.request.Request(fallback_fav, headers=headers)
                        with urllib.request.urlopen(req_fav, context=ctx, timeout=3) as resp_fav:
                            if resp_fav.status == 200:
                                favicon_url = fallback_fav
                                favicon_found = True
                    except Exception:
                        pass

                # --- CONTACT EXTRACTOR ---
                found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_code)
                for em in found_emails:
                    if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg', '.js', '.css', '.woff', '.woff2')):
                        emails.add(em.lower())

                tel_matches = re.findall(r'href=["\']tel:([^"\']+)["\']', html_code, re.IGNORECASE)
                for tm in tel_matches:
                    phones.add(tm.strip())
                
                raw_phones = re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', html_code)
                for ph in raw_phones[:5]:
                    if len(ph.strip()) >= 10:
                        phones.add(ph.strip())

                social_domains = ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com', 'x.com', 'youtube.com', 'github.com', 'telegram.me', 't.me', 'wa.me']

                # --- CATEGORIZED LINK & ASSET SCRAPING ---
                # All hrefs
                all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
                for href in all_hrefs:
                    href_str = href.strip()
                    if not href_str or href_str.startswith('#') or href_str.startswith('javascript:'):
                        continue

                    full_url = urllib.parse.urljoin(base_url, href_str)

                    # Check for Socials
                    if any(sd in full_url.lower() for sd in social_domains):
                        socials.add(full_url)

                    # Categorize CSS
                    if '.css' in full_url.lower():
                        css_links.add(full_url)
                    # Categorize Fonts
                    elif any(ft in full_url.lower() for ft in ['.woff', '.woff2', '.ttf', '.eot', '.otf']):
                        font_links.add(full_url)
                    # Categorize Page Links (Internal vs External)
                    else:
                        parsed_link = urllib.parse.urlparse(full_url)
                        if target_domain in parsed_link.netloc:
                            internal_links.add(full_url)
                        elif parsed_link.netloc:
                            external_links.add(full_url)

                # Script srcs (JS)
                scripts = re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
                for sc in scripts:
                    js_links.add(urllib.parse.urljoin(base_url, sc))

                # Image srcs
                imgs = re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_code, re.IGNORECASE)
                for img in imgs:
                    img_links.add(urllib.parse.urljoin(base_url, img))

                # Additional WOFF / Font Srcs inside inline CSS or src attributes
                fonts_in_src = re.findall(r'url\(["\']?([^"\'\)]+\.(?:woff2?|ttf|eot|otf))["\']?\)', html_code, re.IGNORECASE)
                for fn in fonts_in_src:
                    font_links.add(urllib.parse.urljoin(base_url, fn))

        except Exception:
            pass

        # Convert sets to sorted lists
        internal_list = sorted(list(internal_links))
        external_list = sorted(list(external_links))
        css_list = sorted(list(css_links))
        js_list = sorted(list(js_links))
        img_list = sorted(list(img_links))
        font_list = sorted(list(font_links))

        # 4. WHOIS Data Retrieval
        registrar = "N/A"
        creation_date = "N/A"
        expiration_date = "N/A"
        nameservers = []
        raw_whois_text = ""

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

        if registrar == "N/A" or not raw_whois_text:
            try:
                rdap_url = f"https://rdap.org/domain/{target_domain}"
                req_rdap = urllib.request.Request(rdap_url, headers=headers)
                with urllib.request.urlopen(req_rdap, context=ctx, timeout=6) as resp_rdap:
                    rdap_data = json.loads(resp_rdap.read().decode('utf-8'))
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

📞 1. EXTRACTED CONTACTS & SOCIALS:
----------------------------------------------------------------------
  • Emails Found ({len(emails)})    : {', '.join(list(emails)) if emails else 'None'}
  • Phones Found ({len(phones)})    : {', '.join(list(phones)) if phones else 'None'}
  • Social Profiles ({len(socials)}):
{chr(10).join(['     - ' + s for s in list(socials)]) if socials else '     - None Detected'}

🖼️ 2. CATEGORIZED ASSET BREAKDOWN:
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
🌐 3. GEOLOCATION & WHOIS SERVER RECORD:
======================================================================
{raw_whois_text}
"""

        return jsonify({
            "status": "success",
            "domain": target_domain,
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
            "latency": latency,
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
                "fonts": font_list
            },
            "full_detailed_log": full_detailed_log
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Audit process error: {str(e)}"
        })


