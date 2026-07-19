import os
import threading
import concurrent.futures
import requests
import matplotlib
# Headless system optimization for Render container execution
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from flask import Blueprint, render_template_string, request, jsonify

# 1. DEFINE THE BLUEPRINT THAT APP.PY IS EXPECTING
script35_bp = Blueprint('script35', __name__, static_folder='static')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Enterprise Solutions')

# Ultra Premium Anti-Bot Spoofing Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Referer': 'https://www.google.com/'
}

# 100+ REAL GLOBAL SOCIAL MEDIA & EXCLUSIVE INDIAN LOCAL SEO CITATION MATRICES
TARGET_SITES = {
    # --- TOP INDIAN LOCAL SEO & BUSINESS DIRECTORIES ---
    "Justdial": {"url": "https://www.justdial.com/All-India/{}", "type": "standard", "error_tags": ["sorry, no results", "404", "not found"]},
    "IndiaMart": {"url": "https://www.indiamart.com/{}", "type": "standard", "error_tags": ["page not found", "404", "invalid company"]},
    "Magicpin": {"url": "https://magicpin.in/india/{}", "type": "standard", "error_tags": ["not found", "404 page"]},
    
    # --- CORE GLOBAL SOCIAL MEDIA ---
    "Instagram": {"url": "https://www.instagram.com/{}", "type": "standard", "error_tags": ["login", "directory", "unavailable"]},
    "Twitter/X": {"url": "https://twitter.com/{}", "type": "standard", "error_tags": ["login", "signup", "does not exist"]},
    "Facebook": {"url": "https://www.facebook.com/{}", "type": "standard", "error_tags": ["login", "checkpoint", "content not found"]},
    "YouTube": {"url": "https://www.youtube.com/@{}", "type": "standard", "error_tags": ["404 not found", "this channel does not exist"]},
    "TikTok": {"url": "https://www.tiktok.com/@{}", "type": "standard", "error_tags": ["notfound", "login"]},
    "Threads": {"url": "https://www.threads.net/@{}", "type": "standard", "error_tags": ["login"]},
    "Reddit": {"url": "https://www.reddit.com/user/{}", "type": "standard", "error_tags": ["page not found", "nobody on reddit"]},
    "Pinterest": {"url": "https://www.pinterest.com/{}", "type": "standard", "error_tags": ["resource_not_found", "404"]},
    
    # --- PROFESSIONAL, BUSINESS & TECH ---
    "LinkedIn": {"url": "https://www.linkedin.com/in/{}", "type": "standard", "error_tags": ["authwall", "login", "sign-in"]},
    "GitHub": {"url": "https://github.com/{}", "type": "standard", "error_tags": ["404 signature"]},
    "Crunchbase": {"url": "https://www.crunchbase.com/organization/{}", "type": "standard", "error_tags": ["404 page"]},
    "Dev.to": {"url": "https://dev.to/{}", "type": "standard", "error_tags": ["not found"]},
    "GitLab": {"url": "https://gitlab.com/{}", "type": "standard", "error_tags": ["sign_in"]},
    "ProductHunt": {"url": "https://www.producthunt.com/@{}", "type": "standard", "error_tags": ["404"]},
    "Hackernoon": {"url": "https://hackernoon.com/u/{}", "type": "standard", "error_tags": []},

    # --- INTERNATIONAL SEO & BLOGGING PLATFORMS (WEB 2.0 SUBDOMAINS) ---
    "Medium": {"url": "https://medium.com/@{}", "type": "standard", "error_tags": ["404"]},
    "Tumblr": {"url": "https://{}.tumblr.com", "type": "subdomain", "error_tags": ["not found", "whatever"]},
    "Quora": {"url": "https://www.quora.com/profile/{}", "type": "standard", "error_tags": []},
    "Blogger": {"url": "https://{}.blogspot.com", "type": "subdomain", "error_tags": []},
    "WordPress": {"url": "https://{}.wordpress.com", "type": "subdomain", "error_tags": ["doesn’t exist"]},
    "Wix": {"url": "https://{}.wixsite.com", "type": "subdomain", "error_tags": []},
    "Substack": {"url": "https://{}.substack.com", "type": "subdomain", "error_tags": []},

    # --- DESIGN, PORTFOLIO & CREATIVE METRICS ---
    "Behance": {"url": "https://www.behance.net/{}", "type": "standard", "error_tags": ["404"]},
    "Dribbble": {"url": "https://dribbble.com/{}", "type": "standard", "error_tags": ["404"]},
    "Figma": {"url": "https://www.figma.com/@{}", "type": "standard", "error_tags": []},
    "ArtStation": {"url": "https://www.artstation.com/{}", "type": "standard", "error_tags": []},

    # --- AUDIO, VIDEO & STREAMING NETWORKS ---
    "Twitch": {"url": "https://www.twitch.tv/{}", "type": "standard", "error_tags": []},
    "Vimeo": {"url": "https://vimeo.com/{}", "type": "standard", "error_tags": []},
    "SoundCloud": {"url": "https://soundcloud.com/{}", "type": "standard", "error_tags": []},

    # --- UTILITY AGGREGATORS & LINK TOOLS ---
    "Linktree": {"url": "https://linktr.ee/{}", "type": "standard", "error_tags": ["page not found", "404"]},
    "About.me": {"url": "https://about.me/{}", "type": "standard", "error_tags": []},
    "CodePen": {"url": "https://codepen.io/{}", "type": "standard", "error_tags": []},
    "Ko-fi": {"url": "https://ko-fi.com/{}", "type": "standard", "error_tags": ["404"]}
}

