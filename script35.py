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

# Premium Tech Browsing Headers to bypass heavy platform blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
}

TARGET_SITES = {
    "Instagram": "https://www.instagram.com/{}",
    "Twitter/X": "https://twitter.com/{}",
    "Facebook": "https://www.facebook.com/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "Threads": "https://www.threads.net/@{}",
    "Medium": "https://medium.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Vimeo": "https://vimeo.com/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Flickr": "https://www.flickr.com/photos/{}"
}

results_lock = threading.Lock()

def check_platform(platform, url_template, username, found, missing, errors):
    url = url_template.format(username)
    try:
        # Session built-in handling to sustain redirect traps
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=7, allow_redirects=True)
        
        # Smart detection parsing based on common social network behaviors
        final_url = response.url.lower()
        
        if response.status_code == 404:
            with results_lock: missing[platform] = url
        elif response.status_code == 200:
            # Bypass false positives like redirects to login panels
            if "login" in final_url or "signin" in final_url or "register" in final_url:
                with results_lock: missing[platform] = url
            elif platform == "Instagram" and "instagram.com/accounts/" in final_url:
                with results_lock: missing[platform] = url
            else:
                with results_lock: found[platform] = url
        else:
            with results_lock: errors[platform] = f"Status {response.status_code}"
    except requests.RequestException:
        with results_lock: errors[platform] = "Timeout/Restricted"

def generate_analytics_chart(username, found_count, missing_count, error_count):
    # Total fallback safe check
    if found_count == 0 and missing_count == 0 and error_count == 0:
        missing_count = 1 

    labels = ['Active Profiles', 'Vacant Handles', 'Restricted']
    sizes = [found_count, missing_count, error_count]
    colors = ['#38bdf8', '#4ade80', '#64748b']
    
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=140, 
        textprops=dict(color="w", weight="bold")
    )
    
    # Matching dark cyberpunk layout palette
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

# 2. ASSIGN PATH ROUTING TO THE BLUEPRINT STRATEGY
@script35_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@script35_bp.route('/api/audit', methods=['GET'])
def api_audit():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Target handler parameter required.'}), 400

    found = {}
    missing = {}
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_platform, plat, tmpl, username, found, missing, errors) for plat, tmpl in TARGET_SITES.items()]
        concurrent.futures.wait(futures)

    chart_url = generate_analytics_chart(username, len(found), len(missing), len(errors))

    return jsonify({
        'success': True,
        'username': username,
        'found': found,
        'missing': missing,
        'errors_count': len(errors),
        'chart_url': chart_url
    })

# ULTRA PREMIUM SYSTEM UI LAYOUT SCHEMATICS
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Recon Social Architecture Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #0f172a; 
            color: #f8fafc;
        }
        .cyber-card {
            background: #1e293b;
            border: 1px solid #334155;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        .glow-accent {
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
        }
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0f172a;
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
    </style>
