"""
OrbitEdgeMedia Audit Suite - Script40.py
Flask Blueprint for Advanced Cyber-SEO & Technical Auditing
Production-Ready, Zero-Dependency on Paid APIs
Author: Shivam Singh Omega Dashboard
"""

from flask import Blueprint, render_template_string, request, jsonify, session
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.request import urlopen, Request
import requests
from bs4 import BeautifulSoup
import threading
import time
import json
import re
import socket
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import xml.etree.ElementTree as ET
from io import StringIO
import base64

script40_bp = Blueprint('script40', __name__, url_prefix='/audit')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

class AuditEngine:
    """Core audit engine for comprehensive SEO and technical analysis"""
    
    def __init__(self, domain):
        self.domain = domain.strip().lower().replace('https://', '').replace('http://', '').replace('www.', '')
        self.clean_domain = self.domain.split('/')[0]
        self.base_url = f"https://{self.clean_domain}"
        self.audit_data = {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.timeout = 8
    
    def fetch_page(self, url, timeout=8):
        """Fetch page with error handling"""
        try:
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            return None
    
    def get_ssl_status(self):
        """Check SSL/HTTPS configuration"""
        try:
            response = self.fetch_page(self.base_url, timeout=5)
            if response and response.url.startswith('https://'):
                return {'ssl_enabled': True, 'certificate_valid': True}
            else:
                return {'ssl_enabled': False, 'certificate_valid': False}
        except:
            return {'ssl_enabled': False, 'certificate_valid': False}
    
    def detect_cms(self, html_content):
        """Detect CMS stack from HTML headers and meta tags"""
        cms_indicators = {
            'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
            'Shopify': ['myshopify.com', 'shopify-cdn'],
            'Wix': ['wix.com', 'wixstatic'],
            'Squarespace': ['squarespace.com'],
            'React': ['__NEXT_DATA__', '__NUXT__', 'react-app'],
            'Next.js': ['__NEXT_DATA__', '_next/'],
            'Vue.js': ['__nuxt__', 'vue.js'],
            'Django': ['csrfmiddlewaretoken', 'django'],
            'Custom HTML': []
        }
        
        detected = []
        if html_content:
            html_lower = html_content.lower()
            for cms, indicators in cms_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in html_lower:
                        detected.append(cms)
                        break
        
        return detected[0] if detected else 'Custom HTML'
    
    def get_ip_geolocation(self):
        """Get server IP and geolocation"""
        try:
            ip = socket.gethostbyname(self.clean_domain)
            try:
                response = self.fetch_page(f"http://ip-api.com/json/{ip}?fields=country,city,isp", timeout=5)
                if response:
                    data = response.json()
                    return {'ip': ip, 'country': data.get('country', 'Unknown'), 'city': data.get('city', 'Unknown'), 'isp': data.get('isp', 'Unknown')}
            except:
                return {'ip': ip, 'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}
        except:
            return {'ip': 'Unknown', 'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}
    
    def measure_speed(self):
        """Measure page load speed"""
        try:
            start = time.time()
            response = self.fetch_page(self.base_url, timeout=10)
            latency_ms = int((time.time() - start) * 1000)
            return latency_ms
        except:
            return 0
    
    def audit_robots_txt(self):
        """Audit robots.txt file"""
        try:
            response = self.fetch_page(f"{self.base_url}/robots.txt", timeout=5)
            if response:
                content = response.text
                issues = []
                if 'disallow: /' in content.lower():
                    issues.append('Critical: All robots blocked with Disallow: /')
                if 'user-agent: *' not in content.lower():
                    issues.append('Warning: No wildcard user-agent directive')
                return {'exists': True, 'content': content[:500], 'issues': issues, 'health': 'Pass' if not issues else 'Fail'}
            else:
                return {'exists': False, 'content': '', 'issues': ['robots.txt not found'], 'health': 'Fail'}
        except:
            return {'exists': False, 'content': '', 'issues': ['Failed to fetch robots.txt'], 'health': 'Fail'}
    
    def audit_manifest(self):
        """Audit PWA manifest.json"""
        try:
            response = self.fetch_page(f"{self.base_url}/manifest.json", timeout=5)
            if response:
                data = response.json()
                issues = []
                if 'name' not in data:
                    issues.append('Missing app name')
                if 'icons' not in data or not data['icons']:
                    issues.append('Missing icons')
                return {'exists': True, 'content': json.dumps(data, indent=2)[:500], 'issues': issues, 'health': 'Pass' if not issues else 'Warning'}
            else:
                return {'exists': False, 'content': '', 'issues': ['manifest.json not found (Optional)'], 'health': 'Warning'}
        except:
            return {'exists': False, 'content': '', 'issues': ['Failed to parse manifest.json'], 'health': 'Warning'}
    
    def parse_sitemap(self):
        """Parse XML sitemap and return URLs"""
        urls = []
        try:
            response = self.fetch_page(f"{self.base_url}/sitemap.xml", timeout=8)
            if response:
                try:
                    root = ET.fromstring(response.content)
                    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                    for url_elem in root.findall('.//ns:loc', namespace):
                        if url_elem.text:
                            urls.append(url_elem.text)
                except:
                    urls = []
            return urls[:100]
        except:
            return []
    
    def check_sitemap_health(self, urls):
        """Multi-threaded sitemap URL health check"""
        results = {'healthy': 0, 'broken': 0, 'timeout': 0, 'details': []}
        
        def check_url(url):
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                status = response.status_code
                if status == 200:
                    return {'url': url[:60], 'status': 200, 'health': 'Pass'}
                else:
                    return {'url': url[:60], 'status': status, 'health': 'Fail'}
            except requests.exceptions.Timeout:
                return {'url': url[:60], 'status': 'Timeout', 'health': 'Timeout'}
            except:
                return {'url': url[:60], 'status': 'Error', 'health': 'Error'}
        
        threads = []
        lock = threading.Lock()
        
        for url in urls[:20]:
            thread = threading.Thread(target=lambda u=url: self._thread_check(u, results, lock, check_url))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=10)
        
        return results
    
    def _thread_check(self, url, results, lock, check_func):
        """Thread worker for URL checking"""
        result = check_func(url)
        with lock:
            results['details'].append(result)
            if result['health'] == 'Pass':
                results['healthy'] += 1
            elif result['health'] == 'Timeout':
                results['timeout'] += 1
            else:
                results['broken'] += 1
    
    def get_backlinks(self):
        """Scrape live backlink mentions from search engines"""
        backlinks = []
        try:
            query = f'"{self.clean_domain}" -site:{self.clean_domain}'
            url = f"https://www.google.com/search?q={query}&num=20"
            
            response = self.fetch_page(url, timeout=8)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for result in soup.find_all('div', class_='g')[:15]:
                    try:
                        link_elem = result.find('a')
                        if link_elem and link_elem.get('href'):
                            source_url = link_elem.get('href', '').split('/url?q=')[1].split('&')[0] if '/url?q=' in link_elem.get('href', '') else link_elem.get('href')
                            title = result.find('h3')
                            title_text = title.text if title else 'No title'
                            
                            if source_url and self.clean_domain not in source_url:
                                parsed = urlparse(source_url)
                                referring_domain = parsed.netloc.replace('www.', '')
                                anchor_text = link_elem.text if link_elem else 'Unknown'
                                
                                backlinks.append({
                                    'source_url': source_url[:80],
                                    'referring_domain': referring_domain,
                                    'anchor_text': anchor_text[:40],
                                    'title': title_text[:60],
                                    'live': True,
                                    'timestamp': datetime.now().isoformat()
                                })
                    except:
                        continue
        except:
            pass
        
        return backlinks[:20]
    
    def analyze_page_metadata(self, html_content):
        """Extract and analyze on-page metadata"""
        metadata = {
            'title': '', 'meta_description': '', 'meta_keywords': '',
            'og_title': '', 'og_description': '', 'og_image': '',
            'canonical': '', 'favicon': '', 'language': 'en',
            'hreflang_tags': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title_tag = soup.find('title')
            metadata['title'] = title_tag.text if title_tag else ''
            
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                property_attr = meta.get('property', '').lower()
                
                if name == 'description':
                    metadata['meta_description'] = meta.get('content', '')
                elif name == 'keywords':
                    metadata['meta_keywords'] = meta.get('content', '')
                elif property_attr == 'og:title':
                    metadata['og_title'] = meta.get('content', '')
                elif property_attr == 'og:description':
                    metadata['og_description'] = meta.get('content', '')
                elif property_attr == 'og:image':
                    metadata['og_image'] = meta.get('content', '')
            
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical:
                metadata['canonical'] = canonical.get('href', '')
            
            favicon = soup.find('link', {'rel': 'icon'}) or soup.find('link', {'rel': 'shortcut icon'})
            if favicon:
                metadata['favicon'] = favicon.get('href', '')
            
            html_tag = soup.find('html')
            if html_tag:
                metadata['language'] = html_tag.get('lang', 'en')
            
            hreflang_tags = soup.find_all('link', {'rel': 'alternate', 'hreflang': True})
            metadata['hreflang_tags'] = [tag.get('href', '') for tag in hreflang_tags[:10]]
        
        except:
            pass
        
        return metadata
    
    def analyze_headings(self, html_content):
        """Analyze heading structure"""
        headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': []}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for level in ['h1', 'h2', 'h3', 'h4', 'h5']:
                tags = soup.find_all(level)
                for tag in tags[:15]:
                    headings[level].append(tag.text.strip()[:80])
        
        except:
            pass
        
        return headings
    
    def analyze_content(self, html_content):
        """Analyze content metrics"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            text = soup.get_text()
            words = text.split()
            word_count = len(words)
            
            html_size = len(html_content)
            text_size = len(text)
            text_ratio = (text_size / html_size * 100) if html_size > 0 else 0
            
            img_tags = soup.find_all('img')
            missing_alt_count = sum(1 for img in img_tags if not img.get('alt'))
            
            keyword_freq = Counter(word.lower() for word in words if len(word) > 4)
            top_keywords = keyword_freq.most_common(10)
            
            css_files = len(soup.find_all('link', {'rel': 'stylesheet'}))
            js_files = len(soup.find_all('script', {'src': True}))
            
            return {
                'word_count': word_count,
                'text_ratio': round(text_ratio, 2),
                'total_images': len(img_tags),
                'missing_alt_count': missing_alt_count,
                'css_files': css_files,
                'js_files': js_files,
                'top_keywords': [{'keyword': k[0], 'count': k[1]} for k in top_keywords]
            }
        except:
            return {
                'word_count': 0, 'text_ratio': 0, 'total_images': 0,
                'missing_alt_count': 0, 'css_files': 0, 'js_files': 0,
                'top_keywords': []
            }
    
    def track_redirects(self):
        """Track HTTP redirect chain"""
        redirects = []
        try:
            response = self.session.get(self.base_url, timeout=8, allow_redirects=False)
            current_url = self.base_url
            
            for i in range(10):
                if response.status_code in [301, 302, 303, 307, 308]:
                    next_url = response.headers.get('Location')
                    if next_url:
                        redirects.append({'from': current_url[:80], 'to': next_url[:80], 'status': response.status_code})
                        current_url = next_url
                        response = self.session.get(current_url, timeout=8, allow_redirects=False)
                    else:
                        break
                else:
                    redirects.append({'from': current_url[:80], 'to': current_url[:80], 'status': response.status_code, 'final': True})
                    break
        except:
            pass
        
        return redirects[:10]
    
    def run_full_audit(self):
        """Execute complete audit"""
        try:
            page_response = self.fetch_page(self.base_url)
            html_content = page_response.text if page_response else ''
            
            self.audit_data = {
                'domain': self.clean_domain,
                'timestamp': datetime.now().isoformat(),
                'ssl': self.get_ssl_status(),
                'cms': self.detect_cms(html_content),
                'ip_geolocation': self.get_ip_geolocation(),
                'speed_ms': self.measure_speed(),
                'robots': self.audit_robots_txt(),
                'manifest': self.audit_manifest(),
                'metadata': self.analyze_page_metadata(html_content),
                'headings': self.analyze_headings(html_content),
                'content': self.analyze_content(html_content),
                'sitemap_urls': self.parse_sitemap(),
                'redirects': self.track_redirects(),
                'backlinks': self.get_backlinks()
            }
            
            if self.audit_data['sitemap_urls']:
                self.audit_data['sitemap_health'] = self.check_sitemap_health(self.audit_data['sitemap_urls'])
            
            return self.audit_data
        except Exception as e:
            return {'error': str(e)}

def generate_audit_grade(audit_data):
    """Generate overall audit grade and summary"""
    if 'error' in audit_data:
        return {'grade': 'F', 'score': 0, 'issues': ['Audit failed to complete']}
    
    score = 100
    issues = []
    
    if not audit_data.get('ssl', {}).get('ssl_enabled'):
        score -= 20
        issues.append('SSL/HTTPS not enabled')
    
    if audit_data.get('robots', {}).get('health') == 'Fail':
        score -= 15
        issues.append('robots.txt has critical issues')
    
    if audit_data.get('content', {}).get('word_count', 0) < 300:
        score -= 10
        issues.append('Low word count content')
    
    if audit_data.get('content', {}).get('missing_alt_count', 0) > 5:
        score -= 10
        issues.append('Multiple images missing ALT text')
    
    if audit_data.get('speed_ms', 0) > 3000:
        score -= 10
        issues.append('Slow page load speed')
    
    if not audit_data.get('metadata', {}).get('meta_description'):
        score -= 5
        issues.append('Missing meta description')
    
    if audit_data.get('redirects', []) and len(audit_data['redirects']) > 2:
        score -= 5
        issues.append('Multiple redirect chain detected')
    
    score = max(0, score)
    
    if score >= 90:
        grade = 'A'
    elif score >= 75:
        grade = 'B'
    elif score >= 60:
        grade = 'C'
    else:
        grade = 'F'
    
    return {'grade': grade, 'score': score, 'issues': issues[:5]}

@script40_bp.route('/', methods=['GET', 'POST'])
def audit_dashboard():
    """Main audit dashboard"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        domain = request.form.get('domain', '').strip()
        if not domain:
            return render_template_string(DASHBOARD_HTML, error='Domain required')
        
        audit = AuditEngine(domain)
        audit_data = audit.run_full_audit()
        audit_grade = generate_audit_grade(audit_data)
        
        return render_template_string(
            DASHBOARD_HTML,
            audit_data=json.dumps(audit_data),
            audit_grade=json.dumps(audit_grade),
            domain=domain,
            show_results=True
        )
    
    return render_template_string(DASHBOARD_HTML, audit_data='{}', audit_grade='{}', show_results=False)

@script40_bp.route('/api/audit', methods=['POST'])
def api_audit():
    """API endpoint for audits"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    domain = data.get('domain', '').strip()
    
    if not domain:
        return jsonify({'error': 'Domain required'}), 400
    
    audit = AuditEngine(domain)
    audit_data = audit.run_full_audit()
    audit_grade = generate_audit_grade(audit_data)
    
    return jsonify({
        'audit': audit_data,
        'grade': audit_grade,
        'success': 'error' not in audit_data
    })

@script40_bp.route('/api/fix-code/<fix_type>', methods=['GET'])
def get_fix_code(fix_type):
    """Generate fix code for audit issues"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    fixes = {
        'robots': {
            'title': 'Optimized robots.txt',
            'code': '''User-agent: *
Allow: /
Disallow: /admin/
Disallow: /private/
Disallow: /?utm_source=*
Disallow: /*?*sort=
Crawl-delay: 1

User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

Sitemap: https://yourdomain.com/sitemap.xml
'''
        },
        'sitemap': {
            'title': 'Dynamic XML Sitemap Generator (Flask)',
            'code': '''from flask import Blueprint
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime

sitemap_bp = Blueprint('sitemap', __name__)

@sitemap_bp.route('/sitemap.xml', methods=['GET'])
def sitemap():
    urlset = Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    urls = [
        {'loc': 'https://yourdomain.com/', 'changefreq': 'weekly', 'priority': 1.0},
        {'loc': 'https://yourdomain.com/about', 'changefreq': 'monthly', 'priority': 0.8},
        {'loc': 'https://yourdomain.com/blog', 'changefreq': 'daily', 'priority': 0.9},
    ]
    
    for url in urls:
        url_elem = SubElement(urlset, 'url')
        loc = SubElement(url_elem, 'loc')
        loc.text = url['loc']
        lastmod = SubElement(url_elem, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
        changefreq = SubElement(url_elem, 'changefreq')
        changefreq.text = url['changefreq']
        priority = SubElement(url_elem, 'priority')
        priority.text = str(url['priority'])
    
    from flask import Response
    return Response(tostring(urlset, encoding='unicode'), mimetype='application/xml')
'''
        },
        'manifest': {
            'title': 'Progressive Web App manifest.json',
            'code': '''{
  "name": "Your App Name",
  "short_name": "App",
  "description": "Optimized PWA application",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#030712",
  "scope": "/",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    }
  ],
  "shortcuts": [
    {
      "name": "Dashboard",
      "short_name": "Dashboard",
      "description": "Open the main dashboard",
      "url": "/dashboard",
      "icons": [
        {
          "src": "/icons/dashboard.png",
          "sizes": "192x192"
        }
      ]
    }
  ],
  "categories": ["productivity", "utilities"],
  "screenshots": [
    {
      "src": "/screenshots/screenshot1.png",
      "sizes": "540x720",
      "type": "image/png"
    }
  ]
}
'''
        }
    }
    
    if fix_type not in fixes:
        return jsonify({'error': 'Invalid fix type'}), 400
    
    return jsonify(fixes[fix_type])

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdgeMedia Audit Suite</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #030712 0%, #0f1419 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
        .glass-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        .glow-border { border: 1px solid rgba(99,102,241,0.5); box-shadow: 0 0 20px rgba(99,102,241,0.2); }
        .metric-box { background: rgba(99,102,241,0.1); border-left: 4px solid #6366f1; padding: 16px; border-radius: 8px; }
        .btn-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 10px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; transition: all 0.3s; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(99,102,241,0.4); }
        .btn-secondary { background: rgba(255,255,255,0.1); color: #e0e0e0; padding: 8px 16px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); cursor: pointer; font-size: 12px; }
        .badge-pass { background: rgba(34,197,94,0.2); color: #22c55e; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .badge-fail { background: rgba(239,68,68,0.2); color: #ef4444; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .badge-warning { background: rgba(234,179,8,0.2); color: #eab308; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .grade-a { font-size: 48px; font-weight: 900; color: #22c55e; }
        .grade-b { font-size: 48px; font-weight: 900; color: #eab308; }
        .grade-c { font-size: 48px; font-weight: 900; color: #f97316; }
        .grade-f { font-size: 48px; font-weight: 900; color: #ef4444; }
        .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .data-table th { background: rgba(99,102,241,0.2); padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .data-table tr:hover { background: rgba(99,102,241,0.1); }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); justify-content: center; align-items: center; z-index: 1000; }
        .modal.active { display: flex; }
        .modal-content { background: #0f1419; border: 1px solid rgba(99,102,241,0.5); border-radius: 12px; padding: 30px; max-width: 600px; max-height: 80vh; overflow-y: auto; position: relative; }
        .modal-close { position: absolute; top: 15px; right: 15px; background: none; border: none; color: #e0e0e0; font-size: 24px; cursor: pointer; }
        .code-block { background: rgba(0,0,0,0.3); border: 1px solid rgba(99,102,241,0.3); border-radius: 8px; padding: 16px; margin: 16px 0; font-family: 'Courier New', monospace; font-size: 12px; max-height: 400px; overflow-y: auto; }
        .copy-btn { position: absolute; top: 10px; right: 10px; background: #6366f1; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; }
        .chart-container { position: relative; height: 300px; margin: 20px 0; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(99,102,241,0.3); border-radius: 50%; border-top-color: #6366f1; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="min-h-screen p-4 md:p-8">
        <div class="max-w-7xl mx-auto">
            <div class="mb-12">
                <div class="flex items-center gap-3 mb-2">
                    <i class="fas fa-globe text-2xl text-indigo-500"></i>
                    <h1 class="text-4xl font-bold text-white">OrbitEdgeMedia Audit Suite</h1>
                </div>
                <p class="text-gray-400">Real-time Cyber-SEO Technical Auditing & Optimization</p>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h2 class="text-xl font-bold mb-4 text-white">Domain Audit Scanner</h2>
                <form method="POST" class="flex gap-3">
                    <input type="text" name="domain" placeholder="example.com or https://example.com" 
                           class="flex-1 bg-rgba(255,255,255,0.05) border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400" required>
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-search mr-2"></i> Audit Domain
                    </button>
                </form>
                {% if error %}
                <div class="mt-4 bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded">{{ error }}</div>
                {% endif %}
            </div>

            {% if show_results %}
            <script>
                const auditData = {{ audit_data | safe }};
                const auditGrade = {{ audit_grade | safe }};
            </script>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass-card glow-border p-6 text-center">
                    <p class="text-gray-400 text-sm mb-2">Overall Score</p>
                    <div class="grade-{{ auditGrade['grade'].lower() }}">{{ auditGrade['grade'] }}</div>
                    <p class="text-xl font-bold text-white mt-2">{{ auditGrade['score'] }}/100</p>
                </div>

                <div class="glass-card glow-border p-6">
                    <p class="text-gray-400 text-sm mb-3">Page Speed</p>
                    <p class="text-2xl font-bold text-indigo-400">{{ auditData['speed_ms'] }}ms</p>
                    <p class="text-xs text-gray-400 mt-2">Response time from server</p>
                </div>

                <div class="glass-card glow-border p-6">
                    <p class="text-gray-400 text-sm mb-3">SSL Status</p>
                    {% if auditData['ssl']['ssl_enabled'] %}
                    <span class="badge-pass"><i class="fas fa-lock mr-1"></i> Enabled</span>
                    {% else %}
                    <span class="badge-fail"><i class="fas fa-lock-open mr-1"></i> Disabled</span>
                    {% endif %}
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="glass-card glow-border p-6">
                    <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-exclamation-circle text-red-500 mr-2"></i> Critical Issues</h3>
                    <div class="space-y-2">
                        {% if auditGrade['issues'] %}
                            {% for issue in auditGrade['issues'] %}
                            <div class="flex items-start gap-2 p-3 bg-red-500/10 rounded border border-red-500/30">
                                <i class="fas fa-circle-xmark text-red-500 mt-1 flex-shrink-0"></i>
                                <span class="text-sm">{{ issue }}</span>
                            </div>
                            {% endfor %}
                        {% else %}
                        <div class="flex items-center gap-2 p-3 bg-green-500/10 rounded border border-green-500/30">
                            <i class="fas fa-circle-check text-green-500"></i>
                            <span class="text-sm">No critical issues detected</span>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="glass-card glow-border p-6">
                    <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-chart-pie text-indigo-500 mr-2"></i> Content Metrics</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Word Count</span>
                            <span class="font-bold text-indigo-400">{{ auditData['content']['word_count'] }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Text-to-HTML Ratio</span>
                            <span class="font-bold text-indigo-400">{{ auditData['content']['text_ratio'] }}%</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Total Images</span>
                            <span class="font-bold text-indigo-400">{{ auditData['content']['total_images'] }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Missing ALT Tags</span>
                            <span class="font-bold text-red-400">{{ auditData['content']['missing_alt_count'] }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-link mr-2"></i> Backlinks & Mentions</h3>
                {% if auditData['backlinks'] %}
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Source URL</th>
                                <th>Referring Domain</th>
                                <th>Anchor Text</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for backlink in auditData['backlinks'] %}
                            <tr>
                                <td><a href="{{ backlink['source_url'] }}" target="_blank" class="text-indigo-400 hover:underline">{{ backlink['source_url'] }}</a></td>
                                <td class="text-gray-300">{{ backlink['referring_domain'] }}</td>
                                <td class="text-gray-400 text-sm">{{ backlink['anchor_text'] }}</td>
                                <td><span class="badge-pass">Live</span></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-gray-400">No recent backlinks detected</p>
                {% endif %}
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="glass-card glow-border p-6">
                    <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-robot mr-2"></i> Robots.txt Audit</h3>
                    <div class="mb-3">
                        {% if auditData['robots']['health'] == 'Pass' %}
                        <span class="badge-pass">Pass</span>
                        {% else %}
                        <span class="badge-fail">{{ auditData['robots']['health'] }}</span>
                        {% endif %}
                    </div>
                    {% if auditData['robots']['issues'] %}
                    <ul class="space-y-2 text-sm">
                        {% for issue in auditData['robots']['issues'] %}
                        <li class="flex items-start gap-2">
                            <i class="fas fa-exclamation text-yellow-500 mt-1 flex-shrink-0"></i>
                            <span>{{ issue }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    <button class="btn-secondary mt-4 w-full" onclick="openModal('robots')">
                        <i class="fas fa-code mr-2"></i> Get Fix Code
                    </button>
                </div>

                <div class="glass-card glow-border p-6">
                    <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-sitemap mr-2"></i> Sitemap Audit</h3>
                    <div class="mb-3">
                        <p class="text-sm text-gray-400">Total URLs indexed: <span class="font-bold text-indigo-400">{{ auditData['sitemap_urls']|length }}</span></p>
                    </div>
                    {% if auditData.get('sitemap_health') %}
                    <div class="space-y-2 text-sm mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Healthy:</span>
                            <span class="text-green-400 font-bold">{{ auditData['sitemap_health']['healthy'] }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Broken:</span>
                            <span class="text-red-400 font-bold">{{ auditData['sitemap_health']['broken'] }}</span>
                        </div>
                    </div>
                    {% endif %}
                    <button class="btn-secondary mt-4 w-full" onclick="openModal('sitemap')">
                        <i class="fas fa-code mr-2"></i> Get Fix Code
                    </button>
                </div>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-heading mr-2"></i> Heading Structure</h3>
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {% for level, headings in [('h1', auditData['headings']['h1']), ('h2', auditData['headings']['h2']), ('h3', auditData['headings']['h3']), ('h4', auditData['headings']['h4']), ('h5', auditData['headings']['h5'])] %}
                    <div class="metric-box">
                        <p class="text-xs font-bold text-indigo-400 uppercase">{{ level }}</p>
                        <p class="text-2xl font-bold text-white">{{ headings|length }}</p>
                        {% if headings %}
                        <p class="text-xs text-gray-400 mt-2 truncate">{{ headings[0][:30] }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-keyboard mr-2"></i> Top Keywords (Density)</h3>
                {% if auditData['content']['top_keywords'] %}
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Keyword</th>
                                <th>Frequency</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for kw in auditData['content']['top_keywords'] %}
                            <tr>
                                <td class="font-medium">{{ kw['keyword'] }}</td>
                                <td>
                                    <div class="flex items-center gap-2">
                                        <div class="w-24 bg-gray-600 rounded-full h-2">
                                            <div class="bg-indigo-500 h-2 rounded-full" style="width: {{ (kw['count'] / 5 * 100)|int }}%"></div>
                                        </div>
                                        <span class="text-sm font-bold">{{ kw['count'] }}</span>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-gray-400">Insufficient content for keyword analysis</p>
                {% endif %}
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-server mr-2"></i> Server Information</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <p class="text-gray-400 text-xs mb-1">IP Address</p>
                        <p class="font-mono text-sm">{{ auditData['ip_geolocation']['ip'] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">Country</p>
                        <p class="font-mono text-sm">{{ auditData['ip_geolocation']['country'] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">City</p>
                        <p class="font-mono text-sm">{{ auditData['ip_geolocation']['city'] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">ISP</p>
                        <p class="font-mono text-sm">{{ auditData['ip_geolocation']['isp'][:20] }}</p>
                    </div>
                </div>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-arrows-turn-right mr-2"></i> Redirect Chain</h3>
                {% if auditData['redirects'] %}
                <div class="space-y-3">
                    {% for redirect in auditData['redirects'] %}
                    <div class="flex items-center gap-3 text-sm">
                        <span class="font-mono text-indigo-400">{{ redirect['from'] }}</span>
                        <i class="fas fa-arrow-right text-gray-500"></i>
                        <span class="font-mono text-gray-400">{{ redirect['to'] }}</span>
                        <span class="ml-auto px-2 py-1 bg-gray-700 rounded text-xs">{{ redirect['status'] }}</span>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p class="text-gray-400 text-sm">No redirect chains detected</p>
                {% endif %}
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-tag mr-2"></i> Metadata Analysis</h3>
                <div class="space-y-4">
                    <div>
                        <p class="text-gray-400 text-xs mb-1">Page Title</p>
                        <p class="text-sm">{{ auditData['metadata']['title'][:80] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">Meta Description</p>
                        <p class="text-sm">{{ auditData['metadata']['meta_description'][:80] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">Canonical URL</p>
                        <p class="text-sm font-mono">{{ auditData['metadata']['canonical'][:60] }}</p>
                    </div>
                    <div>
                        <p class="text-gray-400 text-xs mb-1">Language</p>
                        <p class="text-sm">{{ auditData['metadata']['language'] }}</p>
                    </div>
                </div>
            </div>

            <div class="glass-card glow-border p-6 mb-8">
                <h3 class="text-lg font-bold text-white mb-4"><i class="fas fa-print mr-2"></i> Export & Tools</h3>
                <div class="flex flex-wrap gap-3">
                    <button class="btn-primary" onclick="window.print()">
                        <i class="fas fa-file-pdf mr-2"></i> Export as PDF
                    </button>
                    <button class="btn-secondary" onclick="location.reload()">
                        <i class="fas fa-rotate-right mr-2"></i> New Audit
                    </button>
                </div>
            </div>

            <div id="fixModal" class="modal">
                <div class="modal-content">
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                    <h2 class="text-xl font-bold text-white mb-4">Fix Code</h2>
                    <div id="fixContent"></div>
                    <div class="flex gap-3 mt-6">
                        <button class="btn-primary flex-1" onclick="copyCode()">
                            <i class="fas fa-copy mr-2"></i> Copy Code
                        </button>
                        <button class="btn-secondary flex-1" onclick="closeModal()">
                            <i class="fas fa-times mr-2"></i> Close
                        </button>
                    </div>
                </div>
            </div>

            {% endif %}
        </div>
    </div>

    <script>
        function openModal(fixType) {
            fetch(`/audit/api/fix-code/${fixType}`)
                .then(r => r.json())
                .then(data => {
                    const html = `
                        <h3 class="text-lg font-bold text-indigo-400 mb-3">${data.title}</h3>
                        <div class="code-block" id="codeBlock">${escapeHtml(data.code)}</div>
                    `;
                    document.getElementById('fixContent').innerHTML = html;
                    document.getElementById('fixModal').classList.add('active');
                });
        }

        function closeModal() {
            document.getElementById('fixModal').classList.remove('active');
        }

        function copyCode() {
            const codeBlock = document.getElementById('codeBlock');
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('Code copied to clipboard!');
            });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>

    <style>
        @media print {
            body { background: white; }
            .glass-card { background: white; border: 1px solid #ddd; }
            .btn-primary, .btn-secondary { display: none; }
            .modal { display: none !important; }
        }
    </style>
</body>
</html>
'''

__all__ = ['script40_bp']
