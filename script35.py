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
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
        response = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
        if response.status_code == 200:
            with results_lock: found[platform] = url
        elif response.status_code == 404:
            with results_lock: missing[platform] = url
        else:
            with results_lock: errors[platform] = f"Status: {response.status_code}"
    except requests.RequestException:
        with results_lock: errors[platform] = "Timeout/Restricted"

def generate_analytics_chart(username, found_count, missing_count, error_count):
    labels = ['Active Profiles', 'Vacant Handles', 'Errors/Blocked']
    sizes = [found_count, missing_count, error_count]
    colors = ['#6366f1', '#f43f5e', '#9ca3af']
    
    plt.figure(figsize=(6, 4))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    
    # Render static path architecture security
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    graph_path = os.path.join(static_dir, f"{username}_intel_report.png")
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', transparent=True)
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

# SYSTEM UI LAYOUT SCHEMATICS
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Advanced Social Intelligence Finder</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; transition: background-color 0.3s, color 0.3s; }
        .dark-mode { 
            --bg-panel: #111827; 
            --bg-main: #030712; 
            --text-main: #f9fafb; 
            --text-muted: #9ca3af; 
            --border-color: #1f2937; 
        }
        .light-mode { 
            --bg-panel: #ffffff; 
            --bg-main: #f3f4f6; 
            --text-main: #111827; 
            --text-muted: #6b7280; 
            --border-color: #e5e7eb; 
        }
        body { background-color: var(--bg-main); color: var(--text-main); }
        .panel-card { background-color: var(--bg-panel); border-color: var(--border-color); }
        .text-custom-main { color: var(--text-main); }
        .text-custom-muted { color: var(--text-muted); }
        .border-custom { border-color: var(--border-color); }
        .input-custom { background-color: var(--bg-main); border-color: var(--border-color); color: var(--text-main); }
    </style>
