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
                "summary": f"Active Sitemap detected containing {url_count} indexed URL nodes.",
                "seo_impact": "Excellent for SEO. Allows Googlebot & Bingbot to discover, crawl, and index deep links efficiently."
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url_count": 0,
            "summary": "Sitemap XML file not found at default root path.",
            "seo_impact": "High SEO Risk. Search Engines may miss deep pages, delaying indexing for new content."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Unreachable",
            "url_count": 0,
            "summary": "Connection timeout while fetching sitemap.xml.",
            "seo_impact": "Crawlers cannot reach sitemap file automatically."
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            has_sitemap_link = "sitemap:" in content.lower()
            
            seo_verdict = "Blocking all search engines! Site won't index on Google." if is_blocking_all else "SEO Friendly. Robots.txt allows search crawlers to scan allowed routes properly."
            
            return {
                "exists": True,
                "code": 200,
                "is_blocking_all": is_blocking_all,
                "has_sitemap_link": has_sitemap_link,
                "summary": content[:300] + ("..." if len(content) > 300 else ""),
                "seo_impact": seo_verdict
            }
        return {
            "exists": False,
            "code": res.status_code,
            "is_blocking_all": False,
            "has_sitemap_link": False,
            "summary": "Robots.txt file missing or empty.",
            "seo_impact": "Neutral / Mild Risk. Search engines will crawl everything by default, but crawl-budget cannot be managed."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Unreachable",
            "is_blocking_all": False,
            "has_sitemap_link": False,
            "summary": "Connection timeout fetching robots.txt.",
            "seo_impact": "Unable to verify bot crawling directives."
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            try:
                data = res.json()
                app_name = data.get("name") or data.get("short_name") or "Unnamed Web App"
                icons_count = len(data.get("icons", []))
                theme_color = data.get("theme_color", "Default")
                return {
                    "exists": True,
                    "code": 200,
                    "app_name": app_name,
                    "icons_count": icons_count,
                    "theme_color": theme_color,
                    "summary": f"Valid PWA Manifest. Name: '{app_name}', Theme: {theme_color}, Icons: {icons_count}.",
                    "seo_impact": "Great Mobile UX. Enables 'Add to Home Screen' PWA capabilities, boosting mobile engagement & search signals."
                }
            except Exception:
                pass
        return {
            "exists": False,
            "code": res.status_code,
            "summary": "Manifest.json missing or invalid JSON format.",
            "seo_impact": "Standard Web Application mode. Non-PWA structure."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Unreachable",
            "summary": "Unable to retrieve manifest.json.",
            "seo_impact": "No Progressive Web App capabilities configured."
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
            "sample": clean_matches[:3]
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

    # 6. Header & Footer Analysis
    has_header_tag = bool(re.search(r'<(header|nav)[^>]*>', html_body, re.IGNORECASE))
    has_footer_tag = bool(re.search(r'<footer[^>]*>', html_body, re.IGNORECASE))

    header_footer_analysis = {
        "has_header": has_header_tag,
        "has_footer": has_footer_tag,
        "header_desc": "Header/Navigation block detected. Essential for site navigation, branding, and user retention." if has_header_tag else "Missing <header> or <nav> tag. Can harm user navigation experience.",
        "footer_desc": "Footer area detected. Crucial for legal links (Privacy, Terms), copyright, contact info, and sitewide SEO anchors." if has_footer_tag else "Missing <footer> tag. May degrade trust signals for search engines.",
        "seo_impact": "Both Header and Footer are present! Perfect for semantic HTML5 structure and indexing crawlers." if (has_header_tag and has_footer_tag) else "Incomplete HTML5 semantic landmark structure. Add missing landmark tags."
    }

    # 7. Concurrent File Deep Inspection (Sitemap, Robots, Manifest)
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

    # 8. Broken Link Detection (Top 6 On-Page Anchors)
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

    # 10. WHOIS Lookup & Host Intelligence
    try:
        ip_address = socket.gethostbyname(domain)
        dns_records = socket.gethostbyname_ex(domain)
        
        whois_data = f"================================================\n" \
                     f"         DOMAIN INTEL & WHOIS RECORD            \n" \
                     f"================================================\n" \
                     f"Target Domain    : {domain}\n" \
                     f"Resolved IPv4    : {ip_address}\n" \
                     f"Host CNAME Alias : {dns_records[0]}\n" \
                     f"IP Map Array     : {', '.join(dns_records[2])}\n" \
                     f"Protocol Mode    : {'HTTPS (Encrypted TLS)' if is_https else 'HTTP (Unencrypted)'}\n" \
                     f"TLD Classification: .{domain.split('.')[-1]}\n" \
                     f"Audit Stamp      : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n" \
                     f"Status           : RESOLVED & ACTIVE ON NETWORK\n" \
                     f"================================================"
    except Exception:
        ip_address = "Resolution Failed"
        whois_data = f"Domain Name: {domain}\nStatus: Could not resolve DNS record or domain host unreachable."

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
                    <i class="fa-solid fa-microchip text-indigo-400"></i> Enterprise SEO & Deep Web Suite
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Realtime Technical Audit • Deep Content & Infrastructure Inspection</p>
            </div>
            <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
            </a>
        </div>

        <!-- TARGET INPUT PANEL -->
        <div class="cyber-card p-6 rounded-2xl glow-indigo">
            <form id="auditForm" onsubmit="triggerScanSequence(event)" class="space-y-3">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Target Domain / Endpoint URL Address</label>
                <div class="flex flex-col sm:flex-row gap-3">
                    <div class="relative flex-1">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-globe text-sm"></i></span>
                        <input type="text" id="targetUrl" required placeholder="e.g. domain.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Run Full SEO Audit</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- MAIN DASHBOARD METRICS -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- QUICK METRIC BADGES -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">HTTPS Protocol</span>
                    <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Server Latency</span>
                    <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Structure Health</span>
                    <h3 id="badge-structure" class="text-xs md:text-sm font-bold text-emerald-400 mt-1">Analyzing...</h3>
                </div>
                <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500">
                    <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider block">Resolved IPv4</span>
                    <h3 id="badge-ip" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                </div>
            </div>

            <!-- SYSTEM FILES DEEP INSPECTION SECTION -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                    <i class="fa-solid fa-file-code text-indigo-400"></i> Core Search Engine Files & Manifest Analysis
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    
                    <!-- SITEMAP CARD -->
                    <div id="card-sitemap" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-white"><i class="fa-solid fa-sitemap text-indigo-400 mr-1.5"></i> Sitemap.xml</span>
                            <span id="badge-sitemap" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                        </div>
                        <p id="desc-sitemap" class="text-[11px] text-gray-300 leading-relaxed"></p>
                        <p id="seo-sitemap" class="text-[10px] font-medium text-indigo-300 border-t border-gray-800/80 pt-2 mt-1"></p>
                    </div>

                    <!-- ROBOTS CARD -->
                    <div id="card-robots" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-white"><i class="fa-solid fa-robot text-cyan-400 mr-1.5"></i> Robots.txt</span>
                            <span id="badge-robots" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                        </div>
                        <p id="desc-robots" class="text-[11px] text-gray-300 font-mono leading-relaxed truncate"></p>
                        <p id="seo-robots" class="text-[10px] font-medium text-indigo-300 border-t border-gray-800/80 pt-2 mt-1"></p>
                    </div>

                    <!-- MANIFEST CARD -->
                    <div id="card-manifest" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-white"><i class="fa-solid fa-mobile-screen text-amber-400 mr-1.5"></i> Manifest.json</span>
                            <span id="badge-manifest" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                        </div>
                        <p id="desc-manifest" class="text-[11px] text-gray-300 leading-relaxed"></p>
                        <p id="seo-manifest" class="text-[10px] font-medium text-indigo-300 border-t border-gray-800/80 pt-2 mt-1"></p>
                    </div>

                </div>
            </div>

            <!-- HEADER & FOOTER ANALYSIS CARD -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                    <i class="fa-solid fa-window-maximize text-emerald-400"></i> Header & Footer Semantic Layout Analysis
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800/80 space-y-1.5">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-emerald-400 text-[11px] uppercase tracking-wider font-mono">&lt;header&gt; / &lt;nav&gt; Component</span>
                            <span id="status-header-tag" class="px-2 py-0.5 rounded text-[10px] font-bold font-mono"></span>
                        </div>
                        <p id="desc-header-tag" class="text-gray-300 text-[11px] leading-relaxed"></p>
                    </div>
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800/80 space-y-1.5">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-emerald-400 text-[11px] uppercase tracking-wider font-mono">&lt;footer&gt; Component</span>
                            <span id="status-footer-tag" class="px-2 py-0.5 rounded text-[10px] font-bold font-mono"></span>
                        </div>
                        <p id="desc-footer-tag" class="text-gray-300 text-[11px] leading-relaxed"></p>
                    </div>
                </div>
                <div id="seo-hf-summary" class="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300 font-medium flex items-center gap-2"></div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT SECTION (SEO & TAGS) -->
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

                    <!-- META TAGS CARD -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-tags text-indigo-400"></i> Meta Directives & OpenGraph Engine
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
                            <i class="fa-solid fa-list-ol text-indigo-400"></i> Heading Structure Analysis (H1 — H5)
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
                            <i class="fa-solid fa-terminal text-purple-400"></i> Detailed WHOIS & DNS Intelligence
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

                    // Header & Footer Layout Details
                    const hf = data.header_footer;
                    document.getElementById('status-header-tag').className = hf.has_header ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded" : "bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded";
                    document.getElementById('status-header-tag').innerText = hf.has_header ? "Present" : "Missing";
                    document.getElementById('desc-header-tag').innerText = hf.header_desc;

                    document.getElementById('status-footer-tag').className = hf.has_footer ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded" : "bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded";
                    document.getElementById('status-footer-tag').innerText = hf.has_footer ? "Present" : "Missing";
                    document.getElementById('desc-footer-tag').innerText = hf.footer_desc;

                    document.getElementById('seo-hf-summary').innerHTML = `<i class="fa-solid fa-circle-info text-indigo-400"></i> <span>${hf.seo_impact}</span>`;
                    document.getElementById('badge-structure').innerText = (hf.has_header && hf.has_footer) ? "Fully Validated" : "Partial Semantic";

                    // Render File Cards (Sitemap, Robots, Manifest)
                    const renderFileCard = (cardId, badgeId, descId, seoId, fileObj) => {
                        const card = document.getElementById(cardId);
                        const badge = document.getElementById(badgeId);
                        if (fileObj.exists) {
                            card.className = "p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-2";
                            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                            badge.innerText = `Found (${fileObj.code})`;
                        } else {
                            card.className = "p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 space-y-2";
                            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30";
                            badge.innerText = `Missing (${fileObj.code})`;
                        }
                        document.getElementById(descId).innerText = fileObj.summary;
                        document.getElementById(seoId).innerText = fileObj.seo_impact;
                    };

                    renderFileCard('card-sitemap', 'badge-sitemap', 'desc-sitemap', 'seo-sitemap', data.files.sitemap);
                    renderFileCard('card-robots', 'badge-robots', 'desc-robots', 'seo-robots', data.files.robots);
                    renderFileCard('card-manifest', 'badge-manifest', 'desc-manifest', 'seo-manifest', data.files.manifest);

                    // Metadata
                    document.getElementById('val-title').innerText = data.title;
                    document.getElementById('val-canonical').innerText = data.canonical_url;
                    document.getElementById('img-favicon').src = data.favicon_url;

                    // Meta Directives
                    document.getElementById('meta-desc').innerText = data.meta.description;
                    document.getElementById('meta-keys').innerText = data.meta.keywords;
                    document.getElementById('og-title').innerText = data.meta.og_title;
                    document.getElementById('og-desc').innerText = data.meta.og_description;

                    // Heading Hierarchy Mapping
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
                        linksContainer.innerHTML = `<div class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center text-emerald-400 text-xs font-medium"><i class="fa-solid fa-circle-check mr-1.5"></i> All Anchor Links Operational!</div>`;
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