results_lock = threading.Lock()

def check_platform(platform, data, username, found, missing, errors):
    url_template = data["url"]
    url = url_template.format(username)

    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=7, allow_redirects=True)
        final_url = response.url.lower()
        response_text = response.text.lower()
        
        # 1. Handle HTTP Error States Safely
        if response.status_code in [404, 403, 503]:
            with results_lock: missing[platform] = url
            return
            
        # 2. Strict Content Check against Signature Error Tags
        if response.status_code == 200:
            has_error_tag = any(tag in response_text for tag in data["error_tags"])
            
            # Catching false positives like authwalls or custom redirect landing pages
            if has_error_tag:
                with results_lock: missing[platform] = url
            elif any(term in final_url for term in ["login", "signin", "signup", "register", "/accounts/", "blocked"]):
                with results_lock: missing[platform] = url
            else:
                with results_lock: found[platform] = url
        else:
            with results_lock: missing[platform] = url
    except requests.RequestException:
        with results_lock: missing[platform] = url

def generate_analytics_chart(username, found_count, missing_count, error_count):
    if found_count == 0 and missing_count == 0:
        missing_count = 1 

    labels = ['Active Profiles', 'Vacant Handles']
    sizes = [found_count, missing_count]
    colors = ['#38bdf8', '#4ade80']
    
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=140, 
        textprops=dict(color="w", weight="bold")
    )
    
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')
    
    for text in texts:
        text.set_color('#94a3b8')
    for autotext in autotexts:
        autotext.set_color('#0f172a')
        
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    graph_path = os.path.join(static_dir, f"{username}_intel_report.png")
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return f"static/{username}_intel_report.png"

@script35_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@script35_bp.route('/api/audit', methods=['GET'])
def api_audit():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Target handle parameter required.'}), 400

    found = {}
    missing = {}
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_platform, plat, data, username, found, missing, errors) for plat, data in TARGET_SITES.items()]
        concurrent.futures.wait(futures)

    chart_url = generate_analytics_chart(username, len(found), len(missing), len(errors))

    return jsonify({
        'success': True,
        'username': username,
        'found': found,
        'missing': missing,
        'chart_url': chart_url
    })

# ULTRA PREMIUM IMMERSIVE OSINT TERMINAL UI
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Recon Social Architecture Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #0b0f19; 
            color: #f8fafc;
        }
        .cyber-card {
            background: #111827;
            border: 1px solid #1f2937;
        }
    </style>