</head>
<body class="light-mode antialiased selection:bg-indigo-500 selection:text-white">

    <div class="min-h-screen flex flex-col md:flex-row">
        <aside class="w-full md:w-64 bg-gray-950 text-white flex flex-col border-r border-gray-900">
            <div class="p-6 border-b border-gray-900 flex items-center gap-3">
                <div class="p-2.5 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl"><i class="fa-solid fa-satellite-dish text-lg text-white"></i></div>
                <div>
                    <h2 class="font-bold text-base tracking-wide leading-none text-white">SocialFinder</h2>
                    <span class="text-[10px] text-gray-400 uppercase tracking-widest mt-1 block">OSINT v35.0</span>
                </div>
            </div>
            <nav class="flex-1 p-4 space-y-1.5">
                <button class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"><i class="fa-solid fa-magnifying-glass w-5 text-center"></i> Recon Gateway</button>
            </nav>
            <div class="p-4 border-t border-gray-900 space-y-2">
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-gray-900 text-xs font-semibold cursor-pointer text-gray-300">
                    <span>Appearance System</span><i id="theme-icon" class="fa-solid fa-moon"></i>
                </button>
            </div>
        </aside>

        <main class="flex-1 p-6 md:p-8 overflow-y-auto max-h-screen">
            <div class="flex justify-between items-center border-b border-custom pb-5 mb-6">
                <div>
                    <h1 class="text-2xl font-black tracking-tight text-custom-main">{{ company }}</h1>
                    <p class="text-xs text-custom-muted mt-0.5">Advanced Cross-Border Social Footprint Footmarking Engine</p>
                </div>
                <span class="text-[10px] font-mono font-bold bg-indigo-500/10 text-indigo-500 px-2 py-1 rounded border border-indigo-500/20">Active Node</span>
            </div>

            <div class="panel-card border p-6 rounded-2xl shadow-sm mb-8 space-y-3">
                <h3 class="text-xs font-bold uppercase tracking-wider text-custom-muted"><i class="fa-solid fa-terminal text-indigo-500"></i> Intelligence Scan Target</h3>
                <div class="flex flex-col sm:flex-row gap-3">
                    <input type="text" id="targetUsername" placeholder="Enter social brand username handle" 
                           class="flex-1 input-custom border rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 font-medium">
                    <button onclick="executeAsyncRecon()" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-6 py-3 rounded-xl text-sm transition shadow-md cursor-pointer">
                        Trigger Threat Map
                    </button>
                </div>
            </div>

            <div id="loader" class="hidden text-center py-20">
                <i class="fa-solid fa-circle-notch fa-spin text-4xl text-indigo-500"></i>
                <p class="text-xs text-custom-muted mt-4 font-semibold animate-pulse">Running multi-threaded matrix loops on international clusters...</p>
            </div>

            <div id="outputContainer" class="hidden space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    
                    <div class="panel-card border p-5 rounded-2xl flex flex-col items-center justify-center shadow-sm">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-custom-muted w-full mb-4 text-left"><i class="fa-solid fa-chart-pie text-indigo-500"></i> Graphical Data Matrix</h3>
                        <div class="border border-custom p-2 rounded-xl bg-gray-500/5">
                            <img id="analyticsChart" src="" alt="Live Analysis Plot Engine" class="rounded-lg max-w-full">
                        </div>
                    </div>

                    <div class="panel-card border p-5 rounded-2xl flex flex-col shadow-sm">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-emerald-500 mb-4"><i class="fa-solid fa-square-check"></i> Discovered Network Profiles (<span id="count-found">0</span>)</h3>
                        <div id="foundList" class="space-y-2 overflow-y-auto max-h-72 flex-1 pr-1"></div>
                    </div>

                    <div class="panel-card border p-5 rounded-2xl flex flex-col shadow-sm">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-rose-500 mb-4"><i class="fa-solid fa-circle-nodes"></i> Vacant Marketing Assets (<span id="count-vacant">0</span>)</h3>
                        <div id="vacantList" class="space-y-2 overflow-y-auto max-h-72 flex-1 pr-1"></div>
                    </div>

                </div>
            </div>
        </main>
    </div>

    <script>
        function toggleDarkMode(forceDark = false) {
            const body = document.body;
            const icon = document.getElementById('theme-icon');
            if (body.classList.contains('light-mode') || forceDark) {
                body.classList.remove('light-mode'); body.classList.add('dark-mode');
                body.style.setProperty('--bg-main', '#030712'); body.style.setProperty('--bg-panel', '#111827');
                body.style.setProperty('--text-main', '#f9fafb'); body.style.setProperty('--border-color', '#1f2937');
                body.style.setProperty('--text-muted', '#9ca3af');
                icon.className = "fa-solid fa-sun text-amber-400";
                localStorage.setItem('theme', 'dark');
            } else {
                body.classList.remove('dark-mode'); body.classList.add('light-mode');
                body.style.setProperty('--bg-main', '#f3f4f6'); body.style.setProperty('--bg-panel', '#ffffff');
                body.style.setProperty('--text-main', '#111827'); body.style.setProperty('--border-color', '#e5e7eb');
                body.style.setProperty('--text-muted', '#6b7280');
                icon.className = "fa-solid fa-moon";
                localStorage.setItem('theme', 'light');
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            if (localStorage.getItem('theme') === 'dark') toggleDarkMode(true);
        });

        async function executeAsyncRecon() {
            const user = document.getElementById('targetUsername').value.trim();
            if(!user) return alert("Validation Failed: Active handle node must not be blank.");

            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('outputContainer').classList.add('hidden');

            try {
                // Modified blueprint endpoint structural tracking
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
                        foundBox.innerHTML = '<p class="text-xs text-gray-500 text-center py-6 font-medium">No brand footprints discovered.</p>';
                    } else {
                        for(const [platform, link] of Object.entries(data.found)) {
                            foundBox.innerHTML += `
                                <div class="flex justify-between items-center p-3 bg-gray-500/5 border border-custom rounded-xl text-xs">
                                    <span class="font-bold text-custom-main">${platform}</span>
                                    <a href="${link}" target="_blank" class="text-indigo-500 hover:underline flex items-center gap-1 font-semibold">Verify Link <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i></a>
                                </div>`;
                        }
                    }

                    const vacantBox = document.getElementById('vacantList');
                    vacantBox.innerHTML = '';
                    const missingKeys = Object.keys(data.missing);
                    document.getElementById('count-vacant').innerText = missingKeys.length;
                    
                    if(missingKeys.length === 0) {
                        vacantBox.innerHTML = '<p class="text-xs text-gray-500 text-center py-6 font-medium">Global saturation complete.</p>';
                    } else {
                        for(const platform of missingKeys) {
                            vacantBox.innerHTML += `
                                <div class="p-3 bg-gray-500/5 border border-dashed border-custom rounded-xl text-xs flex justify-between items-center text-custom-muted">
                                    <span class="font-medium">${platform}</span>
                                    <span class="text-[9px] text-emerald-500 font-bold bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-md uppercase tracking-wider">Available</span>
                                </div>`;
                        }
                    }

                    document.getElementById('outputContainer').classList.remove('hidden');
                } else {
                    alert("Fatal: Signal loss within core logic loop.");
                }
            } catch (err) {
                document.getElementById('loader').classList.add('hidden');
                console.error("Transmission Error:", err);
            }
        }
    </script>
</body>
</html>
"""

