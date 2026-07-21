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
from bs4 import BeautifulSoup
from flask import Blueprint, render_template_string, request, jsonify, session

# =========================================================================
# FLASK BLUEPRINT DEFINITION
# =========================================================================
script40_bp = Blueprint('script40', __name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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

def extract_keywords_density(text, top_n=10):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stop_words = {'the', 'and', 'for', 'that', 'with', 'this', 'you', 'from', 'have', 'are', 'not', 'was', 'were', 'your', 'site', 'about', 'more', 'page', 'home', 'will', 'can', 'all', 'has', 'our', 'their', 'been', 'which'}
    filtered_words = [w for w in words if w not in stop_words]
    total_words = len(filtered_words) or 1
    counts = Counter(filtered_words).most_common(top_n)
    
    result = []
    for word, count in counts:
        density = round((count / total_words) * 100, 2)
        result.append({"word": word, "count": count, "density": density})
    return result

# =========================================================================
# REAL GOOGLE BACKLINK SCRAPER (WITHOUT PAID API)
# =========================================================================
def fetch_real_google_backlinks(domain):
    real_backlinks = []
    try:
        # Google query searching for mentions of domain outside of its own domain
        search_url = f"https://www.google.com/search?q=%22{domain}%22+-site:{domain}&num=15"
        scrape_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        res = requests.get(search_url, headers=scrape_headers, timeout=3)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results:
                link_tag = result.find('a', href=True)
                title_tag = result.find('h3')
                
                if link_tag and title_tag:
                    href = link_tag['href']
                    title = title_tag.get_text()
                    
                    if href.startswith('http') and domain not in href:
                        parsed_href = urllib.parse.urlparse(href)
                        real_backlinks.append({
                            "source_website": href,
                            "domain": parsed_href.netloc,
                            "anchor": title[:50] or "Direct Mention",
                            "type": "Live Web Link"
                        })
    except Exception as e:
        print("Google Backlink Scrape Limit:", e)
    
    return real_backlinks

# =========================================================================
# FILE ANALYZERS WITH FAST TIMEOUTS
# =========================================================================
def analyze_sitemap(url):
    try:
        res = requests.get(url, timeout=2, headers=DEFAULT_HEADERS)
        if res.status_code == 200 and ("xml" in res.headers.get("Content-Type", "").lower() or "<urlset" in res.text or "<sitemapindex" in res.text):
            urls = re.findall(r'<loc>(.*?)</loc>', res.text, re.IGNORECASE)
            url_count = len(urls)
            return {
                "exists": True,
                "code": 200,
                "url_count": url_count,
                "url": url,
                "summary": f"Valid XML Sitemap with {url_count} URLs indexed.",
                "explanation": "Search engine crawlers can index deep routes effortlessly.",
                "fix_action": "Sitemap active & healthy."
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url_count": 0,
            "url": url,
            "summary": "Sitemap XML missing or non-200 HTTP code.",
            "explanation": "Crawlers might miss lower-level pages.",
            "fix_action": "Generate XML Sitemap."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url_count": 0,
            "url": url,
            "summary": "Sitemap check timed out.",
            "explanation": "Server didn't respond to sitemap endpoint within 2s.",
            "fix_action": "Verify /sitemap.xml route."
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=2, headers=DEFAULT_HEADERS)
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            explanation = "CRITICAL: Site completely blocks crawlers!" if is_blocking_all else "Good: Robots directives allow indexing."
            return {
                "exists": True,
                "code": 200,
                "url": url,
                "is_blocking_all": is_blocking_all,
                "summary": content[:200] + ("..." if len(content) > 200 else ""),
                "explanation": explanation,
                "fix_action": "Check Disallow rules." if is_blocking_all else "Robots.txt is active."
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt file missing.",
            "explanation": "Crawlers scan everything unrestricted.",
            "fix_action": "Create robots.txt file."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt request timed out.",
            "explanation": "Could not fetch crawler instructions in 2s.",
            "fix_action": "Check server routing."
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=2, headers=DEFAULT_HEADERS)
        if res.status_code == 200:
            try:
                data = res.json()
                app_name = data.get("name") or data.get("short_name") or "Web App"
                return {
                    "exists": True,
                    "code": 200,
                    "url": url,
                    "summary": f"PWA Manifest active ('{app_name}').",
                    "explanation": "Supports installation on mobile/desktop.",
                    "fix_action": "Manifest healthy."
                }
            except Exception:
                pass
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "summary": "Manifest.json missing or invalid JSON.",
            "explanation": "No PWA installation prompts.",
            "fix_action": "Add web manifest.json."
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "summary": "Manifest request timed out.",
            "explanation": "Unreachable web app manifest.",
            "fix_action": "Verify manifest path."
        }

