import os
import json
import time
import socket
import ssl
import re
import urllib.parse
import concurrent.futures
from collections import Counter
from datetime import datetime
import requests
from flask import Blueprint, render_template_string, request, jsonify, session

# =========================================================================
# FLASK BLUEPRINT DEFINITION
# =========================================================================
script40_bp = Blueprint('script40', __name__)

# =========================================================================
# HELPER PARSING & CLEANING FUNCTIONS
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

def extract_keywords_density(text, top_n=8):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stop_words = {'the', 'and', 'for', 'that', 'with', 'this', 'you', 'from', 'have', 'are', 'not', 'was', 'were', 'your', 'with', 'site', 'about', 'more', 'page', 'home', 'will', 'can', 'all', 'has'}
    filtered_words = [w for w in words if w not in stop_words]
    total_words = len(filtered_words) or 1
    counts = Counter(filtered_words).most_common(top_n)
    
    result = []
    for word, count in counts:
        density = round((count / total_words) * 100, 2)
        result.append({"word": word, "count": count, "density": density})
    return result

# =========================================================================
# ADVANCED FILE & SERVICE ANALYZERS
# =========================================================================
def analyze_sitemap(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/1.0"})
        if res.status_code == 200 and ("xml" in res.headers.get("Content-Type", "").lower() or "<urlset" in res.text or "<sitemapindex" in res.text):
            urls = re.findall(r'<loc>(.*?)</loc>', res.text, re.IGNORECASE)
            url_count = len(urls)
            return {
                "exists": True,
                "code": 200,
                "url_count": url_count,
                "url": url,
                "summary": f"Sitemap XML contains {url_count} indexed URL entries.",
                "explanation": "Search engines like Google & Bing use this to index all pages.",
                "fix_action": "Sitemap is properly configured."
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url_count": 0,
            "url": url,
            "summary": "Sitemap XML missing or returning non-200 code.",
            "explanation": "Search engine bots may miss deeply nested pages.",
            "fix_action": "Generate XML Sitemap via Yoast SEO / RankMath or custom generator."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url_count": 0,
            "url": url,
            "summary": "Sitemap request timed out.",
            "explanation": "Server failed to respond to sitemap lookup.",
            "fix_action": "Check server configuration and sitemap route accessibility."
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/1.0"})
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            explanation = "CRITICAL SEO RISK: Site blocks all search crawlers!" if is_blocking_all else "Good: Crawlers are allowed to index public pages."
            return {
                "exists": True,
                "code": 200,
                "url": url,
                "is_blocking_all": is_blocking_all,
                "summary": content[:250] + ("..." if len(content) > 250 else ""),
                "explanation": explanation,
                "fix_action": "Modify Disallow: / directive in robots.txt if indexing is blocked." if is_blocking_all else "Robots.txt is active."
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt missing or unreadable.",
            "explanation": "Search engines scan everything, but admin paths remain unprotected.",
            "fix_action": "Create a robots.txt file in site root path."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt endpoint timeout.",
            "explanation": "Unable to verify crawler instructions.",
            "fix_action": "Verify server routing for /robots.txt."
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/1.0"})
        if res.status_code == 200:
            try:
                data = res.json()
                app_name = data.get("name") or data.get("short_name") or "Web Application"
                return {
                    "exists": True,
                    "code": 200,
                    "url": url,
                    "summary": f"Valid Web App Manifest detected ('{app_name}').",
                    "explanation": "Supports Progressive Web App (PWA) installation.",
                    "fix_action": "Manifest file is healthy."
                }
            except Exception:
                pass
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "summary": "Manifest.json missing or invalid JSON.",
            "explanation": "Website will run without mobile PWA installation support.",
            "fix_action": "Add web app manifest.json for PWA mobile experience."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "summary": "Manifest.json request timed out.",
            "explanation": "Could not inspect web manifest.",
            "fix_action": "Check manifest endpoint."
        }

def fetch_ip_geolocation(ip_address):
    if not ip_address or ip_address == "Resolution Failed":
        return {"country": "Unknown", "region": "Unknown", "city": "Unknown", "isp": "Unknown"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,isp", timeout=3)
        if r.status_code == 200 and r.json().get('status') == 'success':
            data = r.json()
            return {
                "country": data.get("country", "Unknown"),
                "region": data.get("regionName", "Unknown"),
                "city": data.get("city", "Unknown"),
                "isp": data.get("isp", "Unknown")
            }
    except Exception:
        pass
    return {"country": "Global Cloud", "region": "Edge Node", "city": "Datacenter", "isp": "CDNs Host"}

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
        return jsonify({"success": False, "message": "Target URL input cannot be empty."})

    domain, full_url, base_scheme_url = clean_domain_input(target_raw)
    
    start_time = time.time()
    try:
        session_req = requests.Session()
        res = session_req.get(full_url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OrbitEdgeMedia-Auditor/4.0"}, allow_redirects=True)
        latency = round((time.time() - start_time) * 1000, 2)
        html_body = res.text
        response_headers = dict(res.headers)
        
        # Track Redirect Chains
        redirect_chain = []
        if res.history:
            for resp in res.history:
                redirect_chain.append({"status": resp.status_code, "url": resp.url})
            redirect_chain.append({"status": res.status_code, "url": res.url})
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Target endpoint unreachable or connection timed out: {str(e)}"
        })

    # 1. CMS Detection
    html_lower = html_body.lower()
    is_wordpress = any(i in html_lower for i in ["wp-content", "wp-includes", "wp-json", "wordpress", "elementor", "yoast"])
    is_shopify = "shopify" in html_lower or "cdn.shopify.com" in html_lower
    is_wix = "wix.com" in html_lower
    cms_detected = "WordPress CMS" if is_wordpress else ("Shopify E-Commerce" if is_shopify else ("Wix Builder" if is_wix else "Custom Stack"))

    # 2. Responsiveness & Viewport
    has_viewport = bool(re.search(r'<meta\s+name=["\']viewport["\']', html_body, re.IGNORECASE))
    is_responsive = has_viewport or ("@media" in html_lower)
    responsive_status = "Responsive (Mobile & Desktop Ready)" if is_responsive else "Non-Responsive (Viewport Meta Missing)"

    # 3. Metadata & OpenGraph
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_body, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else "No Title Tag Found"

    meta_description = extract_meta_tag(html_body, "description") or "Not Specified"
    meta_keywords = extract_meta_tag(html_body, "keywords") or "Not Specified"
    og_title = extract_meta_tag(html_body, "og:title") or "Not Specified"
    og_description = extract_meta_tag(html_body, "og:description") or "Not Specified"
    og_image = extract_meta_tag(html_body, "og:image") or "Not Specified"
    twitter_card = extract_meta_tag(html_body, "twitter:card") or "Not Specified"

    # 4. Heading Tag Hierarchy
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

    # 6. Structural Landmark Tags
    has_header = bool(re.search(r'<(header|nav)[^>]*>', html_body, re.IGNORECASE))
    has_footer = bool(re.search(r'<footer[^>]*>', html_body, re.IGNORECASE))

    # 7. International SEO
    html_lang_match = re.search(r'<html[^>]*\s+lang=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    html_lang = html_lang_match.group(1) if html_lang_match else "Not Specified"
    hreflang_matches = re.findall(r'<link\s+[^>]*hreflang=["\']([^"\']+)["\']', html_body, re.IGNORECASE)

    # 8. Framesets & Iframes
    iframes_found = len(re.findall(r'<iframe[^>]*>', html_body, re.IGNORECASE))
    framesets_found = len(re.findall(r'<frameset[^>]*>', html_body, re.IGNORECASE))

    # 9. Page Quality & Payload Analysis
    raw_text = re.sub(r'<[^>]+>', ' ', html_body)
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    word_count = len(raw_text.split())
    html_size_kb = round(len(html_body.encode('utf-8')) / 1024, 2)
    text_size_kb = round(len(raw_text.encode('utf-8')) / 1024, 2)
    text_ratio = round((text_size_kb / (html_size_kb or 1)) * 100, 2)

    # Images Alt Tag Audit
    img_tags = re.findall(r'<img\s+[^>]*>', html_body, re.IGNORECASE)
    images_missing_alt = 0
    for img in img_tags:
        if not re.search(r'alt=["\'][^"\']+["\']', img, re.IGNORECASE):
            images_missing_alt += 1

    # Assets Count
    css_files = len(re.findall(r'<link\s+[^>]*rel=["\']stylesheet["\']', html_body, re.IGNORECASE))
    js_files = len(re.findall(r'<script\s+[^>]*src=["\']', html_body, re.IGNORECASE))

    # 10. Links Analysis & Backlinks Discovery
    all_anchors = re.findall(r'<a\s+([^>]+)>', html_body, re.IGNORECASE)
    internal_links = 0
    external_links = 0
    nofollow_links = 0
    external_domains = set()

    for anchor_attrs in all_anchors:
        href_match = re.search(r'href=["\']([^"\']*)["\']', anchor_attrs, re.IGNORECASE)
        if href_match:
            href = href_match.group(1).strip()
            if href.startswith('http://') or href.startswith('https://'):
                parsed_href = urllib.parse.urlparse(href)
                if parsed_href.netloc and domain not in parsed_href.netloc:
                    external_links += 1
                    external_domains.add(parsed_href.netloc)
                else:
                    internal_links += 1
            elif href.startswith('/') or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                internal_links += 1

        if 'rel="nofollow"' in anchor_attrs.lower() or "rel='nofollow'" in anchor_attrs.lower():
            nofollow_links += 1

    # Social Profiles Discovery
    social_platforms = ['facebook.com', 'twitter.com', 'x.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'pinterest.com']
    social_links_found = [d for d in external_domains if any(sp in d for sp in social_platforms)]

    # 11. Keyword Density Extraction
    keyword_density = extract_keywords_density(raw_text)

    # 12. Concurrent Core Files Inspection
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

    # 13. Broken Link Check (Sampled)
    found_hrefs = list(set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html_body)))[:6]
    broken_links = []
    
    def check_link(link):
        try:
            r = requests.head(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code >= 400:
                broken_links.append({"url": link, "status": r.status_code})
        except Exception:
            broken_links.append({"url": link, "status": "Failed/Timeout"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(check_link, found_hrefs)

    # 14. Server & Security Inspection
    is_https = full_url.startswith("https://")
    server_header = response_headers.get('Server', 'Hidden / Protected')
    content_encoding = response_headers.get('Content-Encoding', 'Uncompressed')
    hsts_header = 'Strict-Transport-Security' in response_headers
    x_frame_options = response_headers.get('X-Frame-Options', 'Not Configured')

    # 15. Geolocation & Network WHOIS
    try:
        ip_address = socket.gethostbyname(domain)
    except Exception:
        ip_address = "Resolution Failed"

    geo_data = fetch_ip_geolocation(ip_address)

    # Calculate Overall Health Score (0 - 100)
    score = 100
    if not is_https: score -= 15
    if not is_responsive: score -= 15
    if page_title == "No Title Tag Found": score -= 10
    if meta_description == "Not Specified": score -= 10
    if not sitemap_info["exists"]: score -= 10
    if not robots_info["exists"]: score -= 10
    if images_missing_alt > 0: score -= 10
    if headings.get("H1", {}).get("count", 0) == 0: score -= 10
    score = max(score, 20)

    return jsonify({
        "success": True,
        "score": score,
        "domain": domain,
        "full_url": full_url,
        "latency": latency,
        "is_https": is_https,
        "cms_detected": cms_detected,
        "is_responsive": is_responsive,
        "responsive_status": responsive_status,
        "ip_address": ip_address,
        "geo_data": geo_data,
        "server_info": {
            "server": server_header,
            "encoding": content_encoding,
            "hsts": hsts_header,
            "x_frame": x_frame_options
        },
        "title": page_title,
        "canonical_url": canonical_url,
        "favicon_url": favicon_url,
        "international_seo": {
            "lang": html_lang,
            "hreflang_count": len(hreflang_matches)
        },
        "meta": {
            "description": meta_description,
            "keywords": meta_keywords,
            "og_title": og_title,
            "og_description": og_description,
            "og_image": og_image,
            "twitter_card": twitter_card
        },
        "headings": headings,
        "header_footer": {
            "has_header": has_header,
            "has_footer": has_footer
        },
        "page_quality": {
            "word_count": word_count,
            "html_size_kb": html_size_kb,
            "text_size_kb": text_size_kb,
            "text_ratio": text_ratio,
            "total_images": len(img_tags),
            "missing_alt_images": images_missing_alt,
            "css_files": css_files,
            "js_files": js_files,
            "iframes_found": iframes_found,
            "framesets_found": framesets_found
        },
        "links": {
            "internal": internal_links,
            "external": external_links,
            "nofollow": nofollow_links,
            "external_domains_count": len(external_domains),
            "social_links": social_links_found
        },
        "keyword_density": keyword_density,
        "redirect_chain": redirect_chain,
        "files": {
            "sitemap": sitemap_info,
            "robots": robots_info,
            "manifest": manifest_info
        },
        "broken_links": broken_links,
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

# =========================================================================
# ULTRA MODERN NEON CYBERPUNK UI LAYOUT WITH CHART.JS & PDF EXPORT
# =========================================================================
UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdgeMedia Site Audit Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
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

    <div class="max-w-[1500px] mx-auto p-4 md:p-8 space-y-6" id="reportable-content">
        
        <!-- BRANDING HEADER BANNER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-3xl font-bold heading-font tracking-wide text-white flex items-center gap-3">
                    <i class="fa-solid fa-chart-line text-indigo-400"></i> OrbitEdgeMedia Site Audit
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Enterprise Technical SEO • Backlinks • Performance Audit Engine</p>
            </div>
            <div class="flex items-center gap-3">
                <button id="pdfBtn" onclick="exportPDFReport()" class="hidden bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2.5 rounded-xl font-bold transition shadow-lg flex items-center gap-2 cursor-pointer">
                    <i class="fa-solid fa-file-pdf"></i> Export PDF Report
                </button>
                <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                    <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
                </a>
            </div>
        </div>

        <!-- TARGET INPUT PANEL -->
        <div class="cyber-card p-6 rounded-2xl glow-indigo" id="input-panel">
            <form id="auditForm" onsubmit="triggerScanSequence(event)" class="space-y-3">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Target Domain / Web Address</label>
                <div class="flex flex-col sm:flex-row gap-3">
                    <div class="relative flex-1">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-globe text-sm"></i></span>
                        <input type="text" id="targetUrl" required placeholder="e.g. orbitedgemedia.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Start Audit Engine</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- MAIN DASHBOARD METRICS -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- OVERALL HEALTH & KEY STATS -->
            <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <!-- CHART: HEALTH SCORE -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                    <h3 class="text-xs uppercase font-bold text-gray-400 tracking-wider mb-2">SEO Health Score</h3>
                    <div class="w-40 h-40 relative flex items-center justify-center">
                        <canvas id="healthScoreChart"></canvas>
                        <span id="scoreText" class="absolute text-2xl font-bold font-mono text-white">0%</span>
                    </div>
                    <p id="scoreGrade" class="text-xs text-indigo-400 font-bold mt-2 font-mono"></p>
                </div>

                <!-- QUICK METRIC BADGES -->
                <div class="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">HTTPS Protocol</span>
                        <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">SSL/TLS Security</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-blue-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">CMS Stack</span>
                        <h3 id="badge-cms" class="text-xs md:text-sm font-bold text-white mt-1 truncate">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Architecture Tech</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Responsiveness</span>
                        <h3 id="badge-responsive" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Mobile Viewport</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Latency Speed</span>
                        <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Server Response Time</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Server IP & Geolocation</span>
                        <h3 id="badge-geo" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                        <p id="badge-location" class="text-[9px] text-gray-500 mt-2">Country Location</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-pink-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">International SEO</span>
                        <h3 id="badge-lang" class="text-xs md:text-sm font-bold text-white mt-1">HTML Lang: -</h3>
                        <p id="badge-hreflang" class="text-[9px] text-gray-500 mt-2">0 Hreflangs</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-amber-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Word Count</span>
                        <h3 id="badge-words" class="text-xs md:text-sm font-bold text-amber-400 font-mono mt-1">0 Words</h3>
                        <p id="badge-ratio" class="text-[9px] text-gray-500 mt-2">Text-to-HTML Ratio: 0%</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-teal-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Assets & Size</span>
                        <h3 id="badge-assets" class="text-xs md:text-sm font-bold text-teal-300 font-mono mt-1">0 KB</h3>
                        <p id="badge-assets-count" class="text-[9px] text-gray-500 mt-2">0 CSS / 0 JS Files</p>
                    </div>
                </div>
            </div>

            <!-- VISUAL CHARTS ROW -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- CHART 1: LINKS BREAKDOWN -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Links Structure (Internal vs External)</h3>
                    <div class="w-full max-w-[280px] h-48">
                        <canvas id="linksChart"></canvas>
                    </div>
                </div>

                <!-- CHART 2: KEYWORD DENSITY -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Top Keyword Frequencies</h3>
                    <div class="w-full max-w-[320px] h-48">
                        <canvas id="keywordsChart"></canvas>
                    </div>
                </div>

                <!-- CHART 3: ASSET & PAGE WEIGHT -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center col-span-1 md:col-span-2 lg:col-span-1">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Page Payload Composition</h3>
                    <div class="w-full max-w-[280px] h-48">
                        <canvas id="assetsChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- EASY CORE FILES DEEP INSPECTION -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center justify-between">
                    <span class="flex items-center gap-2"><i class="fa-solid fa-file-code text-indigo-400"></i> Search Engine Core Files & Directives</span>
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

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT COLUMN -->
                <div class="lg:col-span-2 space-y-6">
                    
                    <!-- TITLE & CANONICAL & FAVICON -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                            <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                                <i class="fa-solid fa-heading text-indigo-400"></i> Page Title & Identity Directive
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

                    <!-- META TAGS & SOCIAL METADATA -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-share-nodes text-indigo-400"></i> Meta Directives & OpenGraph Social Media
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

                    <!-- HEADING TAGS HIERARCHY -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-list-ol text-indigo-400"></i> Heading Structure (H1 — H5)
                        </h3>
                        <div id="headings-container" class="space-y-3"></div>
                    </div>

                </div>

                <!-- RIGHT COLUMN -->
                <div class="space-y-6">
                    
                    <!-- SOCIAL MEDIA PROFILES DETECTED -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-hashtag text-pink-400"></i> Linked Social Profiles
                        </h3>
                        <div id="social-container" class="space-y-2"></div>
                    </div>

                    <!-- BROKEN LINKS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-link-slash text-rose-400"></i> Link Health Diagnostics
                        </h3>
                        <div id="broken-links-container" class="space-y-2 max-h-64 overflow-y-auto"></div>
                    </div>

                    <!-- REDIRECT TRAIL -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-route text-amber-400"></i> HTTP Redirect Chain Tracker
                        </h3>
                        <div id="redirects-container" class="space-y-2 font-mono text-xs"></div>
                    </div>

                    <!-- RECOMMENDED FIX ACTIONS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4 border-l-4 border-l-emerald-500">
                        <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                            <i class="fa-solid fa-wrench text-emerald-400"></i> Automated Actionable Fixes
                        </h3>
                        <div id="fixes-container" class="space-y-3 text-xs"></div>
                    </div>

                </div>
            </div>

            <!-- FOOTER STAMP -->
            <div class="text-center text-xs text-gray-500 font-mono py-4 border-t border-gray-800">
                OrbitEdgeMedia Site Audit Engine • Report Stamp: <span id="report-timestamp"></span>
            </div>

        </div>
    </div>

    <script>
        let healthChart, linksChart, keywordsChart, assetsChart;

        async function triggerScanSequence(e) {
            e.preventDefault();
            const target = document.getElementById('targetUrl').value;
            const submitBtn = document.getElementById('submitBtn');
            const spinIcon = document.getElementById('spinIcon');
            const dashboard = document.getElementById('analyticsDashboard');
            const pdfBtn = document.getElementById('pdfBtn');

            submitBtn.disabled = true;
            spinIcon.classList.remove('hidden');

            let fd = new FormData();
            fd.append('target', target);

            try {
                let response = await fetch('/script40/api/audit', { method: 'POST', body: fd });
                let data = await response.json();

                if (data.success) {
                    // Update Health Score Chart
                    renderHealthChart(data.score);

                    // Badges Update
                    const httpsEl = document.getElementById('badge-https');
                    httpsEl.className = data.is_https ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    httpsEl.innerText = data.is_https ? "HTTPS Secure" : "HTTP Insecure";

                    document.getElementById('badge-cms').innerText = data.cms_detected;

                    const respEl = document.getElementById('badge-responsive');
                    respEl.className = data.is_responsive ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    respEl.innerText = data.is_responsive ? "Mobile Friendly" : "Non-Responsive";

                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;
                    document.getElementById('badge-geo').innerText = data.ip_address;
                    document.getElementById('badge-location').innerText = `${data.geo_data.city}, ${data.geo_data.country} (${data.geo_data.isp})`;

                    document.getElementById('badge-lang').innerText = `HTML Lang: ${data.international_seo.lang}`;
                    document.getElementById('badge-hreflang').innerText = `${data.international_seo.hreflang_count} Hreflang Tags`;

                    document.getElementById('badge-words').innerText = `${data.page_quality.word_count} Words`;
                    document.getElementById('badge-ratio').innerText = `Text Ratio: ${data.page_quality.text_ratio}%`;

                    document.getElementById('badge-assets').innerText = `${data.page_quality.html_size_kb} KB Page`;
                    document.getElementById('badge-assets-count').innerText = `${data.page_quality.css_files} CSS / ${data.page_quality.js_files} JS Files`;

                    // Render Charts
                    renderLinksChart(data.links.internal, data.links.external, data.links.nofollow);
                    renderKeywordsChart(data.keyword_density);
                    renderAssetsChart(data.page_quality);

                    // Render Core File Cards
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

                    // Social Links
                    const socialContainer = document.getElementById('social-container');
                    socialContainer.innerHTML = '';
                    if (data.links.social_links.length === 0) {
                        socialContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No social media links detected in HTML anchor tags.</p>';
                    } else {
                        data.links.social_links.forEach(domain => {
                            socialContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg text-xs font-mono text-pink-400 flex items-center gap-2">
                                    <i class="fa-solid fa-share-nodes"></i> ${domain}
                                </div>
                            `;
                        });
                    }

                    // Broken Links
                    const linksContainer = document.getElementById('broken-links-container');
                    linksContainer.innerHTML = '';
                    if (data.broken_links.length === 0) {
                        linksContainer.innerHTML = `<div class="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center text-emerald-400 text-xs font-medium"><i class="fa-solid fa-circle-check mr-1.5"></i> All Analyzed Anchor Links Active!</div>`;
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

                    // Redirect Chain
                    const redirectsContainer = document.getElementById('redirects-container');
                    redirectsContainer.innerHTML = '';
                    if (!data.redirect_chain || data.redirect_chain.length <= 1) {
                        redirectsContainer.innerHTML = '<p class="text-xs text-emerald-400">Direct loading path without redirects (HTTP 200 OK).</p>';
                    } else {
                        data.redirect_chain.forEach((step, idx) => {
                            redirectsContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-amber-500/30 rounded-lg flex items-center justify-between">
                                    <span class="truncate text-[10px] text-gray-300">${idx+1}. ${step.url}</span>
                                    <span class="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded text-[10px] font-bold">${step.status}</span>
                                </div>
                            `;
                        });
                    }

                    // Automated Recommendations
                    renderActionableFixes(data);

                    document.getElementById('report-timestamp').innerText = data.timestamp;

                    // Unhide Dashboard & Show PDF Button
                    dashboard.classList.remove('hidden');
                    pdfBtn.classList.remove('hidden');
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

        function renderFileCard(cardId, badgeId, descId, expId, btnId, fileObj) {
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
        }

        function renderHealthChart(score) {
            const ctx = document.getElementById('healthScoreChart').getContext('2d');
            if (healthChart) healthChart.destroy();

            document.getElementById('scoreText').innerText = `${score}%`;
            document.getElementById('scoreGrade').innerText = score >= 80 ? "Grade: A (Excellent)" : (score >= 60 ? "Grade: B (Moderate)" : "Grade: C (Needs Optimization)");

            healthChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [score, 100 - score],
                        backgroundColor: [score >= 70 ? '#10b981' : '#f59e0b', '#1f2937'],
                        borderWidth: 0
                    }]
                },
                options: {
                    cutout: '80%',
                    plugins: { tooltip: { enabled: false } },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function renderLinksChart(internal, external, nofollow) {
            const ctx = document.getElementById('linksChart').getContext('2d');
            if (linksChart) linksChart.destroy();

            linksChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Internal Links', 'External Links', 'Nofollow Links'],
                    datasets: [{
                        data: [internal, external, nofollow],
                        backgroundColor: ['#6366f1', '#06b6d4', '#f43f5e'],
                        borderWidth: 0
                    }]
                },
                options: {
                    plugins: { legend: { labels: { color: '#9ca3af', font: { size: 10 } } } },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function renderKeywordsChart(keywords) {
            const ctx = document.getElementById('keywordsChart').getContext('2d');
            if (keywordsChart) keywordsChart.destroy();

            const labels = keywords.map(k => k.word);
            const counts = keywords.map(k => k.count);

            keywordsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Count',
                        data: counts,
                        backgroundColor: '#a855f7',
                        borderRadius: 6
                    }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#9ca3af', font: { size: 9 } } },
                        y: { ticks: { color: '#9ca3af', font: { size: 9 } } }
                    },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function renderAssetsChart(quality) {
            const ctx = document.getElementById('assetsChart').getContext('2d');
            if (assetsChart) assetsChart.destroy();

            assetsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['HTML Size (KB)', 'Text Size (KB)', 'CSS Files', 'JS Files'],
                    datasets: [{
                        data: [quality.html_size_kb, quality.text_size_kb, quality.css_files, quality.js_files],
                        backgroundColor: ['#3b82f6', '#10b981', '#eab308', '#ec4899'],
                        borderWidth: 0
                    }]
                },
                options: {
                    plugins: { legend: { labels: { color: '#9ca3af', font: { size: 10 } } } },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function renderActionableFixes(data) {
            const container = document.getElementById('fixes-container');
            container.innerHTML = '';

            const fixes = [];
            if (!data.is_https) fixes.push("🔒 Enable SSL / HTTPS certificate on server to protect user data.");
            if (!data.is_responsive) fixes.push("📱 Add <meta name='viewport' content='width=device-width, initial-scale=1.0'> tag for responsiveness.");
            if (!data.files.sitemap.exists) fixes.push("🗺️ Generate /sitemap.xml and submit it to Google Search Console.");
            if (!data.files.robots.exists) fixes.push("🤖 Create /robots.txt file to instruct web crawlers.");
            if (data.page_quality.missing_alt_images > 0) fixes.push(`🖼️ Add 'alt' attributes to ${data.page_quality.missing_alt_images} image tags for accessibility.`);
            if (data.meta.description === "Not Specified") fixes.push("✍️ Write a unique Meta Description tag (150-160 characters).");

            if (fixes.length === 0) {
                container.innerHTML = '<p class="text-emerald-400 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> No high-priority fixes needed! Site is highly optimized.</p>';
            } else {
                fixes.forEach(fix => {
                    container.innerHTML += `<div class="p-2.5 bg-gray-950 border border-gray-800 rounded-lg text-gray-300 font-mono">${fix}</div>`;
                });
            }
        }

        function exportPDFReport() {
            const element = document.getElementById('reportable-content');
            const inputPanel = document.getElementById('input-panel');
            
            // Temporarily hide input bar for clean PDF export
            inputPanel.style.display = 'none';

            const opt = {
                margin:       0.3,
                filename:     `OrbitEdgeMedia_Site_Audit_${Date.now()}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };

            html2pdf().set(opt).from(element).save().then(() => {
                inputPanel.style.display = 'block';
            });
        }
    </script>
</body>
</html>
"""

