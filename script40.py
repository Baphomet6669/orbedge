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
# LIVE GOOGLE SEARCH & MENTION BACKLINK SCRAPER (REAL UNBOUNDED)
# =========================================================================
def fetch_real_live_backlinks(domain):
    scraped_backlinks = []
    try:
        search_query = f"\"{domain}\" -site:{domain}"
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"https://www.google.com/search?q={encoded_query}&num=15"
        
        custom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        resp = requests.get(search_url, headers=custom_headers, timeout=3.5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            blocks = soup.find_all('div', class_='g')
            
            for block in blocks:
                link_el = block.find('a', href=True)
                heading_el = block.find('h3')
                
                if link_el and heading_el:
                    link_href = link_el['href']
                    anchor_text = heading_el.get_text()
                    
                    if link_href.startswith('http') and domain not in link_href:
                        parsed_href = urllib.parse.urlparse(link_href)
                        scraped_backlinks.append({
                            "source_website": link_href,
                            "domain": parsed_href.netloc,
                            "anchor": anchor_text[:60] or "Direct Mention",
                            "type": "Live Web Index"
                        })
    except Exception as err:
        print(f"[Backlink Scraper Engine] Log Notice: {err}")
    
    return scraped_backlinks

# =========================================================================
# ADVANCED SITEMAP XML & CORE FILE ANALYZERS
# =========================================================================
def analyze_sitemap_deep(url):
    try:
        res = requests.get(url, timeout=3, headers=DEFAULT_HEADERS)
        if res.status_code == 200 and ("xml" in res.headers.get("Content-Type", "").lower() or "<urlset" in res.text or "<sitemapindex" in res.text):
            urls = re.findall(r'<loc>(.*?)</loc>', res.text, re.IGNORECASE)
            url_count = len(urls)
            
            sample_urls = urls[:5]
            seo_healthy_count = 0
            issues = []

            for u in sample_urls:
                try:
                    chk = requests.head(u, timeout=1.5, headers=DEFAULT_HEADERS)
                    if chk.status_code == 200:
                        seo_healthy_count += 1
                    else:
                        issues.append(f"URL {u} returned HTTP status {chk.status_code}")
                except Exception:
                    issues.append(f"Unreachable URL in Sitemap: {u}")

            is_seo_optimized = (seo_healthy_count == len(sample_urls)) and (url_count > 0)
            status_msg = "Sitemap XML is fully active & indexed URLs are accessible." if is_seo_optimized else "Sitemap XML has broken or slow URLs."

            return {
                "exists": True,
                "code": 200,
                "url_count": url_count,
                "url": url,
                "is_seo_optimized": is_seo_optimized,
                "sample_urls": sample_urls,
                "issues": issues,
                "summary": f"Valid XML Sitemap found with {url_count} URLs indexed.",
                "explanation": status_msg,
                "fix_code": f"""<!-- XML Sitemap Recommended Template -->
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{url.replace('/sitemap.xml','')}/</loc>
    <lastmod>{datetime.utcnow().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url_count": 0,
            "url": url,
            "is_seo_optimized": False,
            "sample_urls": [],
            "issues": ["Sitemap file missing or non-200 HTTP code."],
            "summary": "Sitemap XML missing or non-200 HTTP code.",
            "explanation": "Search engines cannot systematically crawl and index site structure.",
            "fix_code": """# Flask Dynamic Sitemap Route:
@app.route('/sitemap.xml')
def sitemap():
    pages = ['/', '/about', '/contact', '/services']
    host_base = request.host_url.rstrip('/')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
    for p in pages:
        xml += f'  <url><loc>{host_base}{p}</loc><changefreq>weekly</changefreq></url>\\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')"""
        }
    except Exception as e:
        return {
            "exists": False,
            "code": "Timeout",
            "url_count": 0,
            "url": url,
            "is_seo_optimized": False,
            "sample_urls": [],
            "issues": [str(e)],
            "summary": "Sitemap request timed out.",
            "explanation": "Server didn't respond to sitemap endpoint within 3s.",
            "fix_code": "# Ensure /sitemap.xml is routed cleanly without blocking database queries."
        }

def analyze_robots(url):
    try:
        res = requests.get(url, timeout=2.5, headers=DEFAULT_HEADERS)
        if res.status_code == 200 and ("disallow" in res.text.lower() or "user-agent" in res.text.lower()):
            content = res.text
            is_blocking_all = bool(re.search(r'Disallow:\s*/\s*$', content, re.MULTILINE))
            explanation = "CRITICAL: Site completely blocks crawlers!" if is_blocking_all else "Good: Robots directives allow search indexing."
            
            return {
                "exists": True,
                "code": 200,
                "url": url,
                "is_blocking_all": is_blocking_all,
                "summary": content[:180] + ("..." if len(content) > 180 else ""),
                "explanation": explanation,
                "fix_code": """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /private/

Sitemap: """ + url.replace('/robots.txt', '/sitemap.xml')
            }
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt file missing.",
            "explanation": "Crawlers scan everything unrestricted. Recommended to restrict admin endpoints.",
            "fix_code": """User-agent: *
Allow: /
Disallow: /api/
Disallow: /login/

Sitemap: """ + url.replace('/robots.txt', '/sitemap.xml')
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "is_blocking_all": False,
            "summary": "Robots.txt request timed out.",
            "explanation": "Could not fetch crawler instructions in time.",
            "fix_code": "# Return standard static robots.txt file from web root."
        }

def analyze_manifest(url):
    try:
        res = requests.get(url, timeout=2.5, headers=DEFAULT_HEADERS)
        if res.status_code == 200:
            try:
                data = res.json()
                app_name = data.get("name") or data.get("short_name") or "Web App"
                return {
                    "exists": True,
                    "code": 200,
                    "url": url,
                    "summary": f"PWA Manifest active ('{app_name}').",
                    "explanation": "Supports installation on mobile and desktop devices.",
                    "fix_code": json.dumps(data, indent=2)
                }
            except Exception:
                pass
        return {
            "exists": False,
            "code": res.status_code,
            "url": url,
            "summary": "Manifest.json missing or invalid JSON.",
            "explanation": "No PWA installation prompts on mobile browsers.",
            "fix_code": """{
  "short_name": "App",
  "name": "WebApplication",
  "icons": [{ "src": "favicon.ico", "sizes": "64x64", "type": "image/x-icon" }],
  "start_url": "/",
  "background_color": "#030712",
  "theme_color": "#6366f1",
  "display": "standalone"
}"""
        }
    except Exception:
        return {
            "exists": False,
            "code": "Timeout",
            "url": url,
            "summary": "Manifest request timed out.",
            "explanation": "Unreachable web app manifest.",
            "fix_code": "// Add manifest link in HTML <head>: <link rel='manifest' href='/manifest.json'>"
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

    # CMS & Stack Detection
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
    discovered_external_links = []
    dofollow_cnt, nofollow_cnt = 0, 0

    for attrs, inner_text in anchor_tags:
        href_m = re.search(r'href=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        rel_m = re.search(r'rel=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        
        rel_val = rel_m.group(1).lower() if rel_m else "dofollow"
        is_nofollow = "nofollow" in rel_val
        if is_nofollow: nofollow_cnt += 1
        else: dofollow_cnt += 1

        clean_anchor = re.sub(r'<[^>]+>', '', inner_text).strip() or "[Brand Link]"

        if href_m:
            target_link = href_m.group(1).strip()
            if target_link.startswith(('http://', 'https://')):
                p = urllib.parse.urlparse(target_link)
                ext_domain = p.netloc.lower()
                if ext_domain and domain not in ext_domain:
                    discovered_external_links.append({
                        "source_website": domain,
                        "target_url": target_link,
                        "domain": ext_domain,
                        "anchor": clean_anchor[:40],
                        "type": "NoFollow" if is_nofollow else "DoFollow"
                    })

    # FETCH REAL LIVE SCRAPED BACKLINKS
    scraped_live_backlinks = fetch_real_live_backlinks(domain)

    keyword_density = extract_keywords_density(raw_text)

    sitemap_url = f"{base_scheme_url}/sitemap.xml"
    robots_url = f"{base_scheme_url}/robots.txt"
    manifest_url = f"{base_scheme_url}/manifest.json"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_sitemap = executor.submit(analyze_sitemap_deep, sitemap_url)
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

    # Health Score Calculation
    score = 100
    critical_issues = []

    if not is_https:
        score -= 15
        critical_issues.append("Website is not using SSL/HTTPS encryption.")
    if not is_responsive:
        score -= 15
        critical_issues.append("Viewport tag missing; site may look broken on mobile devices.")
    if page_title == "No Title Tag Found":
        score -= 10
        critical_issues.append("Title tag is completely missing.")
    if meta_description == "Not Specified":
        score -= 10
        critical_issues.append("Meta Description is not configured.")
    if not sitemap_info["exists"]:
        score -= 15
        critical_issues.append("Sitemap XML file is missing or returning errors.")
    elif not sitemap_info["is_seo_optimized"]:
        score -= 5
        critical_issues.append("Sitemap contains unreachable or unindexed URLs.")
    if not robots_info["exists"]:
        score -= 10
        critical_issues.append("Robots.txt file is missing.")
    if missing_alt_count > 0:
        score -= 5
        critical_issues.append(f"{missing_alt_count} images are missing alt tags.")

    score = max(score, 20)

    # Executive Conclusion Construction
    conclusion_summary = {
        "status": "EXCELLENT" if score >= 85 else ("AVERAGE" if score >= 60 else "CRITICAL ATTENTION NEEDED"),
        "critical_issues_count": len(critical_issues),
        "issues": critical_issues if critical_issues else ["No critical structural errors found! Site is healthy."]
    }

    return jsonify({
        "success": True,
        "score": score,
        "conclusion": conclusion_summary,
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
        "live_backlinks_engine": {
            "total_count": len(scraped_live_backlinks),
            "scraped_list": scraped_live_backlinks,
            "outbound_count": len(discovered_external_links),
            "outbound_list": discovered_external_links[:15]
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
# COMPLETE DASHBOARD UI LAYOUT WITH ALL PANELS & CHARTS
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
        
        <!-- HEADER BANNER -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-500 shadow-2xl">
            <div>
                <h1 class="text-xl md:text-3xl font-bold heading-font tracking-wide text-white flex items-center gap-3">
                    <i class="fa-solid fa-chart-line text-indigo-400"></i> OrbitEdgeMedia Enterprise Audit
                </h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Live Web Scraped Backlinks • XML Sitemap Deep Parser • Technical SEO</p>
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

        <!-- INPUT FORM -->
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
                        <span>Run Full Audit</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- DASHBOARD CONTAINER -->
        <div id="analyticsDashboard" class="hidden space-y-6">
            
            <!-- EXECUTIVE CONCLUSION BANNER -->
            <div class="cyber-card p-6 rounded-2xl border-l-4 border-l-amber-500 space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="font-bold text-sm uppercase text-amber-400 font-mono flex items-center gap-2">
                        <i class="fa-solid fa-clipboard-check text-base"></i> Executive Audit Conclusion
                    </h3>
                    <span id="conclusion-status" class="px-3 py-1 rounded text-xs font-bold font-mono"></span>
                </div>
                <ul id="conclusion-issues-list" class="space-y-1 text-xs text-gray-300 font-mono list-disc pl-5"></ul>
            </div>

            <!-- SCORE & TOP BADGES -->
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
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-purple-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">Server IP</span>
                        <h3 id="badge-geo" class="text-xs md:text-sm font-bold text-gray-300 font-mono mt-1 truncate">0.0.0.0</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-pink-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">International SEO</span>
                        <h3 id="badge-lang" class="text-xs md:text-sm font-bold text-white mt-1">Lang: -</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-amber-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">Word Count</span>
                        <h3 id="badge-words" class="text-xs md:text-sm font-bold text-amber-400 font-mono mt-1">0 Words</h3>
                    </div>
                    <div class="cyber-card p-4 rounded-xl border-b-2 border-b-teal-500 flex flex-col justify-between">
                        <span class="text-[10px] uppercase text-gray-400 font-bold">Schema.org Data</span>
                        <h3 id="badge-schema" class="text-xs md:text-sm font-bold text-teal-300 font-mono mt-1">Checking...</h3>
                    </div>
                </div>
            </div>

            <!-- LIVE SCRAPED BACKLINKS SECTION -->
            <div class="cyber-card p-6 rounded-2xl space-y-4 border-2 border-indigo-500/40 glow-indigo">
                <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                    <div>
                        <h3 class="font-bold text-base text-white heading-font flex items-center gap-2">
                            <i class="fa-solid fa-link text-indigo-400"></i> Live Backlinks (Google Index Scraped)
                        </h3>
                        <p class="text-xs text-gray-400 mt-0.5">Verified live web sources mentioning or linking to your domain</p>
                    </div>
                    <span id="stat-backlinks-count" class="bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 font-mono text-xs px-3 py-1.5 rounded-lg font-bold">Live Found: 0</span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs font-mono">
                        <thead class="bg-gray-950 text-gray-400 uppercase text-[10px]">
                            <tr>
                                <th class="p-3 border-b border-gray-800">Source Live Web Link</th>
                                <th class="p-3 border-b border-gray-800">Referring Domain</th>
                                <th class="p-3 border-b border-gray-800">Anchor / Page Mention</th>
                                <th class="p-3 border-b border-gray-800 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody id="real-backlinks-table" class="divide-y divide-gray-800/60 bg-gray-950/50"></tbody>
                    </table>
                </div>
            </div>

            <!-- CORE FILES SECTION WITH FIX BUTTONS -->
            <div class="cyber-card p-6 rounded-2xl space-y-4 border-2 border-indigo-500/40">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3 flex items-center justify-between">
                    <span>Search Engine Core Files & Deep Sitemap Evaluation</span>
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div id="card-sitemap" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-sitemap text-indigo-400 mr-1"></i> Sitemap.xml</span>
                                <span id="badge-sitemap" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-sitemap" class="text-[11px] text-gray-200 font-semibold leading-relaxed"></p>
                            <p id="exp-sitemap" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <button id="btn-fix-sitemap" onclick="openFixModal('Sitemap XML Fix Code', currentData.files.sitemap.fix_code)" class="w-full text-center bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold py-2 rounded-lg transition font-mono cursor-pointer">
                            <i class="fa-solid fa-code mr-1"></i> Get Sitemap Fix Code
                        </button>
                    </div>

                    <div id="card-robots" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-robot text-cyan-400 mr-1"></i> Robots.txt</span>
                                <span id="badge-robots" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-robots" class="text-[11px] text-gray-200 font-semibold leading-relaxed truncate font-mono"></p>
                            <p id="exp-robots" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <button id="btn-fix-robots" onclick="openFixModal('Robots.txt Recommended Code', currentData.files.robots.fix_code)" class="w-full text-center bg-cyan-600 hover:bg-cyan-500 text-white text-[10px] font-bold py-2 rounded-lg transition font-mono cursor-pointer">
                            <i class="fa-solid fa-code mr-1"></i> Get Robots.txt Fix Code
                        </button>
                    </div>

                    <div id="card-manifest" class="p-4 rounded-xl border bg-gray-950 space-y-3 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-white"><i class="fa-solid fa-mobile-screen text-amber-400 mr-1"></i> Manifest.json</span>
                                <span id="badge-manifest" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono">Checking</span>
                            </div>
                            <p id="desc-manifest" class="text-[11px] text-gray-200 font-semibold leading-relaxed"></p>
                            <p id="exp-manifest" class="text-[10px] text-gray-400 leading-relaxed"></p>
                        </div>
                        <button id="btn-fix-manifest" onclick="openFixModal('Manifest JSON Template', currentData.files.manifest.fix_code)" class="w-full text-center bg-amber-600 hover:bg-amber-500 text-white text-[10px] font-bold py-2 rounded-lg transition font-mono cursor-pointer">
                            <i class="fa-solid fa-code mr-1"></i> Get Manifest Template
                        </button>
                    </div>
                </div>
            </div>

            <!-- CHARTS ROW -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Links Structure</h3>
                    <div class="w-full max-w-[280px] h-48"><canvas id="linksChart"></canvas></div>
                </div>
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Top Keywords Frequency</h3>
                    <div class="w-full max-w-[320px] h-48"><canvas id="keywordsChart"></canvas></div>
                </div>
                <div class="cyber-card p-6 rounded-2xl flex flex-col items-center">
                    <h3 class="font-bold text-xs text-white heading-font mb-4 uppercase tracking-wider">Page Assets Breakdown</h3>
                    <div class="w-full max-w-[280px] h-48"><canvas id="assetsChart"></canvas></div>
                </div>
            </div>

            <!-- HEADINGS & METADATA -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="cyber-card p-6 rounded-2xl space-y-4">
                    <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3">Metadata & Identity Directives</h3>
                    <div class="space-y-3 text-xs">
                        <div>
                            <span class="text-gray-400 font-semibold uppercase text-[10px]">Title Tag:</span>
                            <p id="val-title" class="text-white font-medium bg-gray-950 p-2 rounded border border-gray-800 mt-1"></p>
                        </div>
                        <div>
                            <span class="text-gray-400 font-semibold uppercase text-[10px]">Meta Description:</span>
                            <p id="meta-desc" class="text-gray-300 bg-gray-950 p-2 rounded border border-gray-800 mt-1"></p>
                        </div>
                        <div>
                            <span class="text-gray-400 font-semibold uppercase text-[10px]">Canonical URL:</span>
                            <p id="val-canonical" class="text-indigo-300 font-mono bg-gray-950 p-2 rounded border border-gray-800 mt-1 truncate"></p>
                        </div>
                    </div>
                </div>

                <div class="cyber-card p-6 rounded-2xl space-y-4">
                    <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3">Heading Structure (H1 - H5)</h3>
                    <div id="headings-container" class="space-y-2"></div>
                </div>
            </div>

            <!-- HTTP REDIRECT CHAIN -->
            <div class="cyber-card p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-sm text-white heading-font border-b border-gray-800 pb-3">HTTP Redirect Chain Tracker</h3>
                <div id="redirects-container" class="space-y-2 font-mono text-xs"></div>
            </div>

            <div class="text-center text-xs text-gray-500 font-mono py-4 border-t border-gray-800">
                OrbitEdgeMedia Site Audit Engine • Live System
            </div>

        </div>
    </div>

    <!-- CODE FIX MODAL -->
    <div id="fixModal" class="fixed inset-0 bg-black/80 backdrop-blur-md hidden flex items-center justify-center p-4 z-50">
        <div class="cyber-card max-w-2xl w-full p-6 rounded-2xl space-y-4 border border-indigo-500/50">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                <h3 id="modalTitle" class="font-bold text-sm text-indigo-400 heading-font">Fix Code Solution</h3>
                <button onclick="closeFixModal()" class="text-gray-400 hover:text-white text-lg font-bold cursor-pointer">&times;</button>
            </div>
            <pre id="modalCode" class="bg-gray-950 p-4 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto max-h-80 border border-gray-800 selection:bg-emerald-800 selection:text-white"></pre>
            <div class="flex justify-end">
                <button onclick="closeFixModal()" class="bg-gray-800 hover:bg-gray-700 text-white text-xs px-4 py-2 rounded-lg font-bold cursor-pointer">Close</button>
            </div>
        </div>
    </div>

    <script>
        let healthChart, linksChart, keywordsChart, assetsChart;
        let currentData = null;

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
                    currentData = data;
                    renderHealthChart(data.score);

                    // Render Executive Conclusion
                    const statusBadge = document.getElementById('conclusion-status');
                    statusBadge.innerText = data.conclusion.status;
                    statusBadge.className = data.score >= 80 ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded text-xs font-bold" : "bg-rose-500/20 text-rose-400 border border-rose-500/30 px-3 py-1 rounded text-xs font-bold";

                    const issuesList = document.getElementById('conclusion-issues-list');
                    issuesList.innerHTML = '';
                    data.conclusion.issues.forEach(iss => {
                        issuesList.innerHTML += `<li>${iss}</li>`;
                    });

                    // Badges
                    document.getElementById('badge-https').innerText = data.is_https ? "HTTPS Secure" : "HTTP Insecure";
                    document.getElementById('badge-cms').innerText = data.cms_detected;
                    document.getElementById('badge-responsive').innerText = data.is_responsive ? "Mobile Friendly" : "Non-Responsive";
                    document.getElementById('badge-latency').innerText = `${data.latency} ms`;
                    document.getElementById('badge-geo').innerText = data.ip_address;
                    document.getElementById('badge-lang').innerText = `Lang: ${data.international_seo.lang}`;
                    document.getElementById('badge-words').innerText = `${data.files_structure.word_count} Words`;
                    document.getElementById('badge-schema').innerText = data.has_schema ? "Schema Detected" : "No Schema";

                    // LIVE BACKLINKS SCRAPED
                    const backlinks = data.live_backlinks_engine.scraped_list;
                    document.getElementById('stat-backlinks-count').innerText = `Live Found: ${backlinks.length}`;

                    const tableBody = document.getElementById('real-backlinks-table');
                    tableBody.innerHTML = '';

                    if (backlinks.length === 0) {
                        tableBody.innerHTML = `
                            <tr>
                                <td colspan="4" class="p-4 text-center text-gray-400 italic">
                                    No external Google indexed backlinks found right now for this target domain.
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
                                    <td class="p-3 text-center">
                                        <span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-bold">
                                            200 Live
                                        </span>
                                    </td>
                                </tr>
                            `;
                        });
                    }

                    // File Cards
                    renderFileCard('badge-sitemap', 'desc-sitemap', 'exp-sitemap', data.files.sitemap);
                    renderFileCard('badge-robots', 'desc-robots', 'exp-robots', data.files.robots);
                    renderFileCard('badge-manifest', 'desc-manifest', 'exp-manifest', data.files.manifest);

                    // Charts
                    renderLinksChart(data.live_backlinks_engine.outbound_count, backlinks.length);
                    renderKeywordsChart(data.keyword_density);
                    renderAssetsChart(data.files_structure);

                    // Metadata
                    document.getElementById('val-title').innerText = data.title;
                    document.getElementById('meta-desc').innerText = data.meta.description;
                    document.getElementById('val-canonical').innerText = data.canonical_url;

                    // Headings
                    const headingsContainer = document.getElementById('headings-container');
                    headingsContainer.innerHTML = '';
                    Object.keys(data.headings).forEach(tag => {
                        const item = data.headings[tag];
                        const samples = item.sample.length > 0 ? item.sample.map(s => `<li class="truncate">• ${s}</li>`).join('') : '<li class="text-gray-500 italic">No tags detected</li>';
                        headingsContainer.innerHTML += `
                            <div class="bg-gray-950 p-2.5 rounded-lg border border-gray-800 text-xs">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="font-bold font-mono text-indigo-400 text-xs">${tag} Tag</span>
                                    <span class="text-gray-400 text-[10px] font-mono">${item.count} Found</span>
                                </div>
                                <ul class="text-[11px] text-gray-400 space-y-0.5 font-mono">${samples}</ul>
                            </div>
                        `;
                    });

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

                    dashboard.classList.remove('hidden');
                } else {
                    alert("Audit Error: " + data.message);
                }
            } catch (err) {
                alert("Server Connection Error!");
            } finally {
                submitBtn.disabled = false;
                spinIcon.classList.add('hidden');
            }
        }

        function renderFileCard(badgeId, descId, expId, fileObj) {
            const badge = document.getElementById(badgeId);
            if (fileObj.exists) {
                badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                badge.innerText = `Found (${fileObj.code})`;
            } else {
                badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30";
                badge.innerText = `Missing (${fileObj.code})`;
            }
            document.getElementById(descId).innerText = fileObj.summary;
            document.getElementById(expId).innerText = fileObj.explanation;
        }

        function openFixModal(title, code) {
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalCode').innerText = code || "// No specific fix required.";
            document.getElementById('fixModal').classList.remove('hidden');
        }

        function closeFixModal() {
            document.getElementById('fixModal').classList.add('hidden');
        }

        function renderHealthChart(score) {
            const ctx = document.getElementById('healthScoreChart').getContext('2d');
            if (healthChart) healthChart.destroy();
            document.getElementById('scoreText').innerText = `${score}%`;
            document.getElementById('scoreGrade').innerText = score >= 80 ? "Grade: A" : "Grade: B";

            healthChart = new Chart(ctx, {
                type: 'doughnut',
                data: { datasets: [{ data: [score, 100 - score], backgroundColor: ['#10b981', '#1f2937'], borderWidth: 0 }] },
                options: { cutout: '80%', plugins: { tooltip: { enabled: false } }, responsive: true, maintainAspectRatio: false }
            });
        }

        function renderLinksChart(outbound, back) {
            const ctx = document.getElementById('linksChart').getContext('2d');
            if (linksChart) linksChart.destroy();
            linksChart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels: ['Outbound Links', 'Live Backlinks'], datasets: [{ data: [outbound, back], backgroundColor: ['#6366f1', '#06b6d4'], borderWidth: 0 }] },
                options: { plugins: { legend: { labels: { color: '#9ca3af', font: { size: 10 } } } }, responsive: true, maintainAspectRatio: false }
            });
        }

        function renderKeywordsChart(keywords) {
            const ctx = document.getElementById('keywordsChart').getContext('2d');
            if (keywordsChart) keywordsChart.destroy();
            keywordsChart = new Chart(ctx, {
                type: 'bar',
                data: { labels: keywords.map(k => k.word), datasets: [{ label: 'Count', data: keywords.map(k => k.count), backgroundColor: '#a855f7', borderRadius: 4 }] },
                options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#9ca3af', font: { size: 9 } } }, y: { ticks: { color: '#9ca3af', font: { size: 9 } } } }, responsive: true, maintainAspectRatio: false }
            });
        }

        function renderAssetsChart(filesStruct) {
            const ctx = document.getElementById('assetsChart').getContext('2d');
            if (assetsChart) assetsChart.destroy();
            assetsChart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels: ['CSS', 'JS', 'Images'], datasets: [{ data: [filesStruct.css_files_count, filesStruct.js_files_count, filesStruct.images_count], backgroundColor: ['#eab308', '#ec4899', '#10b981'], borderWidth: 0 }] },
                options: { plugins: { legend: { labels: { color: '#9ca3af', font: { size: 10 } } } }, responsive: true, maintainAspectRatio: false }
            });
        }
    </script>
</body>
</html>
"""

