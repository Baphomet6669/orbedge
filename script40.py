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
# ADVANCED FILE & SERVICE ANALYZERS
# =========================================================================
def analyze_sitemap(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/2.0"})
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
            "explanation": "Server didn't respond to sitemap endpoint.",
            "fix_action": "Verify /sitemap.xml route."
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/2.0"})
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            explanation = "CRITICAL: Site completely blocks crawlers!" if is_blocking_all else "Good: Robots directives allow indexing."
            return {
                "exists": True,
                "code": 200,
                "url": url,
                "is_blocking_all": is_blocking_all,
                "summary": content[:250] + ("..." if len(content) > 250 else ""),
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
            "explanation": "Could not fetch crawler instructions.",
            "fix_action": "Check server routing."
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0 OrbitEdgeBot/2.0"})
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
        return jsonify({"error": "Unauthorized Terminal"}), 401
        
    target_raw = request.form.get('target', '').strip()
    if not target_raw:
        return jsonify({"success": False, "message": "Target URL input cannot be empty."})

    domain, full_url, base_scheme_url = clean_domain_input(target_raw)
    
    start_time = time.time()
    try:
        session_req = requests.Session()
        res = session_req.get(full_url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OrbitEdgeMedia-Auditor/5.0"}, allow_redirects=True)
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

    # 1. CMS & Tech Stack Detection
    html_lower = html_body.lower()
    is_wordpress = any(i in html_lower for i in ["wp-content", "wp-includes", "wp-json", "wordpress", "elementor", "yoast"])
    is_shopify = "shopify" in html_lower or "cdn.shopify.com" in html_lower
    is_wix = "wix.com" in html_lower
    is_react = "react" in html_lower or "_next" in html_lower
    is_vue = "vue" in html_lower or "_nuxt" in html_lower
    
    cms_detected = "WordPress CMS" if is_wordpress else ("Shopify E-Commerce" if is_shopify else ("Wix Builder" if is_wix else ("Next.js / React" if is_react else ("Nuxt / Vue" if is_vue else "Custom HTML/JS Stack"))))

    # 2. Viewport & Mobile Responsiveness
    has_viewport = bool(re.search(r'<meta\s+name=["\']viewport["\']', html_body, re.IGNORECASE))
    is_responsive = has_viewport or ("@media" in html_lower)

    # 3. Comprehensive Metadata
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_body, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else "No Title Tag Found"

    meta_description = extract_meta_tag(html_body, "description") or "Not Specified"
    meta_keywords = extract_meta_tag(html_body, "keywords") or "Not Specified"
    og_title = extract_meta_tag(html_body, "og:title") or "Not Specified"
    og_description = extract_meta_tag(html_body, "og:description") or "Not Specified"
    og_image = extract_meta_tag(html_body, "og:image") or "Not Specified"
    twitter_card = extract_meta_tag(html_body, "twitter:card") or "Not Specified"

    # 4. Heading Tag Structure
    headings = {}
    for i in range(1, 6):
        tag_name = f"h{i}"
        matches = re.findall(rf'<{tag_name}[^>]*>(.*?)</{tag_name}>', html_body, re.IGNORECASE | re.DOTALL)
        clean_matches = [re.sub(r'<[^>]+>', '', m).strip() for m in matches if m.strip()]
        headings[tag_name.upper()] = {
            "count": len(clean_matches),
            "sample": clean_matches[:3]
        }

    # 5. Canonical & Favicon
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    canonical_url = canonical_match.group(1) if canonical_match else "Not Configured"

    favicon_match = re.search(r'<link\s+rel=["\'](?:shortcut )?icon["\']\s+href=["\']([^"\']*)["\']', html_body, re.IGNORECASE)
    favicon_url = urllib.parse.urljoin(full_url, favicon_match.group(1)) if favicon_match else f"{base_scheme_url}/favicon.ico"

    # 6. Detailed File Structure & Resource Breakdown (Exact File Counts & Sizes)
    css_urls = list(set(re.findall(r'<link\s+[^>]*rel=["\']stylesheet["\']\s+[^>]*href=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))
    js_urls = list(set(re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))
    img_urls = list(set(re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_body, re.IGNORECASE)))

    html_size_kb = round(len(html_body.encode('utf-8')) / 1024, 2)
    
    # Calculate approximate external assets total weight
    css_count = len(css_urls)
    js_count = len(js_urls)
    img_count = len(img_urls)

    # Word count and Text-to-HTML Ratio
    raw_text = re.sub(r'<[^>]+>', ' ', html_body)
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    word_count = len(raw_text.split())
    text_size_kb = round(len(raw_text.encode('utf-8')) / 1024, 2)
    text_ratio = round((text_size_kb / (html_size_kb or 1)) * 100, 2)

    # Images missing ALT tag
    img_tags = re.findall(r'<img\s+[^>]*>', html_body, re.IGNORECASE)
    missing_alt_count = sum(1 for img in img_tags if not re.search(r'alt=["\'][^"\']+["\']', img, re.IGNORECASE))

    # 7. Comprehensive Internationalization (International SEO Audit)
    html_lang_match = re.search(r'<html[^>]*\s+lang=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    html_dir_match = re.search(r'<html[^>]*\s+dir=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    
    html_lang = html_lang_match.group(1) if html_lang_match else "Not Specified"
    text_direction = html_dir_match.group(1) if html_dir_match else "LTR (Default)"

    hreflangs = re.findall(r'<link\s+[^>]*hreflang=["\']([^"\']+)["\']\s+[^>]*href=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
    if not hreflangs:
        # Reverse attribute order regex
        hreflangs = re.findall(r'<link\s+[^>]*href=["\']([^"\']+)["\']\s+[^>]*hreflang=["\']([^"\']+)["\']', html_body, re.IGNORECASE)
        hreflangs = [(lang, href) for href, lang in hreflangs]

    hreflang_list = [{"lang": lang, "url": href} for lang, href in hreflangs[:10]]

    # 8. Detailed Backlink & Outbound Domain Deep Analysis
    all_anchors = re.findall(r'<a\s+([^>]+)>', html_body, re.IGNORECASE)
    internal_links_list = []
    external_backlinks_list = []
    nofollow_count = 0
    dofollow_count = 0

    external_domain_counter = Counter()

    for anchor_attrs in all_anchors:
        href_match = re.search(r'href=["\']([^"\']*)["\']', anchor_attrs, re.IGNORECASE)
        rel_match = re.search(r'rel=["\']([^"\']*)["\']', anchor_attrs, re.IGNORECASE)
        rel_val = rel_match.group(1).lower() if rel_match else ""

        is_nofollow = "nofollow" in rel_val
        if is_nofollow:
            nofollow_count += 1
        else:
            dofollow_count += 1

        if href_match:
            href = href_match.group(1).strip()
            if href.startswith('http://') or href.startswith('https://'):
                parsed_href = urllib.parse.urlparse(href)
                target_netloc = parsed_href.netloc.lower()
                if target_netloc and domain not in target_netloc:
                    external_domain_counter[target_netloc] += 1
                    if len(external_backlinks_list) < 20:
                        external_backlinks_list.append({
                            "url": href,
                            "domain": target_netloc,
                            "rel": rel_val or "dofollow"
                        })
                else:
                    if len(internal_links_list) < 10:
                        internal_links_list.append(href)
            elif href.startswith('/') or href.startswith('#'):
                if len(internal_links_list) < 10:
                    internal_links_list.append(href)

    total_internal_links = len(internal_links_list)
    total_external_links = sum(external_domain_counter.values())
    unique_outbound_domains = len(external_domain_counter)

    top_outbound_domains = [{"domain": dom, "count": cnt} for dom, cnt in external_domain_counter.most_common(10)]

    # Social Profiles Linked
    social_platforms = ['facebook.com', 'twitter.com', 'x.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'pinterest.com', 'github.com']
    social_links_found = [dom for dom in external_domain_counter if any(sp in dom for sp in social_platforms)]

    # 9. Keyword Density
    keyword_density = extract_keywords_density(raw_text)

    # 10. Core File Inspections Concurrent Execution
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

    # 11. Broken Link Check (Sampled Direct URLs)
    sample_links = [b["url"] for b in external_backlinks_list[:6]]
    broken_links = []
    
    def check_link(link):
        try:
            r = requests.head(link, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code >= 400:
                broken_links.append({"url": link, "status": r.status_code})
        except Exception:
            broken_links.append({"url": link, "status": "Failed / Timeout"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(check_link, sample_links)

    # 12. Security & Server Infrastructure
    is_https = full_url.startswith("https://")
    server_header = response_headers.get('Server', 'Protected / CDN')
    content_encoding = response_headers.get('Content-Encoding', 'Standard / Uncompressed')
    hsts_header = 'Strict-Transport-Security' in response_headers
    x_frame_options = response_headers.get('X-Frame-Options', 'Not Configured')
    csp_header = 'Content-Security-Policy' in response_headers

    try:
        ip_address = socket.gethostbyname(domain)
    except Exception:
        ip_address = "Resolution Failed"

    geo_data = fetch_ip_geolocation(ip_address)

    # 13. Health Score Calculation (Accurate Weights)
    score = 100
    if not is_https: score -= 15
    if not is_responsive: score -= 15
    if page_title == "No Title Tag Found": score -= 10
    if meta_description == "Not Specified": score -= 10
    if not sitemap_info["exists"]: score -= 10
    if not robots_info["exists"]: score -= 10
    if missing_alt_count > 0: score -= 10
    if headings.get("H1", {}).get("count", 0) == 0: score -= 10
    score = max(score, 15)

    return jsonify({
        "success": True,
        "score": score,
        "domain": domain,
        "full_url": full_url,
        "latency": latency,
        "is_https": is_https,
        "cms_detected": cms_detected,
        "is_responsive": is_responsive,
        "ip_address": ip_address,
        "geo_data": geo_data,
        "server_info": {
            "server": server_header,
            "encoding": content_encoding,
            "hsts": hsts_header,
            "x_frame": x_frame_options,
            "csp": csp_header
        },
        "title": page_title,
        "canonical_url": canonical_url,
        "favicon_url": favicon_url,
        "international_seo": {
            "lang": html_lang,
            "direction": text_direction,
            "hreflang_count": len(hreflangs),
            "hreflang_list": hreflang_list
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
        "files_structure": {
            "html_size_kb": html_size_kb,
            "text_size_kb": text_size_kb,
            "text_ratio": text_ratio,
            "css_files_count": css_count,
            "js_files_count": js_count,
            "images_count": img_count,
            "total_images": len(img_tags),
            "missing_alt_images": missing_alt_count,
            "word_count": word_count
        },
        "backlinks_and_links": {
            "internal_count": total_internal_links,
            "external_count": total_external_links,
            "dofollow_count": dofollow_count,
            "nofollow_count": nofollow_count,
            "unique_outbound_domains": unique_outbound_domains,
            "top_outbound_domains": top_outbound_domains,
            "external_backlinks_list": external_backlinks_list,
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
# ULTRA MODERN NEON CYBERPUNK UI LAYOUT WITH CHART.JS & FIXED PDF EXPORT
# =========================================================================
UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdgeMedia Enterprise Site Audit Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f3f4f6; }
        .heading-font { font-family: 'Space Grotesk', sans-serif; }
        .cyber-card { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-indigo { box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.25); }
    </style>
</head>
<body class="antialiased selection:bg-indigo-500 selection:text-white pb-12">

    <div class="max-w-[1500px] mx-auto p-4 md:p-8 space-y-6" id="reportable-content">
        
        <!-- BRANDING HEADER BANNER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-3xl font-bold heading-font tracking-wide text-white flex items-center gap-3">
                    <i class="fa-solid fa-chart-line text-indigo-400"></i> OrbitEdgeMedia Deep Audit v5.0
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Enterprise Backlinks • File Structure • International SEO • Security Engine</p>
            </div>
            <div class="flex items-center gap-3" id="header-actions">
                <button id="pdfBtn" onclick="exportPDFReport()" class="hidden bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2.5 rounded-xl font-bold transition shadow-lg flex items-center gap-2 cursor-pointer">
                    <i class="fa-solid fa-file-pdf"></i> Download Full PDF Report
                </button>
                <a href="/" class="bg-gray-900 border border-gray-800 text-gray-300 text-xs px-4 py-2.5 rounded-xl hover:bg-gray-800 transition font-medium">
                    <i class="fa-solid fa-arrow-left mr-1.5"></i> Dashboard
                </a>
            </div>
        </div>

        <!-- TARGET INPUT PANEL -->
        <div class="cyber-card p-6 rounded-2xl glow-indigo" id="input-panel">
            <form id="auditForm" onsubmit="triggerScanSequence(event)" class="space-y-3">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Target Domain or Web Address</label>
                <div class="flex flex-col sm:flex-row gap-3">
                    <div class="relative flex-1">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-globe text-sm"></i></span>
                        <input type="text" id="targetUrl" required placeholder="e.g. orbitedgemedia.com or https://example.com" class="w-full bg-gray-950 border border-gray-800 rounded-xl py-3.5 pl-11 pr-4 text-xs text-white focus:outline-none focus:border-indigo-500 transition font-mono">
                    </div>
                    <button type="submit" id="submitBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-8 py-3.5 rounded-xl cursor-pointer transition shrink-0 shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2">
                        <i id="spinIcon" class="fa-solid fa-circle-notch animate-spin text-sm hidden"></i>
                        <span>Run Enterprise Audit</span>
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
                    <h3 class="text-xs uppercase font-bold text-gray-400 tracking-wider mb-2">SEO & Security Score</h3>
                    <div class="w-40 h-40 relative flex items-center justify-center">
                        <canvas id="healthScoreChart"></canvas>
                        <span id="scoreText" class="absolute text-2xl font-bold font-mono text-white">0%</span>
                    </div>
                    <p id="scoreGrade" class="text-xs text-indigo-400 font-bold mt-2 font-mono"></p>
                </div>

                <!-- QUICK METRIC BADGES -->
                <div class="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-indigo-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">HTTPS Security</span>
                        <h3 id="badge-https" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">SSL/TLS Protection</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-blue-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">CMS Tech Stack</span>
                        <h3 id="badge-cms" class="text-xs md:text-sm font-bold text-white mt-1 truncate">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Core Architecture</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-emerald-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Responsiveness</span>
                        <h3 id="badge-responsive" class="text-xs md:text-sm font-bold mt-1">Checking...</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Mobile Viewport</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-cyan-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Latency Speed</span>
                        <h3 id="badge-latency" class="text-xs md:text-sm font-bold text-white font-mono mt-1">0 ms</h3>
                        <p class="text-[9px] text-gray-500 mt-2">Server Response</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Server Geolocation</span>
                        <h3 id="badge-geo" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                        <p id="badge-location" class="text-[9px] text-gray-500 mt-2">Country Location</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-pink-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">International SEO</span>
                        <h3 id="badge-lang" class="text-xs md:text-sm font-bold text-white mt-1">Lang: -</h3>
                        <p id="badge-hreflang" class="text-[9px] text-gray-500 mt-2">0 Hreflangs</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-amber-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Word Count</span>
                        <h3 id="badge-words" class="text-xs md:text-sm font-bold text-amber-400 font-mono mt-1">0 Words</h3>
                        <p id="badge-ratio" class="text-[9px] text-gray-500 mt-2">Text-to-HTML Ratio: 0%</p>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-teal-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">File Assets Breakdown</span>
                        <h3 id="badge-assets" class="text-xs md:text-sm font-bold text-teal-300 font-mono mt-1">0 KB</h3>
                        <p id="badge-assets-count" class="text-[9px] text-gray-500 mt-2">CSS / JS / Img Count</p>
                    </div>
                </div>
            </div>

            <!-- VISUAL CHARTS ROW -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- CHART 1: LINKS & BACKLINKS -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Link Distribution (Internal vs Outbound)</h3>
                    <div class="w-full max-w-[280px] h-48">
                        <canvas id="linksChart"></canvas>
                    </div>
                </div>

                <!-- CHART 2: KEYWORD DENSITY -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Top Keyword Density Frequencies</h3>
                    <div class="w-full max-w-[320px] h-48">
                        <canvas id="keywordsChart"></canvas>
                    </div>
                </div>

                <!-- CHART 3: ASSET & PAGE WEIGHT -->
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center col-span-1 md:col-span-2 lg:col-span-1">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">File Assets Count Breakdown</h3>
                    <div class="w-full max-w-[280px] h-48">
                        <canvas id="assetsChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- BACKLINKS & OUTBOUND DOMAINS DEEP INSPECTION -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center justify-between">
                    <span class="flex items-center gap-2"><i class="fa-solid fa-link text-indigo-400"></i> Outbound Backlinks & Target Linking Domains</span>
                    <span id="badge-outbound-count" class="bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs px-2.5 py-0.5 rounded font-mono font-bold">0 Domains</span>
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- TOP LINKED DOMAINS -->
                    <div class="space-y-3">
                        <h4 class="text-xs font-bold uppercase text-gray-400 tracking-wider">Top Linked External Domains</h4>
                        <div id="outbound-domains-list" class="space-y-2 max-h-56 overflow-y-auto"></div>
                    </div>
                    <!-- SAMPLE EXTERNAL BACKLINKS DETECTED -->
                    <div class="space-y-3">
                        <h4 class="text-xs font-bold uppercase text-gray-400 tracking-wider">External Backlink URLs & Rel Directives</h4>
                        <div id="external-backlinks-list" class="space-y-2 max-h-56 overflow-y-auto"></div>
                    </div>
                </div>
            </div>

            <!-- CORE FILES & DIRECTIVES -->
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

            <!-- DETAILED TECHNICAL & METADATA GRID -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT COLUMN -->
                <div class="lg:col-span-2 space-y-6">
                    
                    <!-- TITLE & CANONICAL & FAVICON -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                            <h3 class="font-bold text-sm text-white heading-font flex items-center gap-2">
                                <i class="fa-solid fa-heading text-indigo-400"></i> Page Title & Identity Directives
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

                    <!-- INTERNATIONAL SEO TAGS (HREFLANG) -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-language text-pink-400"></i> International SEO & Hreflang Mapping
                        </h3>
                        <div id="hreflang-container" class="space-y-2 text-xs"></div>
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
                            <i class="fa-solid fa-hashtag text-pink-400"></i> Linked Social Media Profiles
                        </h3>
                        <div id="social-container" class="space-y-2"></div>
                    </div>

                    <!-- BROKEN LINKS DIAGNOSTICS -->
                    <div class="cyber-card p-6 rounded-2xl space-y-4">
                        <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center gap-2">
                            <i class="fa-solid fa-link-slash text-rose-400"></i> Link Health & HTTP Diagnostics
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

                    // Quick Badges
                    const httpsEl = document.getElementById('badge-https');
                    httpsEl.className = data.is_https ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    httpsEl.innerText = data.is_https ? "HTTPS Secure" : "HTTP Insecure";

                    document.getElementById('badge-cms').innerText = data.cms_detected;

                    const respEl = document.getElementById('badge-responsive');
                    respEl.className = data.is_responsive ? "text-xs md:text-sm font-bold text-emerald-400 mt-1" : "text-xs md:text-sm font-bold text-rose-400 mt-1";
                    respEl.innerText = data.is_responsive ? "Mobile Friendly" : "Non-Responsive";

                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;
                    document.getElementById('badge-geo').innerText = data.ip_address;
                    document.getElementById('badge-location').innerText = `${data.geo_data.city}, ${data.geo_data.country}`;

                    document.getElementById('badge-lang').innerText = `Lang: ${data.international_seo.lang}`;
                    document.getElementById('badge-hreflang').innerText = `${data.international_seo.hreflang_count} Hreflang Tags`;

                    document.getElementById('badge-words').innerText = `${data.files_structure.word_count} Words`;
                    document.getElementById('badge-ratio').innerText = `Text Ratio: ${data.files_structure.text_ratio}%`;

                    document.getElementById('badge-assets').innerText = `${data.files_structure.html_size_kb} KB HTML`;
                    document.getElementById('badge-assets-count').innerText = `${data.files_structure.css_files_count} CSS / ${data.files_structure.js_files_count} JS / ${data.files_structure.images_count} Imgs`;

                    // Render Outbound Backlinks
                    document.getElementById('badge-outbound-count').innerText = `${data.backlinks_and_links.unique_outbound_domains} Unique Domains`;
                    
                    const outboundContainer = document.getElementById('outbound-domains-list');
                    outboundContainer.innerHTML = '';
                    if (data.backlinks_and_links.top_outbound_domains.length === 0) {
                        outboundContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No external domains linked.</p>';
                    } else {
                        data.backlinks_and_links.top_outbound_domains.forEach(d => {
                            outboundContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg flex items-center justify-between text-xs font-mono">
                                    <span class="text-indigo-300 truncate">${d.domain}</span>
                                    <span class="bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded text-[10px] font-bold">${d.count} links</span>
                                </div>
                            `;
                        });
                    }

                    const backlinksContainer = document.getElementById('external-backlinks-list');
                    backlinksContainer.innerHTML = '';
                    if (data.backlinks_and_links.external_backlinks_list.length === 0) {
                        backlinksContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No outbound backlinks discovered.</p>';
                    } else {
                        data.backlinks_and_links.external_backlinks_list.forEach(bl => {
                            backlinksContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg flex items-center justify-between text-xs gap-2">
                                    <span class="text-gray-300 font-mono truncate text-[11px]" title="${bl.url}">${bl.url}</span>
                                    <span class="bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded text-[10px] font-mono shrink-0">${bl.rel}</span>
                                </div>
                            `;
                        });
                    }

                    // Render International Hreflangs
                    const hreflangContainer = document.getElementById('hreflang-container');
                    hreflangContainer.innerHTML = '';
                    if (data.international_seo.hreflang_list.length === 0) {
                        hreflangContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No Hreflang language targeting tags detected on page.</p>';
                    } else {
                        data.international_seo.hreflang_list.forEach(hl => {
                            hreflangContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg flex items-center justify-between font-mono">
                                    <span class="text-pink-400 font-bold uppercase text-[10px]">${hl.lang}</span>
                                    <span class="text-gray-400 text-[11px] truncate">${hl.url}</span>
                                </div>
                            `;
                        });
                    }

                    // Render Charts
                    renderLinksChart(data.backlinks_and_links.internal_count, data.backlinks_and_links.external_count, data.backlinks_and_links.nofollow_count);
                    renderKeywordsChart(data.keyword_density);
                    renderAssetsChart(data.files_structure);

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
                    if (data.backlinks_and_links.social_links.length === 0) {
                        socialContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No social media profiles detected in links.</p>';
                    } else {
                        data.backlinks_and_links.social_links.forEach(dom => {
                            socialContainer.innerHTML += `
                                <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg text-xs font-mono text-pink-400 flex items-center gap-2">
                                    <i class="fa-solid fa-share-nodes"></i> ${dom}
                                </div>
                            `;
                        });
                    }

                    // Broken Links
                    const linksContainer = document.getElementById('broken-links-container');
                    linksContainer.innerHTML = '';
                    if (data.broken_links.length === 0) {
                        linksContainer.innerHTML = `<div class="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center text-emerald-400 text-xs font-medium"><i class="fa-solid fa-circle-check mr-1.5"></i> All Analyzed External Links Active!</div>`;
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
                        redirectsContainer.innerHTML = '<p class="text-xs text-emerald-400">Direct loading path without HTTP redirects.</p>';
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
            document.getElementById('scoreGrade').innerText = score >= 80 ? "Grade: A (Excellent)" : (score >= 60 ? "Grade: B (Moderate)" : "Grade: C (Needs Work)");

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
                    labels: ['Internal Links', 'Outbound Links', 'Nofollow Links'],
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

        function renderAssetsChart(filesStruct) {
            const ctx = document.getElementById('assetsChart').getContext('2d');
            if (assetsChart) assetsChart.destroy();

            assetsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['CSS Files', 'JS Files', 'Images Found'],
                    datasets: [{
                        data: [filesStruct.css_files_count, filesStruct.js_files_count, filesStruct.images_count],
                        backgroundColor: ['#eab308', '#ec4899', '#10b981'],
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
            if (!data.is_https) fixes.push("🔒 Enable SSL / HTTPS certificate on server.");
            if (!data.is_responsive) fixes.push("📱 Add viewport tag for mobile responsiveness.");
            if (!data.files.sitemap.exists) fixes.push("🗺️ Generate /sitemap.xml for Google indexing.");
            if (!data.files.robots.exists) fixes.push("🤖 Create /robots.txt file for crawlers.");
            if (data.files_structure.missing_alt_images > 0) fixes.push(`🖼️ Add 'alt' attributes to ${data.files_structure.missing_alt_images} images.`);
            if (data.meta.description === "Not Specified") fixes.push("✍️ Add a custom Meta Description tag.");
            if (data.international_seo.hreflang_count === 0) fixes.push("🌐 Consider adding Hreflang tags if targeting multiple languages.");

            if (fixes.length === 0) {
                container.innerHTML = '<p class="text-emerald-400 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> No high-priority fixes needed!</p>';
            } else {
                fixes.forEach(fix => {
                    container.innerHTML += `<div class="p-2.5 bg-gray-950 border border-gray-800 rounded-lg text-gray-300 font-mono">${fix}</div>`;
                });
            }
        }

        // FIXED PDF EXPORT FUNCTION
        function exportPDFReport() {
            const element = document.getElementById('reportable-content');
            const inputPanel = document.getElementById('input-panel');
            const headerActions = document.getElementById('header-actions');
            
            // Hide control panels temporarily for crisp clean PDF
            inputPanel.style.display = 'none';
            headerActions.style.display = 'none';

            const opt = {
                margin:       [0.3, 0.3, 0.3, 0.3],
                filename:     `OrbitEdge_Site_Audit_${Date.now()}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true, logging: false, backgroundColor: '#030712' },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };

            html2pdf().set(opt).from(element).save().then(() => {
                inputPanel.style.display = 'block';
                headerActions.style.display = 'flex';
            }).catch(err => {
                console.error('PDF Generation error:', err);
                inputPanel.style.display = 'block';
                headerActions.style.display = 'flex';
            });
        }
    </script>
</body>
</html>
"""
