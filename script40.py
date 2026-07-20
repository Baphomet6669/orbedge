import os
import json
import time
import socket
import ssl
import re
import urllib.parse
import concurrent.futures
from datetime import datetime
import requests
from flask import Blueprint, render_template_string, request, jsonify, session

# =========================================================================
# FLASK BLUEPRINT DEFINITION
# =========================================================================
script40_bp = Blueprint('script40', __name__)

# =========================================================================
# HELPER PARSING FUNCTIONS
# =========================================================================
def clean_domain_input(url_input):
    url_input = url_input.strip()
    if not url_input.startswith(('http://', 'https://')):
        full_url = 'https://' + url_input
    else:
        full_url = url_input
    
    parsed = urllib.parse.urlparse(full_url)
    domain = parsed.netloc or parsed.path
    if ':' in domain:
        domain = domain.split(':')[0]
    
    base_scheme_url = f"{parsed.scheme}://{domain}"
    return domain, full_url, base_scheme_url

def check_file_availability(url):
    try:
        res = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            return True, res.status_code
        elif res.status_code == 405: # Method Not Allowed for HEAD, try GET
            res_get = requests.get(url, timeout=3, stream=True, headers={"User-Agent": "Mozilla/5.0"})
            return res_get.status_code == 200, res_get.status_code
        return False, res.status_code
    except Exception:
        return False, "Unreachable"

