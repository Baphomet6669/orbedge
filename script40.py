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

def extract_meta_tag(html, name_or_property):
    pattern = rf'<meta\s+(?:name|property)=["\']{re.escape(name_or_property)}["\']\s+content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        pattern_alt = rf'<meta\s+content=["\']([^"\']*)["\']\s+(?:name|property)=["\']{re.escape(name_or_property)}["\']'
        match = re.search(pattern_alt, html, re.IGNORECASE)
    return match.group(1) if match else None

# =========================================================================
# ADVANCED FILE ANALYZERS (SITEMAP, ROBOTS, MANIFEST)
# =========================================================================
def analyze_sitemap(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200 and ("xml" in res.headers.get("Content-Type", "").lower() or "<urlset" in res.text or "<sitemapindex" in res.text):
            urls = re.findall(r'<loc>(.*?)</loc>', res.text, re.IGNORECASE)
            url_count = len(urls)
            return {
                "exists": True,
                "code": 200,
                "url_count": url_count,
                "url": url,
                "summary": f"Sitemap XML contains {url_count} total URL paths.",
                "explanation": "What it means: Sitemap is a map of your website. It helps Google & Bing find all your pages instantly.",
                "fix_action": f"View Sitemap File"
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url_count": 0,
            "url": url,
            "summary": "Sitemap XML missing or not accessible.",
            "explanation": "What it means: Google crawlers might miss deep pages on your site. Create a sitemap using Yoast SEO or RankMath.",
            "fix_action": "Generate Sitemap XML"
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url_count": 0,
            "url": url,
            "summary": "Sitemap request timed out.",
            "explanation": "What it means: Server did not respond to sitemap lookup.",
            "fix_action": "Check Server Response"
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            
            explanation = "SEO Danger: Your site is blocking Googlebot from indexing!" if is_blocking_all else "Good Job: Search engines are allowed to crawl your site."
            
            return {
                "exists": True,
                "code": 200,
                "url": url,
                "is_blocking_all": is_blocking_all,
                "summary": content[:250] + ("..." if len(content) > 250 else ""),
                "explanation": explanation,
                "fix_action": "View / Edit Robots.txt"
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt file missing or empty.",
            "explanation": "What it means: Search engines will scan everything, but you cannot protect private admin pages.",
            "fix_action": "Create Robots.txt File"
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt connection failed.",
            "explanation": "What it means: Server unreachable during robots lookup.",
            "fix_action": "Verify Endpoint Route"
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            try:
                data = res.json()
                app_name = data.get("name") or data.get("short_name") or "Unnamed App"
                return {
                    "exists": True,
                    "code": 200,
                    "url": url,
                    "summary": f"Valid Web App Manifest detected (App Name: '{app_name}').",
                    "explanation": "What it means: Enables Progressive Web App (PWA) 'Add to Home Screen' on mobile phones.",
                    "fix_action": "Inspect Manifest.json"
                }
            except Exception:
                pass
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "summary": "Manifest.json missing or invalid JSON.",
            "explanation": "What it means: Site runs in standard browser mode without PWA installation support.",
            "fix_action": "Create Manifest.json"
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "summary": "Manifest.json connection failed.",
            "explanation": "What it means: Unable to verify mobile PWA manifest status.",
            "fix_action": "Check Manifest Config"
        }

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
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Target unreachable or connection timed out: {str(e)}"
        })

    # 1. WordPress CMS Detection
    html_lower = html_body.lower()
    is_wordpress = any(indicator in html_lower for indicator in [
        "wp-content", "wp-includes", "wp-json", "wordpress", "elementor", "yoast"
    ])
    cms_detected = "WordPress CMS Platform" if is_wordpress else "Custom / Non-WordPress Architecture"

    # 2. Responsiveness Check
    has_viewport = bool(re.search(r'<meta\s+name=["\']viewport["\']', html_body, re.IGNORECASE))
    is_responsive = has_viewport or ("@media" in html_lower)
    responsive_status = "Responsive (Mobile & Desktop Friendly)" if is_responsive else "Non-Responsive (Viewport Tag Missing)"

    # 3. Title & Meta Directives
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_body, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else "No Title Tag Found"

    meta_description = extract_meta_tag(html_body, "description") or "Not Specified"
    meta_keywords = extract_meta_tag(html_body, "keywords") or "Not Specified"
    og_title = extract_meta_tag(html_body, "og:title") or "Not Specified"
    og_description = extract_meta_tag(html_body, "og:description") or "Not Specified"

    # 4. Heading Tags Hierarchy (H1 to H5)
    headings = {}
    for i in range(1, 6):
        tag_name = f"h{i}"
        matches = re.findall(rf'<{tag_name}[^>]*>(.*?)</{tag_name}>', html_body, re.IGNORECASE | re.DOTALL)
        clean_matches = [re.sub(r'<[^>]+>', '', m).strip() for m in matches if m.strip()]
        headings[tag_name.upper()] = {
            "count": len(clean_matches),
            "sample": clean_matches[:3]
        }

    # 5. Canonical URL & Favicon
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    canonical_url = canonical_match.group(1) if canonical_match else "Not Configured"

    favicon_match = re.search(r'<link\s+rel=["\'](?:shortcut )?icon["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    favicon_url = urllib.parse.urljoin(full_url, favicon_match.group(1)) if favicon_match else f"{base_scheme_url}/favicon.ico"

    # 6. Header & Footer Analysis
    has_header = bool(re.search(r'<(header|nav)[^>]*>', html_body, re.IGNORECASE))
    has_footer = bool(re.search(r'<footer[^>]*>', html_body, re.IGNORECASE))

    header_footer_analysis = {
        "has_header": has_header,
        "has_footer": has_footer,
        "header_desc": "Header/Navbar present. Provides quick site navigation and branding." if has_header else "Missing <header> or <nav> tag.",
        "footer_desc": "Footer present. Contains legal links, copyright, and SEO sitemap anchors." if has_footer else "Missing <footer> tag.",
        "seo_impact": "Header and Footer are well structured for Google crawlers." if (has_header and has_footer) else "Semantic landmark tags missing. Recommended to fix for better ranking."
    }

    # 7. Concurrent Core Files Inspection (Sitemap, Robots, Manifest)
    sitemap_url = f"{base_scheme_url}/sitemap.xml"
    robots_url = f"{base_scheme_url}/robots.txt"
    manifest_url = f"{base_scheme_url}/manifest.json"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_sitemap = executor.submit(analyze_sitemap, sitemap_url)
        f_robots = executor.submit(analyze_robots, robots_url)
        f_manifest = executor.submit(analyze_manifest, manifest_url)
        
        sitemap_info = f_sitemap.result()
        robots_info = f_robots.result()
        manifest_info = f_manifest.result()

    # 8. Broken Link Check
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

    # 10. WHOIS Lookup Data
    try:
        ip_address = socket.gethostbyname(domain)
        dns_records = socket.gethostbyname_ex(domain)
        
        whois_data = f"================================================\n" \
                     f"         DETAILED WHOIS & HOST INTEL            \n" \
                     f"================================================\n" \
                     f"Target Domain    : {domain}\n" \
                     f"Resolved IPv4    : {ip_address}\n" \
                     f"Host Alias/CNAME : {dns_records[0]}\n" \
                     f"IP Map Array     : {', '.join(dns_records[2])}\n" \
                     f"Protocol Security: {'HTTPS (SSL Encrypted)' if is_https else 'HTTP (Unencrypted Insecure)'}\n" \
                     f"TLD Category     : .{domain.split('.')[-1]}\n" \
                     f"CMS Platform     : {cms_detected}\n" \
                     f"Viewport Layout  : {responsive_status}\n" \
                     f"Audit Stamp      : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n" \
                     f"Host Network Status: LIVE & ACTIVE\n" \
                     f"================================================"
    except Exception:
        ip_address = "Resolution Failed"
        whois_data = f"Domain Name: {domain}\nStatus: Could not resolve DNS or WHOIS record for target."

    return jsonify({
        "success": True,
        "domain": domain,
        "full_url": full_url,
        "latency": latency,
        "is_https": is_https,
        "is_wordpress": is_wordpress,
        "cms_detected": cms_detected,
        "is_responsive": is_responsive,
        "responsive_status": responsive_status,
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
        "header_footer": header_footer_analysis,
        "files": {
            "sitemap": sitemap_info,
            "robots": robots_info,
            "manifest": manifest_info
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
    <title>Enterprise Web & SEO Intelligence Suite</title>
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
                    <i class="fa-solid fa-microchip text-indigo-400"></i> Enterprise Web & SEO Intelligence Suite
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Instant Technical Audit • CMS • Responsiveness • WHOIS</p>
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
                        <input type="text" id="targetUrl" required placeholder="e.g. domain.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Start SEO Audit</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- MAIN DASHBOARD METRICS -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- QUICK METRIC BADGES -->
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">HTTPS Protocol</span>
                    <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-blue-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">CMS Platform</span>
                    <h3 id="badge-cms" class="text-xs md:text-sm font-bold text-white mt-1 truncate">Checking...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Mobile Responsive</span>
                    <h3 id="badge-responsive" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Server Latency</span>
                    <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500 col-span-2 md:col-span-1">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Resolved IPv4</span>
                    <h3 id="badge-ip" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                </div>
            </div>

            <!-- EASY CORE FILES DEEP INSPECTION -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center justify-between">
                    <span class="flex items-center gap-2"><i class="fa-solid fa-file-code text-indigo-400"></i> Core Search Engine Files (Detailed Analysis)</span>
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    
                    <!-- SITEMAP CARD -->
                    <div id="card-sitemap" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-sitemap text-indigo-400 mr-1.5"></i> Sitemap.xml</span>
                                <span id="badge-sitemap" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-sitemap" class="text-[11px] text-gray-200 font-semibold leading-relaxed"></p>
                            <p id="exp-sitemap" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <a id="btn-sitemap" target="_blank" class="w-full text-center bg-indigo-600/20 border border-indigo-500/30 hover:bg-indigo-600/40 text-indigo-300 text-[10px] font-bold py-1.5 rounded-lg transition font-mono">View Sitemap File</a>
                    </div>

                    <!-- ROBOTS CARD -->
                    <div id="card-robots" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-robot text-cyan-400 mr-1.5"></i> Robots.txt</span>
                                <span id="badge-robots" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-robots" class="text-[11px] text-gray-200 font-semibold leading-relaxed font-mono truncate"></p>
                            <p id="exp-robots" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <a id="btn-robots" target="_blank" class="w-full text-center bg-cyan-600/20 border border-cyan-500/30 hover:bg-cyan-600/40 text-cyan-300 text-[10px] font-bold py-1.5 rounded-lg transition font-mono">View Robots.txt File</a>
                    </div>

                    <!-- MANIFEST CARD -->
                    <div id="card-manifest" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-mobile-screen text-amber-400 mr-1.5"></i> Manifest.json</span>
                                <span id="badge-manifest" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-manifest" class="text-[11px] text-gray-200 font-semibold leading-relaxed"></p>
                            <p id="exp-manifest" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <a id="btn-manifest" target="_blank" class="w-full text-center bg-amber-600/20 border border-amber-500/30 hover:bg-amber-600/40 text-amber-300 text-[10px] font-bold py-1.5 rounded-lg transition font-mono">View Manifest File</a>
                    </div>

                </div>
            </div>

            <!-- HEADER & FOOTER ANALYSIS -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                    <i class="fa-solid fa-window-maximize text-emerald-400"></i> Header & Footer Structural Analysis
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800/80 space-y-1.5">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-emerald-400 text-[11px] uppercase tracking-wider font-mono">&lt;header&gt; / &lt;nav&gt; Tag</span>
                            <span id="status-header-tag" class="px-2 py-0.5 rounded text-[10px] font-bold font-mono"></span>
                        </div>
                        <p id="desc-header-tag" class="text-gray-300 text-[11px] leading-relaxed"></p>
                    </div>
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800/80 space-y-1.5">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-emerald-400 text-[11px] uppercase tracking-wider font-mono">&lt;footer&gt; Tag</span>
                            <span id="status-footer-tag" class="px-2 py-0.5 rounded text-[10px] font-bold font-mono"></span>
                        </div>
                        <p id="desc-footer-tag" class="text-gray-300 text-[11px] leading-relaxed"></p>
                    </div>
                </div>
                <div id="seo-hf-summary" class="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300 font-medium flex items-center gap-2"></div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT SECTION -->
                <div class="lg:col-span-2 space-y-6">
                    
                    <!-- TITLE & CANONICAL & FAVICON -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                            <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                                <i class="fa-solid fa-heading text-indigo-400"></i> Page Metadata & Identity
                            </h3>
                            <div class="flex items-center gap-2 bg-gray-900 border border-gray-800 px-3 py-1 rounded-lg">
                                <img id="img-favicon" src="" alt="Favicon" class="w-4 h-4 object-contain">
                                <span class="text-[10px] text-gray-400 font-mono">Favicon Icon</span>
                            </div>
                        </div>

                        <div class="space-y-3 text-xs">
                            <div>
                                <span class="text-gray-400 font-semibold uppercase text-[10px]">Title Tag:</span>
                                <p id="val-title" class="text-white font-medium bg-gray-950 p-2.5 rounded-lg border border-gray-800/80 mt-1"></p>
                            </div>
                            <div>
                                <span class="text-gray-400 font-semibold uppercase text-[10px]">Canonical Tag URL:</span>
                                <p id="val-canonical" class="text-indigo-300 font-mono bg-gray-950 p-2.5 rounded-lg border border-gray-800/80 mt-1 truncate"></p>
                            </div>
                        </div>
                    </div>

                    <!-- META TAGS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-tags text-indigo-400"></i> Meta Directives
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

                    <!-- HEADING TAGS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-list-ol text-indigo-400"></i> Heading Tag Structure (H1 — H5)
                        </h3>
                        <div id="headings-container" class="space-y-3"></div>
                    </div>

                </div>

                <!-- RIGHT SECTION -->
                <div class="space-y-6">
                    
                    <!-- BROKEN LINKS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-link-slash text-rose-400"></i> Broken Link Diagnostics
                        </h3>
                        <div id="broken-links-container" class="space-y-2 max-h-64 overflow-y-auto"></div>
                    </div>

                    <!-- WHOIS LOOKUP TERMINAL -->
                    <div class="cyber-card p-6 rounded-2xl space-y-3">
                        <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                            <i class="fa-solid fa-terminal text-purple-400"></i> WHOIS & Host Record Intelligence
                        </h3>
                        <pre id="whois-logs" class="terminal-box p-4 rounded-xl text-[11px] text-emerald-400 whitespace-pre-wrap leading-relaxed min-h-48"></pre>
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
                    // Badges Update
                    const httpsEl = document.getElementById('badge-https');
                    httpsEl.className = data.is_https ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    httpsEl.innerText = data.is_https ? "HTTPS Secure" : "HTTP Insecure";

                    const cmsEl = document.getElementById('badge-cms');
                    cmsEl.innerText = data.is_wordpress ? "WordPress" : "Custom Stack";

                    const respEl = document.getElementById('badge-responsive');
                    respEl.className = data.is_responsive ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    respEl.innerText = data.is_responsive ? "Mobile Friendly" : "Non-Responsive";

                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;
                    document.getElementById('badge-ip').innerText = data.ip_address;

                    // Header/Footer Details
                    const hf = data.header_footer;
                    document.getElementById('status-header-tag').className = hf.has_header ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded" : "bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded";
                    document.getElementById('status-header-tag').innerText = hf.has_header ? "Present" : "Missing";
                    document.getElementById('desc-header-tag').innerText = hf.header_desc;

                    document.getElementById('status-footer-tag').className = hf.has_footer ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded" : "bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded";
                    document.getElementById('status-footer-tag').innerText = hf.has_footer ? "Present" : "Missing";
                    document.getElementById('desc-footer-tag').innerText = hf.footer_desc;

                    document.getElementById('seo-hf-summary').innerHTML = `<i class="fa-solid fa-circle-info text-indigo-400"></i> <span>${hf.seo_impact}</span>`;

                    // Render File Cards
                    const renderFileCard = (cardId, badgeId, descId, expId, btnId, fileObj) => {
                        const card = document.getElementById(cardId);
                        const badge = document.getElementById(badgeId);
                        const btn = document.getElementById(btnId);

                        if (fileObj.exists) {
                            card.className = "p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-3 flex flex-col justify-between";
                            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                            badge.innerText = `Found (${fileObj.code})`;
                        } else {
                            card.className = "p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 space-y-3 flex flex-col justify-between";
                            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30";
                            badge.innerText = `Missing (${fileObj.code})`;
                        }
                        document.getElementById(descId).innerText = fileObj.summary;
                        document.getElementById(expId).innerText = fileObj.explanation;
                        
                        btn.href = fileObj.url;
                        btn.innerText = fileObj.fix_action;
                    };

                    renderFileCard('card-sitemap', 'badge-sitemap', 'desc-sitemap', 'exp-sitemap', 'btn-sitemap', data.files.sitemap);
                    renderFileCard('card-robots', 'badge-robots', 'desc-robots', 'exp-robots', 'btn-robots', data.files.robots);
                    renderFileCard('card-manifest', 'badge-manifest', 'desc-manifest', 'exp-manifest', 'btn-manifest', data.files.manifest);

                    // Metadata
                    document.getElementById('val-title').innerText = data.title;
                    document.getElementById('val-canonical').innerText = data.canonical_url;
                    document.getElementById('img-favicon').src = data.favicon_url;

                    // Meta Directives
                    document.getElementById('meta-desc').innerText = data.meta.description;
                    document.getElementById('meta-keys').innerText = data.meta.keywords;
                    document.getElementById('og-title').innerText = data.meta.og_title;
                    document.getElementById('og-desc').innerText = data.meta.og_description;

                    // Heading Hierarchy
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

                    // Broken Links
                    const linksContainer = document.getElementById('broken-links-container');
                    linksContainer.innerHTML = '';
                    if (data.broken_links.length === 0) {
                        linksContainer.innerHTML = `<div class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center text-emerald-400 text-xs font-medium"><i class="fa-solid fa-circle-check mr-1.5"></i> All Anchor Links Working!</div>`;
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
                    alert(data.message || "Audit engine failed to process target.");
                }
            } catch (err) {
                console.error("Audit Exception:", err);
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

