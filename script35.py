from flask import Flask, Blueprint, render_template_string, request, jsonify, send_from_directory
import os
import threading
import concurrent.futures
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import json

# ===== FLASK APP SETUP =====
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['JSON_SORT_KEYS'] = False

# ===== BLUEPRINT SETUP =====
osint_bp = Blueprint('osint', __name__, url_prefix='/osint')

# ===== CONFIG =====
COMPANY_NAME = 'SocialRadar OSINT'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

# ===== PLATFORMS DATABASE =====
PLATFORMS = {
    "Facebook": "https://www.facebook.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Twitter": "https://twitter.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Threads": "https://www.threads.net/@{}",
    "Bluesky": "https://bsky.app/profile/{}",
    "Telegram": "https://t.me/{}",
    "Discord": "https://discord.com/users/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Stack Overflow": "https://stackoverflow.com/users/{}",
    "Dev.to": "https://dev.to/{}",
    "Hashnode": "https://hashnode.com/@{}",
    "Medium": "https://medium.com/@{}",
    "Substack": "https://{}.substack.com",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "ArtStation": "https://www.artstation.com/{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Flickr": "https://www.flickr.com/photos/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Kick": "https://kick.com/{}",
    "Rumble": "https://rumble.com/c/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Last.fm": "https://www.last.fm/user/{}",
    "Quora": "https://www.quora.com/profile/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Blogger": "https://{}.blogspot.com",
    "WordPress": "https://{}.wordpress.com",
    "Wattpad": "https://www.wattpad.com/user/{}",
    "AngelList": "https://angel.co/{}",
    "Crunchbase": "https://www.crunchbase.com/person/{}",
    "Product Hunt": "https://www.producthunt.com/@{}",
    "Meetup": "https://www.meetup.com/members/{}",
    "eBay": "https://www.ebay.com/usr/{}",
    "Etsy": "https://www.etsy.com/shop/{}",
    "Shopify": "https://{}.myshopify.com",
    "Gumroad": "https://gumroad.com/{}",
    "Yelp": "https://www.yelp.com/user_details?userid={}",
    "IMDb": "https://www.imdb.com/user/{}",
    "Goodreads": "https://www.goodreads.com/user/show/{}",
    "Justdial": "https://www.justdial.com/All-India/{}",
    "OLX": "https://www.olx.in/user/{}",
    "Quikr": "https://www.quikr.com/user/{}",
    "Zomato": "https://www.zomato.com/user/{}",
    "Swiggy": "https://www.swiggy.com/user/{}",
    "Linktree": "https://linktr.ee/{}",
    "About.me": "https://about.me/{}",
    "Carrd": "https://{}.carrd.co",
    "Ko-fi": "https://ko-fi.com/{}",
    "Patreon": "https://www.patreon.com/{}",
    "Dailymotion": "https://www.dailymotion.com/{}",
    "Vimeo": "https://vimeo.com/{}",
    "BitChute": "https://www.bitchute.com/channel/{}",
    "Odysee": "https://odysee.com/@{}",
    "itch.io": "https://itch.io/profile/{}",
    "Epic Games": "https://www.epicgames.com/site/en-US/home/{}",
    "500px": "https://500px.com/{}",
    "SmugMug": "https://www.smugmug.com/{}",
    "Wix": "https://{}.wixsite.com",
    "Squarespace": "https://{}.squarespace.com",
    "WeChat": "https://weixin.qq.com/{}",
    "QQ": "https://qq.com/{}",
    "Douyin": "https://www.douyin.com/{}",
    "Xiaohongshu": "https://www.xiaohongshu.com/{}",
    "Weibo": "https://weibo.com/{}",
    "Viber": "https://viber.click/{}",
    "WhatsApp": "https://wa.me/{}",
    "Signal": "https://signal.me/#p/{}",
    "CodePen": "https://codepen.io/{}",
    "JSFiddle": "https://jsfiddle.net/user/{}",
    "Replit": "https://replit.com/@{}",
    "Kaggle": "https://www.kaggle.com/{}",
    "Hackerrank": "https://www.hackerrank.com/{}",
    "LeetCode": "https://www.leetcode.com/{}",
    "Codeforces": "https://codeforces.com/profile/{}",
    "TopCoder": "https://www.topcoder.com/members/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "Lobsters": "https://lobste.rs/u/{}",
    "Slashdot": "https://slashdot.org/~{}",
    "Digg": "https://digg.com/@{}",
    "StumbleUpon": "https://www.stumbleupon.com/stumbler/{}",
    "Delicious": "https://del.icio.us/{}",
    "Weheartit": "https://weheartit.com/{}",
    "Imgur": "https://imgur.com/user/{}",
    "9GAG": "https://9gag.com/u/{}",
    "Tumblr (alt)": "https://{}tumblr.com",
    "Instagram Story": "https://instagram.com/stories/{}",
    "Facebook Gaming": "https://www.facebook.com/gaming/{}",
    "Twitch Clips": "https://www.twitch.tv/{}/clips",
    "YouTube Community": "https://www.youtube.com/@{}/community",
    "TikTok Profile": "https://www.tiktok.com/@{}/",
    "Nextdoor": "https://nextdoor.com/profile/{}",
    "Airbnb": "https://www.airbnb.com/users/show/{}",
    "Uber": "https://www.uber.com/profile/{}",
    "Lyft": "https://www.lyft.com/profile/{}",
    "DoorDash": "https://www.doordash.com/profile/{}",
    "Grubhub": "https://www.grubhub.com/profile/{}",
    "BookMyShow": "https://in.bookmyshow.com/profile/{}",
}