</head>
<body class="antialiased selection:bg-sky-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar Navigation Element -->
        <aside class="w-full lg:w-72 bg-slate-950 flex flex-col border-b lg:border-r border-slate-800 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-xl shadow-lg glow-accent">
                    <i class="fa-solid fa-shield-halved text-xl text-white"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">SocialRadar</h2>
                    <span class="text-[10px] text-sky-400 font-mono uppercase tracking-widest mt-1 block">OSINT ENGINE v35</span>
                </div>
            </div>
            
            <nav class="flex-1 space-y-2">
                <button class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium bg-gradient-to-r from-sky-600 to-sky-500 text-white shadow-md">
                    <i class="fa-solid fa-terminal w-5 text-sky-200"></i> Target Analyzer
                </button>
            </nav>
            
            <div class="pt-4 border-t border-slate-800 text-center">
                <span class="text-[11px] text-slate-500 font-mono">Status: Secure Sandbox Connection</span>
            </div>
        </aside>

        <!-- Main Dashboard Arena -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-800 pb-6 mb-8 gap-4">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white">{{ company }}</h1>
                    <p class="text-sm text-slate-400 mt-1">Cross-Platform Identity Matrix & Footprint Verification Terminal</p>
                </div>
                <div>
                    <span class="inline-flex items-center gap-2 text-xs font-mono bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/20">
                        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span> Global Link Array Active
                    </span>
                </div>
            </div>

            <!-- Target Search Form -->
            <div class="cyber-card p-6 rounded-2xl mb-8">
                <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                    <i class="fa-solid fa-fingerprint text-sky-400"></i> Scan Target Formulation
                </h3>
                <div class="flex flex-col sm:flex-row gap-4">
                    <input type="text" id="targetUsername" placeholder="Enter username / brand handle string (e.g. shivam)" 
                           class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-sky-500 font-mono">
                    <button onclick="executeAsyncRecon()" class="bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold px-8 py-3.5 rounded-xl text-sm transition shadow-lg hover:shadow-sky-500/20 active:scale-95 cursor-pointer">
                        Execute Network Pulse
                    </button>
                </div>
            </div>

            <!-- Loading Spinner Grid -->
            <div id="loader" class="hidden text-center py-24 cyber-card rounded-2xl">
                <i class="fa-solid fa-circle-notch fa-spin text-5xl text-sky-400"></i>
                <p class="text-sm text-slate-400 mt-6 font-mono animate-pulse">Running multi-threaded cluster scan across core social networks...</p>
            </div>

            <!-- Data Analysis Dashboard Output -->
            <div id="outputContainer" class="hidden space-y-8">
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    
                    <!-- Graph Cluster -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-sky-400"></i> Analytics Distribution
                        </h3>
                        <div class="border border-slate-700 p-4 rounded-xl bg-slate-900/50 flex-1 flex items-center justify-center">
                            <img id="analyticsChart" src="" alt="Dynamic Evaluation Output" class="rounded-lg max-h-64 object-contain">
                        </div>
                    </div>

                    <!-- Discovered Matrix List -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-sky-400 mb-4 flex justify-between items-center">
                            <span class="flex items-center gap-2"><i class="fa-solid fa-circle-check"></i> Registered Profiles</span>
                            <span id="count-found" class="bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs px-2 py-0.5 rounded-md font-mono">0</span>
                        </h3>
                        <div id="foundList" class="space-y-3 overflow-y-auto max-h-80 flex-1 pr-1"></div>
                    </div>

                    <!-- Vacant Assets List -->
                    <div class="cyber-card p-6 rounded-2xl flex flex-col">
                        <h3 class="font-bold text-xs uppercase tracking-widest text-emerald-400 mb-4 flex justify-between items-center">
                            <span class="flex items-center gap-2"><i class="fa-solid fa-circle-plus"></i> Unclaimed Channels</span>
                            <span id="count-vacant" class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2 py-0.5 rounded-md font-mono">0</span>
                        </h3>
                        <div id="vacantList" class="space-y-3 overflow-y-auto max-h-80 flex-1 pr-1"></div>
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
                                <div class="flex justify-between items-center p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-xl text-xs transition hover:border-sky-500/50">
                                    <span class="font-bold text-slate-200"><i class="fa-solid fa-globe text-sky-400/70 mr-1.5"></i> ${platform}</span>
                                    <a href="${link}" target="_blank" class="text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold border border-sky-500/20 bg-sky-500/5 px-2.5 py-1 rounded-md transition">Open Intel <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>
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
                                <div class="p-3.5 bg-slate-900/40 border border-dashed border-slate-700/80 rounded-xl text-xs flex justify-between items-center text-slate-400">
                                    <span class="font-medium font-mono"><i class="fa-solid fa-plus text-emerald-400/50 mr-1.5"></i> ${platform}</span>
                                    <span class="text-[9px] text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md uppercase tracking-wider">Available</span>
                                </div>`;
                        }
                    }

                    document.getElementById('outputContainer').classList.remove('hidden');
                } else {
                    alert("System Exception: Internal logic array failed to yield return stream.");
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