def extract_meta_tag(html, name_or_property):
    # Regex for standard name="attr" or property="og:attr"
    pattern = rf'<meta\s+(?:name|property)=["\']{re.escape(name_or_property)}["\']\s+content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        pattern_alt = rf'<meta\s+content=["\']([^"\']*)["\']\s+(?:name|property)=["\']{re.escape(name_or_property)}["\']'
        match = re.search(pattern_alt, html, re.IGNORECASE)
    return match.group(1) if match else None

# =========================================================================
# CONTROLLER ROUTING LOGIC
# =========================================================================
@script40_bp.route('/')
def index():
    if 'logged_in' not in session:
        return "<h3 style='color:white; font-family:sans-serif;'>ACCESS DENIED: Please log in from main dashboard.</h3>", 403
    return render_template_string(UI_LAYOUT)

@script40_bp.route('/api/audit', methods=['POST'])
def run_toolkit_audit():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized Terminal"}), 401
        
    target_raw = request.form.get('target', '').strip()
    if not target_raw:
        return jsonify({"success": False, "message": "Target endpoint parameters empty."})

    domain, full_url, base_scheme_url = clean_domain_input(target_raw)
    
    start_time = time.time()
    try:
        res = requests.get(full_url, timeout=6, headers={"User-Agent": "OrbitEdge-SecOps-Engine/4.0"})
        latency = round((time.time() - start_time) * 1000, 2)
        html_body = res.text
        res_headers = res.headers
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Target unreachable or execution connection timed out: {str(e)}"
        })

    # 1. Title Extraction
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_body, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else "No Title Tag Found"

    # 2. Meta Tags Extraction
    meta_description = extract_meta_tag(html_body, "description") or "Not Specified"
    meta_keywords = extract_meta_tag(html_body, "keywords") or "Not Specified"
    og_title = extract_meta_tag(html_body, "og:title") or "Not Specified"
    og_description = extract_meta_tag(html_body, "og:description") or "Not Specified"

    # 3. Heading Tags Hierarchy (H1 to H5)
    headings = {}
    for i in range(1, 6):
        tag_name = f"h{i}"
        matches = re.findall(rf'<{tag_name}[^>]*>(.*?)</{tag_name}>', html_body, re.IGNORECASE | re.DOTALL)
        clean_matches = [re.sub(r'<[^>]+>', '', m).strip() for m in matches if m.strip()]
        headings[tag_name.upper()] = {
            "count": len(clean_matches),
            "sample": clean_matches[:3] # Show up to 3 samples
        }

    # 4. Canonical URL
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    canonical_url = canonical_match.group(1) if canonical_match else "Not Configured"

    # 5. Favicon Detection
    favicon_match = re.search(r'<link\s+rel=["\'](?:shortcut )?icon["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    if favicon_match:
        fav_path = favicon_match.group(1)
        favicon_url = urllib.parse.urljoin(full_url, fav_path)
    else:
        favicon_url = f"{base_scheme_url}/favicon.ico"

    # 6. Header and Footer Presence
    has_header_tag = bool(re.search(r'<(header|nav)[^>]*>', html_body, re.IGNORECASE))
    has_footer_tag = bool(re.search(r'<footer[^>]*>', html_body, re.IGNORECASE))

    # 7. Asynchronous File Detection (Sitemap, Robots, Manifest)
    sitemap_url = f"{base_scheme_url}/sitemap.xml"
    robots_url = f"{base_scheme_url}/robots.txt"
    manifest_url = f"{base_scheme_url}/manifest.json"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_sitemap = executor.submit(check_file_availability, sitemap_url)
        f_robots = executor.submit(check_file_availability, robots_url)
        f_manifest = executor.submit(check_file_availability, manifest_url)
        
        has_sitemap, sitemap_status = f_sitemap.result()
        has_robots, robots_status = f_robots.result()
        has_manifest, manifest_status = f_manifest.result()

    # 8. Broken Link Detection (On-page anchors checked concurrently - top 6)
    found_links = list(set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html_body)))[:6]
    broken_links = []
    
    def check_link(link):
        try:
            r = requests.head(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code >= 400:
                broken_links.append({"url": link, "status": r.status_code})
        except Exception:
            broken_links.append({"url": link, "status": "Failed/Timeout"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(check_link, found_links)

    # 9. HTTPS Security Check
    is_https = full_url.startswith("https://")

    # 10. WHOIS Lookup Mapping
    try:
        ip_address = socket.gethostbyname(domain)
        dns_records = socket.gethostbyname_ex(domain)
        whois_data = f"Domain Name: {domain}\nResolved IP: {ip_address}\nCanonical Name: {dns_records[0]}\nServer Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    except Exception:
        ip_address = "Resolution Failed"
        whois_data = f"Domain Name: {domain}\nStatus: Could not resolve DNS record."

    return jsonify({
        "success": True,
        "domain": domain,
        "full_url": full_url,
        "latency": latency,
        "is_https": is_https,
        "ip_address": ip_address,
        "title": page_title,
        "canonical_url": canonical_url,
        "favicon_url": favicon_url,
        "meta": {
            "description": meta_description,
            "keywords": meta_keywords,
            "og_title": og_title,
            "og_description": og_description
        },
        "headings": headings,
        "structure": {
            "has_header": has_header_tag,
            "has_footer": has_footer_tag
        },
        "files": {
            "sitemap": {"exists": has_sitemap, "url": sitemap_url, "code": sitemap_status},
            "robots": {"exists": has_robots, "url": robots_url, "code": robots_status},
            "manifest": {"exists": has_manifest, "url": manifest_url, "code": manifest_status}
        },
        "broken_links": broken_links,
        "whois": whois_data
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
    <title>Enterprise Web & SEO Audit Suite</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f3f4f6; }
        .heading-font { font-family: 'Space Grotesk', sans-serif; }
        .cyber-card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .terminal-box { font-family: 'Courier New', monospace; background: #050811; border: 1px solid #1f2937; }
        .glow-indigo { box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.3); }
    </style>
</head>
<body class="antialiased selection:bg-indigo-500 selection:text-white pb-12">

    <div class="max-w-[1400px] mx-auto p-4 md:p-8 space-y-6">
        
        <!-- HEADER TOP BANNER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-2xl font-bold heading-font tracking-wide text-white flex items-center gap-2">
                    <i class="fa-solid fa-microchip text-indigo-400"></i> Modern Web & SEO Audit Suite
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Realtime Diagnostic • Infrastructure & SEO Intelligence</p>
            </div>
            <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
            </a>
        </div>

        <!-- TARGET INPUT PANEL -->
        <div class="cyber-card p-6 rounded-2xl glow-indigo">
            <form id="auditForm" onsubmit="triggerScanSequence(event)" class="space-y-3">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Target Domain / URL Address</label>
                <div class="flex flex-col sm:flex-row gap-3">
                    <div class="relative flex-1">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-globe text-sm"></i></span>
                        <input type="text" id="targetUrl" required placeholder="e.g. google.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Start Instant Audit</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- MAIN DASHBOARD METRICS (HIDDEN BEFORE SCAN) -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- QUICK METRIC BADGES -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">HTTPS Status</span>
                    <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Response Latency</span>
                    <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Layout Structure</span>
                    <h3 id="badge-structure" class="text-xs md:text-sm font-bold text-emerald-400 mt-1">Header / Footer</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">IP Host</span>
                    <h3 id="badge-ip" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                </div>
            </div>

            <!-- SYSTEM FILE AUDIT ROW -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div id="card-sitemap" class="cyber-card p-4 rounded-xl border flex items-center justify-between">
                    <div>
                        <p class="text-xs font-bold text-gray-200">Sitemap File</p>
                        <p class="text-[11px] font-mono text-gray-400">/sitemap.xml</p>
                    </div>
                    <span id="status-sitemap" class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase font-mono">Checking</span>
                </div>
                <div id="card-robots" class="cyber-card p-4 rounded-xl border flex items-center justify-between">
                    <div>
                        <p class="text-xs font-bold text-gray-200">Robots Directive</p>
                        <p class="text-[11px] font-mono text-gray-400">/robots.txt</p>
                    </div>
                    <span id="status-robots" class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase font-mono">Checking</span>
                </div>
                <div id="card-manifest" class="cyber-card p-4 rounded-xl border flex items-center justify-between">
                    <div>
                        <p class="text-xs font-bold text-gray-200">Web Manifest</p>
                        <p class="text-[11px] font-mono text-gray-400">/manifest.json</p>
                    </div>
                    <span id="status-manifest" class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase font-mono">Checking</span>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT SECTION (SEO & TAGS) -->
                <div class="lg:col-span-2 space-y-6">
                    
                    <!-- TITLE & CANONICAL & FAVICON CARD -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                            <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                                <i class="fa-solid fa-[#00ffcc] fa-heading text-indigo-400"></i> Page Metadata & Identity
                            </h3>
                            <div id="favicon-wrapper" class="flex items-center gap-2 bg-gray-900 border border-gray-800 px-3 py-1 rounded-lg">
                                <img id="img-favicon" src="" alt="Favicon" class="w-4 h-4 object-contain">
                                <span class="text-[10px] text-gray-400 font-mono">Favicon</span>
                            </div>
                        </div>

                        <div class="space-y-3 text-xs">
                            <div>
                                <span class="text-gray-400 font-semibold uppercase text-[10px]">Title Tag:</span>
                                <p id="val-title" class="text-white font-medium bg-gray-950 p-2.5 rounded-lg border border-gray-800/80 mt-1"></p>
                            </div>
                            <div>
                                <span class="text-gray-400 font-semibold uppercase text-[10px]">Canonical Tag:</span>
                                <p id="val-canonical" class="text-indigo-300 font-mono bg-gray-950 p-2.5 rounded-lg border border-gray-800/80 mt-1 truncate"></p>
                            </div>
                        </div>
                    </div>

                    <!-- META TAGS CARD -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-tags text-indigo-400"></i> Meta Directives Engine
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                            <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800/80 space-y-1">
                                <span class="text-indigo-400 font-bold text-[10px] uppercase font-mono">Meta Description</span>
                                <p id="meta-desc" class="text-gray-300 leading-relaxed text-[11px]"></p>
                            </div>
                            <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800/80 space-y-1">
                                <span class="text-indigo-400 font-bold text-[10px] uppercase font-mono">Meta Keywords</span>
                                <p id="meta-keys" class="text-gray-300 leading-relaxed text-[11px]"></p>
                            </div>
                            <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800/80 space-y-1">
                                <span class="text-cyan-400 font-bold text-[10px] uppercase font-mono">OG: Title</span>
                                <p id="og-title" class="text-gray-300 leading-relaxed text-[11px]"></p>
                            </div>
                            <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800/80 space-y-1">
                                <span class="text-cyan-400 font-bold text-[10px] uppercase font-mono">OG: Description</span>
                                <p id="og-desc" class="text-gray-300 leading-relaxed text-[11px]"></p>
                            </div>
                        </div>
                    </div>

                    <!-- HEADING TAGS (H1 TO H5) -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-sitemap text-indigo-400"></i> Heading Structure Analysis (H1 — H5)
                        </h3>
                        <div id="headings-container" class="space-y-3"></div>
                    </div>

                </div>

                <!-- RIGHT SECTION (BROKEN LINKS & WHOIS) -->
                <div class="space-y-6">
                    
                    <!-- BROKEN LINK SCANNER CARD -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-link-slash text-rose-400"></i> Broken Link Diagnostics
                        </h3>
                        <div id="broken-links-container" class="space-y-2 max-h-64 overflow-y-auto"></div>
                    </div>

                    <!-- WHOIS LOOKUP TERMINAL -->
                    <div class="cyber-card p-6 rounded-2xl space-y-3">
                        <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                            <i class="fa-solid fa-terminal text-purple-400"></i> WHOIS & Host Record
                        </h3>
                        <pre id="whois-logs" class="terminal-box p-3.5 rounded-xl text-[11px] text-gray-300 whitespace-pre-wrap leading-relaxed min-h-36"></pre>
                    </div>

                </div>
            </div>

        </div>
    </div>

    <script>
        async function triggerScanSequence(e) {
            e.preventDefault();
            const target = document.getElementById('targetUrl').value;
            const submitBtn = document.getElementById('submitBtn');
            const spinIcon = document.getElementById('spinIcon');
            const dashboard = document.getElementById('analyticsDashboard');

            submitBtn.disabled = true;
            spinIcon.classList.remove('hidden');

            let fd = new FormData();
            fd.append('target', target);

            try {
                let response = await fetch('/script40/api/audit', { method: 'POST', body: fd });
                let data = await response.json();

                if (data.success) {
                    // Quick Badges
                    const httpsEl = document.getElementById('badge-https');
                    if (data.is_https) {
                        httpsEl.className = "text-xs md:text-sm font-bold text-emerald-400 mt-1 flex items-center gap-1";
                        httpsEl.innerHTML = `<i class="fa-solid fa-lock"></i> HTTPS Secure`;
                    } else {
                        httpsEl.className = "text-xs md:text-sm font-bold text-rose-400 mt-1 flex items-center gap-1";
                        httpsEl.innerHTML = `<i class="fa-solid fa-unlock"></i> HTTP Insecure`;
                    }

                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;
                    document.getElementById('badge-ip').innerText = data.ip_address;

                    const structEl = document.getElementById('badge-structure');
                    let structText = [];
                    if (data.structure.has_header) structText.push("Header");
                    if (data.structure.has_footer) structText.push("Footer");
                    structEl.innerText = structText.length > 0 ? structText.join(" + ") : "No Semantic Tags";

                    // File Checks Status helper
                    const setFileStatus = (cardId, statusId, fileObj) => {
                        const card = document.getElementById(cardId);
                        const badge = document.getElementById(statusId);
                        if (fileObj.exists) {
                            card.className = "cyber-card p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 flex items-center justify-between";
                            badge.className = "px-2.5 py-1 rounded-md text-[10px] font-bold uppercase font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                            badge.innerText = `Found (${fileObj.code})`;
                        } else {
                            card.className = "cyber-card p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 flex items-center justify-between";
                            badge.className = "px-2.5 py-1 rounded-md text-[10px] font-bold uppercase font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30";
                            badge.innerText = `Missing (${fileObj.code})`;
                        }
                    };

                    setFileStatus('card-sitemap', 'status-sitemap', data.files.sitemap);
                    setFileStatus('card-robots', 'status-robots', data.files.robots);
                    setFileStatus('card-manifest', 'status-manifest', data.files.manifest);

                    // Page Metadata
                    document.getElementById('val-title').innerText = data.title;
                    document.getElementById('val-canonical').innerText = data.canonical_url;
                    document.getElementById('img-favicon').src = data.favicon_url;

                    // Meta Tags
                    document.getElementById('meta-desc').innerText = data.meta.description;
                    document.getElementById('meta-keys').innerText = data.meta.keywords;
                    document.getElementById('og-title').innerText = data.meta.og_title;
                    document.getElementById('og-desc').innerText = data.meta.og_description;

                    // Heading Hierarchy Mapping (H1 - H5)
                    const headingsContainer = document.getElementById('headings-container');
                    headingsContainer.innerHTML = '';
                    Object.keys(data.headings).forEach(tag => {
                        const item = data.headings[tag];
                        const samples = item.sample.length > 0 ? item.sample.map(s => `<li class="truncate">• ${s}</li>`).join('') : '<li class="text-gray-500 italic">No tags detected</li>';
                        headingsContainer.innerHTML += `
                            <div class="bg-gray-950 p-3 rounded-xl border border-gray-800 text-xs">
                                <div class="flex items-center justify-between mb-1.5">
                                    <span class="font-bold font-mono text-indigo-400 text-xs">${tag} Tag</span>
                                    <span class="bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded text-[10px] font-mono font-bold">${item.count} Found</span>
                                </div>
                                <ul class="text-[11px] text-gray-400 space-y-1 font-mono">${samples}</ul>
                            </div>
                        `;
                    });

                    // Broken Links Loop
                    const linksContainer = document.getElementById('broken-links-container');
                    linksContainer.innerHTML = '';
                    if (data.broken_links.length === 0) {
                        linksContainer.innerHTML = `<div class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center text-emerald-400 text-xs font-medium"><i class="fa-solid fa-circle-check mr-1.5"></i> No Broken Anchors Detected!</div>`;
                    } else {
                        data.broken_links.forEach(l => {
                            linksContainer.innerHTML += `
                                <div class="p-2.5 bg-gray-950 border border-rose-500/30 rounded-xl flex items-center justify-between text-xs gap-2">
                                    <span class="text-gray-300 font-mono truncate text-[11px]" title="${l.url}">${l.url}</span>
                                    <span class="bg-rose-500/20 border border-rose-500/30 text-rose-400 font-bold px-2 py-0.5 rounded text-[10px] font-mono shrink-0">${l.status}</span>
                                </div>
                            `;
                        });
                    }

                    // WHOIS
                    document.getElementById('whois-logs').innerText = data.whois;

                    // Unhide Dashboard
                    dashboard.classList.remove('hidden');
                } else {
                    alert(data.message || "Audit engine encountered an issue.");
                }
            } catch (err) {
                console.error("Audit Failure:", err);
                alert("Server request failed or connection timed out.");
            } finally {
                submitBtn.disabled = false;
                spinIcon.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