results_lock = threading.Lock()

def create_session():
    """Create requests session with retry logic"""
    session = requests.Session()
    retry = Retry(total=1, backoff_factor=0.2, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def check_if_exists(url, username):
    """Universal profile existence check"""
    try:
        session = create_session()
        response = session.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        
        # Status code checks
        if response.status_code == 404:
            return False
        
        if response.status_code in [403, 500, 502, 503]:
            return False
        
        if response.status_code != 200:
            return False
        
        # Content checks
        content = response.text.lower()
        
        # Check for common "not found" messages
        not_found_terms = [
            'not found', 'user not found', 'profile not found',
            'this account doesn\'t exist', 'this person isn\'t available',
            'page not found', 'error 404', 'does not exist',
            'sorry this user', 'not available', 'unavailable',
            'suspended', 'deleted', 'blocked'
        ]
        
        for term in not_found_terms:
            if term in content:
                return False
        
        # Check for login/auth redirects
        if 'login' in response.url.lower() or 'signin' in response.url.lower():
            return False
        
        # Check minimum content length (most profiles have substantial content)
        if len(response.text) < 2000:
            return False
        
        return True
        
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        return False

def check_platform(platform_name, url, username, found, missing, errors):
    """Check single platform"""
    try:
        formatted_url = url.format(username)
        
        if check_if_exists(formatted_url, username):
            with results_lock:
                found[platform_name] = formatted_url
        else:
            with results_lock:
                missing[platform_name] = formatted_url
                
    except Exception as e:
        with results_lock:
            try:
                missing[platform_name] = url.format(username)
            except:
                missing[platform_name] = url

def generate_chart(username, found_count, missing_count):
    """Generate pie chart"""
    try:
        if found_count == 0 and missing_count == 0:
            missing_count = 1
        
        labels = ['Active', 'Available']
        sizes = [found_count, missing_count]
        colors = ['#10b981', '#f59e0b']
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=140, textprops=dict(color="white", weight="bold", fontsize=12))
        
        fig.patch.set_facecolor('#1e293b')
        ax.set_facecolor('#1e293b')
        
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        graph_path = os.path.join(static_dir, f"{username}_chart.png")
        plt.savefig(graph_path, dpi=200, bbox_inches='tight', facecolor='#1e293b')
        plt.close()
        
        return f"/static/{username}_chart.png"
    except Exception as e:
        return "/static/default.png"