def fetch_ip_geolocation(ip_address):
    if not ip_address or ip_address == "Resolution Failed":
        return {"country": "Unknown", "region": "Unknown", "city": "Unknown", "isp": "Unknown"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,isp", timeout=1.5)
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
    return {"country": "Global Cloud", "region": "Edge Node", "city": "Datacenter", "isp": "CDN / Hosting Provider"}

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
        return jsonify({"success": False, "message": "Unauthorized Session."}), 401
        
    target_raw = request.form.get('target', '').strip()
    if not target_raw:
        return jsonify({"success": False, "message": "Target URL input cannot be empty."})

    domain, full_url, base_scheme_url = clean_domain_input(target_raw)
    
    start_time = time.time()
    try:
        session_req = requests.Session()
        res = session_req.get(full_url, timeout=4, headers=DEFAULT_HEADERS, allow_redirects=True)
        latency = round((time.time() - start_time) * 1000, 2)
        html_body = res.text
        response_headers = dict(res.headers)
        
        redirect_chain = []
        if res.history:
            for resp in res.history:
                redirect_chain.append({"status": resp.status_code, "url": resp.url})
            redirect_chain.append({"status": res.status_code, "url": res.url})
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Target website connection failed ({str(e)})."
        }), 400

    # CMS Detection
    html_lower = html_body.lower()
    is_wordpress = any(i in html_lower for i in ["wp-content", "wp-includes", "wp-json", "wordpress", "elementor", "yoast"])
    is_shopify = "shopify" in html_lower or "cdn.shopify.com" in html_lower
    is_wix = "wix.com" in html_lower
    is_react = "react" in html_lower or "_next" in html_lower
    is_vue = "vue" in html_lower or "_nuxt" in html_lower
    
    cms_detected = "WordPress CMS" if is_wordpress else ("Shopify E-Commerce" if is_shopify else ("Wix Builder" if is_wix else ("Next.js / React" if is_react else ("Nuxt / Vue" if is_vue else "Custom HTML/JS Stack"))))

    has_viewport = bool(re.search(r'<meta\s+name=["\']viewport["\']', html_body, re.IGNORECASE))
    is_responsive = has_viewport or ("@media" in html_lower)
    has_schema = "application/ld+json" in html_lower or "itemscope" in html_lower

    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_body, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else "No Title Tag Found"

    meta_description = extract_meta_tag(html_body, "description") or "Not Specified"
    meta_keywords = extract_meta_tag(html_body, "keywords") or "Not Specified"
    og_title = extract_meta_tag(html_body, "og:title") or "Not Specified"
    og_description = extract_meta_tag(html_body, "og:description") or "Not Specified"

    headings = {}
    for i in range(1, 6):
        tag_name = f"h{i}"
        matches = re.findall(rf'<{tag_name}[^>]*>(.*?)</{tag_name}>', html_body, re.IGNORECASE | re.DOTALL)
        clean_matches = [re.sub(r'<[^>]+>', '', m).strip() for m in matches if m.strip()]
        headings[tag_name.upper()] = {
            "count": len(clean_matches),
            "sample": clean_matches[:3]
        }

    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    canonical_url = canonical_match.group(1) if canonical_match else "Not Configured"

    favicon_match = re.search(r'<link\s+rel=["\'](?:shortcut )?icon["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    favicon_url = urllib.parse.urljoin(full_url, favicon_match.group(1)) if favicon_match else f"{base_scheme_url}/favicon.ico"

    css_urls = list(set(re.findall(r'<link\s+[^>]*rel=["\']stylesheet["\']\s+[^>]*href=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))
    js_urls = list(set(re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))
    img_urls = list(set(re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))

    html_size_kb = round(len(html_body.encode('utf-8')) / 1024, 2)
    css_count = len(css_urls)
    js_count = len(js_urls)
    img_count = len(img_urls)

    raw_text = re.sub(r'<[^>]+>', ' ', html_body)
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    word_count = len(raw_text.split())
    text_size_kb = round(len(raw_text.encode('utf-8')) / 1024, 2)
    text_ratio = round((text_size_kb / (html_size_kb or 1)) * 100, 2)

    img_tags = re.findall(r'<img\s+[^>]*>', html_body, re.IGNORECASE)
    missing_alt_count = sum(1 for img in img_tags if not re.search(r'alt=["\'][^"\']+["\']', img, re.IGNORECASE))

    html_lang_match = re.search(r'<html[^>]*\s+lang=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    html_lang = html_lang_match.group(1) if html_lang_match else "Not Specified"

    hreflangs = re.findall(r'<link\s+[^>]*hreflang=["\']([^"\']+)["\']\s+[^>]*href=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    hreflang_list = [{"lang": lang, "url": href} for lang, href in hreflangs[:10]]

    # Parse Internal & Outbound Links
    anchor_tags = re.findall(r'<a\s+(.*?)>(.*?)</a>', html_body, re.IGNORECASE | re.DOTALL)
    discovered_outbound_links = []

    for attrs, inner_text in anchor_tags:
        href_m = re.search(r'href=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        clean_anchor = re.sub(r'<[^>]+>', '', inner_text).strip() or "[Link]"

        if href_m:
            target_link = href_m.group(1).strip()
            if target_link.startswith(('http://', 'https://')):
                p = urllib.parse.urlparse(target_link)
                ext_domain = p.netloc.lower()
                if ext_domain and domain not in ext_domain:
                    discovered_outbound_links.append({
                        "target_url": target_link,
                        "domain": ext_domain,
                        "anchor": clean_anchor[:40]
                    })

    # REAL GOOGLE BACKLINKS SCRAPING CALL
    real_google_backlinks = fetch_real_google_backlinks(domain)
    keyword_density = extract_keywords_density(raw_text)

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

    is_https = full_url.startswith("https://")
    server_header = response_headers.get('Server', 'Protected / CDN')

    try:
        ip_address = socket.gethostbyname(domain)
    except Exception:
        ip_address = "Resolution Failed"

    geo_data = fetch_ip_geolocation(ip_address)

    score = 100
    if not is_https: score -= 15
    if not is_responsive: score -= 15
    if page_title == "No Title Tag Found": score -= 10
    if meta_description == "Not Specified": score -= 10
    if not sitemap_info["exists"]: score -= 10
    if not robots_info["exists"]: score -= 10
    if missing_alt_count > 0: score -= 10
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
        "has_schema": has_schema,
        "ip_address": ip_address,
        "geo_data": geo_data,
        "server_info": {"server": server_header},
        "title": page_title,
        "canonical_url": canonical_url,
        "favicon_url": favicon_url,
        "international_seo": {
            "lang": html_lang,
            "hreflang_count": len(hreflangs),
            "hreflang_list": hreflang_list
        },
        "meta": {
            "description": meta_description,
            "keywords": meta_keywords,
            "og_title": og_title,
            "og_description": og_description
        },
        "headings": headings,
        "files_structure": {
            "html_size_kb": html_size_kb,
            "text_ratio": text_ratio,
            "css_files_count": css_count,
            "js_files_count": js_count,
            "images_count": img_count,
            "missing_alt_images": missing_alt_count,
            "word_count": word_count
        },
        "real_backlinks_engine": {
            "discovered_count": len(real_google_backlinks),
            "inbound_list": real_google_backlinks,
            "outbound_count": len(discovered_outbound_links)
        },
        "keyword_density": keyword_density,
        "redirect_chain": redirect_chain,
        "files": {
            "sitemap": sitemap_info,
            "robots": robots_info,
            "manifest": manifest_info
        },
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

# =========================================================================
# CLEAN UI LAYOUT (NO FAKE 404 LINKS)
# =========================================================================
UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdgeMedia Real Site Audit Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f3f4f6; }
        .heading-font { font-family: 'Space Grotesk', sans-serif; }
        .cyber-card { background: rgba(17, 24, 39, 0.95); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-indigo { box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.25); }
    </style>
</head>
<body class="antialiased selection:bg-indigo-500 selection:text-white pb-12">

    <div class="max-w-[1500px] mx-auto p-4 md:p-8 space-y-6">
        
        <!-- HEADER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-3xl font-bold heading-font tracking-wide text-white flex items-center gap-3">
                    <i class="fa-solid fa-chart-line text-indigo-400"></i> OrbitEdgeMedia Deep Audit v5.0
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Real Google Web Index Scraper • File Structure • Security Audit</p>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="window.print()" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-5 py-2.5 rounded-xl font-bold transition shadow-lg flex items-center gap-2 cursor-pointer">
                    <i class="fa-solid fa-file-pdf"></i> Download PDF
                </button>
                <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                    <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
                </a>
            </div>
        </div>

        <!-- TARGET INPUT PANEL -->
        <div class="cyber-card p-6 rounded-2xl glow-indigo">
            <form id="auditForm" onsubmit="triggerScanSequence(event)" class="space-y-3">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Target Domain or Web Address</label>
                <div class="flex flex-col sm:flex-row gap-3">
                    <div class="relative flex-1">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-globe text-sm"></i></span>
                        <input type="text" id="targetUrl" required placeholder="e.g. orbitedgemedia.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Run Real Audit</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- MAIN DASHBOARD -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- OVERALL SCORE & STATS -->
            <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                    <h3 class="text-xs uppercase font-bold text-gray-400 tracking-wider mb-2">SEO Score</h3>
                    <div class="w-40 h-40 relative flex items-center justify-center">
                        <canvas id="healthScoreChart"></canvas>
                        <span id="scoreText" class="absolute text-2xl font-bold font-mono text-white">0%</span>
                    </div>
                    <p id="scoreGrade" class="text-xs text-indigo-400 font-bold mt-2 font-mono"></p>
                </div>

                <div class="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">HTTPS Security</span>
                        <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-blue-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">CMS Tech Stack</span>
                        <h3 id="badge-cms" class="text-xs md:text-sm font-bold text-white mt-1 truncate">Checking...</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">Responsiveness</span>
                        <h3 id="badge-responsive" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">Latency Speed</span>
                        <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                    </div>
                </div>
            </div>

            <!-- REAL BACKLINKS (GOOGLE SCRAPED) -->
            <div class="cyber-card p-6 rounded-2xl space-y-4 border-2 border-indigo-500/40 glow-indigo">
                <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                    <div>
                        <h3 class="font-bold text-base text-white heading-font flex items-center gap-2">
                            <i class="fa-solid fa-link text-indigo-400"></i> Live Backlinks (Google Search Scraped)
                        </h3>
                        <p class="text-xs text-gray-400 mt-0.5">Real working external pages linking or mentioning your domain on Google</p>
                    </div>
                    <span id="stat-backlinks-count" class="bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 font-mono text-xs px-3 py-1.5 rounded-lg font-bold">Live Found: 0</span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs font-mono">
                        <thead class="bg-gray-950 text-gray-400 uppercase text-[10px]">
                            <tr>
                                <th class="p-3 border-b border-gray-800">Source External Page (Live URL)</th>
                                <th class="p-3 border-b border-gray-800">Referring Domain</th>
                                <th class="p-3 border-b border-gray-800">Page Title / Mention</th>
                            </tr>
                        </thead>
                        <tbody id="real-backlinks-table" class="divide-y divide-gray-800/60 bg-gray-950/50"></tbody>
                    </table>
                </div>
            </div>

            <!-- CORE FILES -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3">Search Engine Core Files</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div id="card-sitemap" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <span id="badge-sitemap" class="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded">Checking</span>
                        <p id="desc-sitemap" class="text-xs font-semibold text-gray-200 mt-1"></p>
                    </div>
                    <div id="card-robots" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <span id="badge-robots" class="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded">Checking</span>
                        <p id="desc-robots" class="text-xs font-semibold text-gray-200 mt-1"></p>
                    </div>
                    <div id="card-manifest" class="p-4 rounded-xl border bg-gray-950 space-y-2">
                        <span id="badge-manifest" class="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded">Checking</span>
                        <p id="desc-manifest" class="text-xs font-semibold text-gray-200 mt-1"></p>
                    </div>
                </div>
            </div>

            <div class="text-center text-xs text-gray-500 font-mono py-4 border-t border-gray-800">
                OrbitEdgeMedia Site Audit Engine • Verified Live Data
            </div>

        </div>
    </div>

    <script>
        let healthChart;

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
                    renderHealthChart(data.score);

                    document.getElementById('badge-https').innerText = data.is_https ? "HTTPS Secure" : "HTTP Insecure";
                    document.getElementById('badge-cms').innerText = data.cms_detected;
                    document.getElementById('badge-responsive').innerText = data.is_responsive ? "Mobile Friendly" : "Non-Responsive";
                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;

                    // RENDER REAL SCRAPED BACKLINKS
                    const backlinks = data.real_backlinks_engine.inbound_list;
                    document.getElementById('stat-backlinks-count').innerText = `Live Found: ${backlinks.length}`;

                    const tableBody = document.getElementById('real-backlinks-table');
                    tableBody.innerHTML = '';

                    if (backlinks.length === 0) {
                        tableBody.innerHTML = `
                            <tr>
                                <td colspan="3" class="p-4 text-center text-gray-400 italic">
                                    No live external backlinks indexed on Google Search right now (or Google Scraper Rate Limit reached).
                                </td>
                            </tr>
                        `;
                    } else {
                        backlinks.forEach(bl => {
                            tableBody.innerHTML += `
                                <tr>
                                    <td class="p-3 text-indigo-300 font-mono text-[11px] font-bold">
                                        <a href="${bl.source_website}" target="_blank" class="hover:underline flex items-center gap-1">
                                            ${bl.source_website} <i class="fa-solid fa-external-link text-[9px]"></i>
                                        </a>
                                    </td>
                                    <td class="p-3 text-cyan-400 font-mono text-[11px]">${bl.domain}</td>
                                    <td class="p-3 text-gray-300 italic">${bl.anchor}</td>
                                </tr>
                            `;
                        });
                    }

                    // Render File Cards
                    renderSimpleFileCard('badge-sitemap', 'desc-sitemap', data.files.sitemap);
                    renderSimpleFileCard('badge-robots', 'desc-robots', data.files.robots);
                    renderSimpleFileCard('badge-manifest', 'desc-manifest', data.files.manifest);

                    dashboard.classList.remove('hidden');
                } else {
                    alert("Audit Error: " + data.message);
                }
            } catch (err) {
                alert("Server Error! Connection took too long.");
            } finally {
                submitBtn.disabled = false;
                spinIcon.classList.add('hidden');
            }
        }

        function renderSimpleFileCard(badgeId, descId, fileObj) {
            const badge = document.getElementById(badgeId);
            const desc = document.getElementById(descId);

            if (fileObj.exists) {
                badge.className = "text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                badge.innerText = `Found (${fileObj.code})`;
            } else {
                badge.className = "text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30";
                badge.innerText = `Missing (${fileObj.code})`;
            }
            desc.innerText = fileObj.summary;
        }

        function renderHealthChart(score) {
            const ctx = document.getElementById('healthScoreChart').getContext('2d');
            if (healthChart) healthChart.destroy();

            document.getElementById('scoreText').innerText = `${score}%`;
            document.getElementById('scoreGrade').innerText = score >= 80 ? "Grade: A" : "Grade: B";

            healthChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [score, 100 - score],
                        backgroundColor: ['#10b981', '#1f2937'],
                        borderWidth: 0
                    }]
                },
                options: { cutout: '80%', plugins: { tooltip: { enabled: false } }, responsive: true, maintainAspectRatio: false }
            });
        }
    </script>
</body>
</html>
"""