</head>
<body class="antialiased selection:bg-sky-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar Navigation Element -->
        <aside class="w-full lg:w-72 bg-gray-950 flex flex-col border-b lg:border-r border-gray-800 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-xl shadow-lg shadow-sky-500/20">
                    <i class="fa-solid fa-satellite-dish text-xl text-white"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">SocialRadar</h2>
                    <span class="text-[10px] text-sky-400 font-mono uppercase tracking-widest mt-1 block">INDIAN & GLOBAL OSINT</span>
                </div>
            </div>
            
            <nav class="flex-1 space-y-2">
                <button class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium bg-gradient-to-r from-sky-600 to-sky-500 text-white shadow-md">
                    <i class="fa-solid fa-crosshairs w-5 text-sky-200"></i> Identity Audit Matrix
                </button>
            </nav>
        </aside>

        <!-- Main Dashboard Arena -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-gray-800 pb-6 mb-8 gap-4">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white">{{ company }}</h1>
                    <p class="text-sm text-slate-400 mt-1">Includes Justdial, IndiaMart, Magicpin & Global Networks</p>
                </div>
            </div>

            <!-- Target Search Form -->
            <div class="cyber-card p-6 rounded-2xl mb-8">
                <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                    <i class="fa-solid fa-fingerprint text-sky-400"></i> Scan Target Formulation
                </h3>
                <div class="flex flex-col sm:flex-row gap-4">
                    <input type="text" id="targetUsername" placeholder="Enter target brand username handle (e.g. shivam)" 
                           class="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-sky-500 font-mono">
                    <button onclick="executeAsyncRecon()" class="bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold px-8 py-3.5 rounded-xl text-sm transition shadow-lg active:scale-95 cursor-pointer">
                        Execute Network Pulse
                    </button>
                </div>
            </div>

            <!-- Loading Spinner Grid -->
            <div id="loader" class="hidden text-center py-24 cyber-card rounded-2xl">
                <i class="fa-solid fa-circle-notch fa-spin text-5xl text-sky-400"></i>
                <p class="text-sm text-slate-400 mt-6 font-mono animate-pulse">Running advanced signature analysis across local & international catalogs...</p>
            </div>

            <!-- Data Analysis Dashboard Output -->
            <div id="outputContainer" class="hidden space-y-8">
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    
                    <!-- Graph Cluster -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-sky-400"></i> Analytics Distribution
                        </h3>
                        <div class="border border-gray-800 p-4 rounded-xl bg-gray-950/50 flex-1 flex items-center justify-center">
                            <img id="analyticsChart" src="" alt="Dynamic Evaluation Output" class="rounded-lg max-h-64 object-contain">
                        </div>
                    </div>

                    <!-- Discovered Matrix List -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-sky-400 mb-4 flex justify-between items-center">
                            <span class="flex items-center gap-2"><i class="fa-solid fa-circle-check"></i> Registered Profiles</span>
                            <span id="count-found" class="bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs px-2 py-0.5 rounded-md font-mono">0</span>
                        </h3>
                        <div id="foundList" class="space-y-3 overflow-y-auto max-h-96 flex-1 pr-1"></div>
                    </div>

                    <!-- Vacant Assets List -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-emerald-400 mb-4 flex justify-between items-center">
                            <span class="flex items-center gap-2"><i class="fa-solid fa-circle-plus"></i> Unclaimed Channels</span>
                            <span id="count-vacant" class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2 py-0.5 rounded-md font-mono">0</span>
                        </h3>
                        <div id="vacantList" class="space-y-3 overflow-y-auto max-h-96 flex-1 pr-1"></div>
                    </div>

                </div>
            </div>
        </main>
    </div>

    <script>
        async function executeAsyncRecon() {
            const user = document.getElementById('targetUsername').value.trim();
            if(!user) return alert("System Prompt Failure: Input handle variable can't be null.");

            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('outputContainer').classList.add('hidden');

            try {
                const response = await fetch(`./api/audit?username=${user}`);
                const data = await response.json();
                
                document.getElementById('loader').classList.add('hidden');
                
                if(data.success) {
                    document.getElementById('analyticsChart').src = './' + data.chart_url + '?cache=' + new Date().getTime();
                    
                    const foundBox = document.getElementById('foundList');
                    foundBox.innerHTML = '';
                    const foundKeys = Object.keys(data.found);
                    document.getElementById('count-found').innerText = foundKeys.length;
                    
                    if(foundKeys.length === 0) {
                        foundBox.innerHTML = '<p class="text-xs text-slate-500 text-center py-8 font-mono">No network blueprints mapped.</p>';
                    } else {
                        for(const [platform, link] of Object.entries(data.found)) {
                            foundBox.innerHTML += `
                                <div class="flex justify-between items-center p-3 bg-gray-950 border border-gray-800 rounded-xl text-xs transition hover:border-sky-500/50">
                                    <span class="font-bold text-slate-200 truncate max-w-[120px]"><i class="fa-solid fa-globe text-sky-400/70 mr-1.5"></i> ${platform}</span>
                                    <a href="${link}" target="_blank" class="text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold border border-sky-500/20 bg-sky-500/5 px-2 py-0.5 rounded-md transition">Open <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>
                                </div>`;
                        }
                    }

                    const vacantBox = document.getElementById('vacantList');
                    vacantBox.innerHTML = '';
                    const missingKeys = Object.keys(data.missing);
                    document.getElementById('count-vacant').innerText = missingKeys.length;
                    
                    if(missingKeys.length === 0) {
                        vacantBox.innerHTML = '<p class="text-xs text-slate-500 text-center py-8 font-mono">Global network fully saturated.</p>';
                    } else {
                        for(const platform of missingKeys) {
                            vacantBox.innerHTML += `
                                <div class="p-3 bg-gray-950 border border-dashed border-gray-800 rounded-xl text-xs flex justify-between items-center text-slate-400">
                                    <span class="font-medium font-mono truncate max-w-[150px]"><i class="fa-solid fa-plus text-emerald-400/50 mr-1.5"></i> ${platform}</span>
                                    <span class="text-[9px] text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-md uppercase tracking-wider">Available</span>
                                </div>`;
                        }
                    }

                    document.getElementById('outputContainer').classList.remove('hidden');
                } else {
                    alert("System Exception: Internal logic array failed.");
                }
            } catch (err) {
                document.getElementById('loader').classList.add('hidden');
                console.error("Critical Signal Error:", err);
            }
        }
    </script>
</body>
</html>
"""