# ===== ROUTES =====
@osint_bp.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@osint_bp.route('/api/audit', methods=['GET'])
def api_audit():
    """Scan username across platforms"""
    try:
        username = request.args.get('username', '').strip()
        
        if not username or len(username) < 2:
            return jsonify({
                'success': False,
                'message': 'Username must be at least 2 characters'
            }), 400
        
        found = {}
        missing = {}
        errors = {}

        # Parallel scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(check_platform, platform_name, url, username, found, missing, errors)
                for platform_name, url in PLATFORMS.items()
            ]
            concurrent.futures.as_completed(futures)

        chart_url = generate_chart(username, len(found), len(missing))

        return jsonify({
            'success': True,
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'total_platforms': len(PLATFORMS),
            'found_count': len(found),
            'missing_count': len(missing),
            'error_count': len(errors),
            'found': found,
            'missing': list(missing.keys()),
            'chart_url': chart_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, path)

@app.route('/')
def home():
    """Redirect to OSINT"""
    return '''
    <html>
        <head><title>SocialRadar OSINT</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h1>ðŸ” SocialRadar OSINT</h1>
            <p>Scan 150+ social media platforms for usernames</p>
            <a href="/osint/" style="font-size: 18px; padding: 10px 20px; background: #10b981; color: white; text-decoration: none; border-radius: 5px;">
                Open Scanner â†’
            </a>
        </body>
    </html>
    '''

# ===== HTML LAYOUT =====
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-900 text-slate-100">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <aside class="w-full lg:w-80 bg-slate-950 border-b lg:border-r border-slate-800 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                    <i class="fa-solid fa-globe text-xl text-white"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg text-white">{{ company }}</h1>
                    <p class="text-xs text-emerald-400">100+ Platforms</p>
                </div>
            </div>
            
            <div class="space-y-4">
                <input type="text" id="username" placeholder="username" 
                       class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 font-mono text-sm">
                <button onclick="scan()" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold py-3 rounded-lg transition">
                    <i class="fa-solid fa-magnifying-glass mr-2"></i> Scan
                </button>
            </div>

            <div id="stats" class="hidden mt-6 space-y-2 text-xs border-t border-slate-800 pt-6">
                <div class="flex justify-between bg-slate-800 p-3 rounded">
                    <span>Total Checked:</span>
                    <span id="stat-total" class="font-bold text-emerald-400">0</span>
                </div>
                <div class="flex justify-between bg-emerald-900/30 p-3 rounded border border-emerald-500/20">
                    <span>Found:</span>
                    <span id="stat-found" class="font-bold text-emerald-300">0</span>
                </div>
                <div class="flex justify-between bg-amber-900/30 p-3 rounded border border-amber-500/20">
                    <span>Available:</span>
                    <span id="stat-vacant" class="font-bold text-amber-300">0</span>
                </div>
            </div>
        </aside>

        <main class="flex-1 p-6 lg:p-10">
            <div id="loader" class="hidden text-center py-20">
                <i class="fa-solid fa-spinner fa-spin text-5xl text-emerald-500 mb-4"></i>
                <p class="text-slate-400 font-mono">Scanning 100+ platforms...</p>
            </div>

            <div id="results" class="hidden space-y-6">
                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <img id="chart" src="" alt="Chart" class="max-h-64 mx-auto rounded">
                </div>

                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h2 class="text-lg font-bold text-emerald-400 mb-4">
                        <i class="fa-solid fa-check-circle mr-2"></i> Found (<span id="count-found">0</span>)
                    </h2>
                    <div id="found-list" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto"></div>
                </div>

                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h2 class="text-lg font-bold text-amber-400 mb-4">
                        <i class="fa-solid fa-circle-plus mr-2"></i> Available (<span id="count-vacant">0</span>)
                    </h2>
                    <div id="vacant-list" class="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-96 overflow-y-auto text-sm"></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function scan() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                alert('Enter a username');
                return;
            }

            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('stats').classList.add('hidden');

            try {
                const res = await fetch(`/osint/api/audit?username=${encodeURIComponent(username)}`);
                const data = await res.json();

                if (data.success) {
                    document.getElementById('stat-total').textContent = data.total_platforms;
                    document.getElementById('stat-found').textContent = data.found_count;
                    document.getElementById('stat-vacant').textContent = data.missing_count;
                    document.getElementById('stats').classList.remove('hidden');

                    document.getElementById('chart').src = data.chart_url + '?t=' + Date.now();

                    const foundList = document.getElementById('found-list');
                    foundList.innerHTML = '';
                    document.getElementById('count-found').textContent = data.found_count;

                    Object.entries(data.found).forEach(([platform, url]) => {
                        foundList.innerHTML += `
                            <a href="${url}" target="_blank" class="bg-emerald-900/30 border border-emerald-500/50 p-3 rounded hover:border-emerald-400 transition flex justify-between items-center text-sm">
                                <span class="font-bold text-emerald-300 truncate">${platform}</span>
                                <i class="fa-solid fa-arrow-up-right text-emerald-500 ml-2"></i>
                            </a>
                        `;
                    });

                    if (data.found_count === 0) {
                        foundList.innerHTML = '<p class="text-slate-500 py-8 col-span-full text-center">No profiles found</p>';
                    }

                    const vacantList = document.getElementById('vacant-list');
                    vacantList.innerHTML = '';
                    document.getElementById('count-vacant').textContent = data.missing_count;

                    data.missing.forEach(platform => {
                        vacantList.innerHTML += `
                            <div class="bg-amber-900/20 border border-dashed border-amber-500/30 p-2 rounded text-center text-xs">
                                <div class="text-amber-400 truncate">${platform}</div>
                                <div class="text-amber-600 text-[10px]">Available</div>
                            </div>
                        `;
                    });

                    if (data.missing_count === 0) {
                        vacantList.innerHTML = '<p class="text-slate-500 py-8 col-span-full text-center">All taken</p>';
                    }

                    document.getElementById('results').classList.remove('hidden');
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }

            document.getElementById('loader').classList.add('hidden');
        }

        document.getElementById('username').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') scan();
        });
    </script>
</body>
</html>
"""

# ===== REGISTER BLUEPRINT & RUN =====
app.register_blueprint(osint_bp)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
