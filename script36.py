import os
import urllib.parse
from flask import Blueprint, render_template_string, request, jsonify
from googlesearch import search

# Blueprint engine setup
script36_bp = Blueprint('script36', __name__)

# High DA Websites Suggestion List
POTENTIAL_BACKLINK_SOURCES = [
    {"site": "github.com", "type": "Profile / Project Backlink", "difficulty": "Easy"},
    {"site": "medium.com", "type": "Article / Blog Backlink", "difficulty": "Medium"},
    {"site": "dev.to", "type": "Article / Tech Blog", "difficulty": "Easy"},
    {"site": "reddit.com", "type": "Community / Link Share", "difficulty": "Medium"},
    {"site": "linkedin.com", "type": "Article / Pulse Backlink", "difficulty": "Easy"},
    {"site": "quora.com", "type": "Q&A Answer Backlink", "difficulty": "Easy"},
    {"site": "tumblr.com", "type": "Microblog Backlink", "difficulty": "Easy"},
    {"site": "pinterest.com", "type": "Image / Pin Backlink", "difficulty": "Easy"}
]

def find_existing_backlinks(target_domain):
    """
    Uses googlesearch-python module to securely fetch live index links.
    """
    query = f'"{target_domain}" -site:{target_domain}'
    existing_links = []
    
    try:
        # Pull up to 15 items safely to avoid immediate strict thresholds
        results = search(query, num_results=15, sleep_interval=2)
        
        for url in results:
            if target_domain not in url and "google.com" not in url:
                parsed_url = urllib.parse.urlparse(url)
                title = parsed_url.netloc.replace("www.", "")
                existing_links.append({"title": f"Indexed link on {title}", "url": url})
                
        return existing_links
    except Exception as e:
        return {"error": "Google limits hit or network timeout. Please try again after a brief pause."}

# Modern UI Dashboard for Script36
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Backlink Hub - Script36</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #4ade80;
            --warning: #fbbf24;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 30px;
            background-color: var(--bg-color);
            color: var(--text-main);
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 { color: var(--accent); margin-bottom: 5px; }
        .search-box {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        input[type="text"] {
            flex: 1;
            padding: 14px;
            border: 2px solid #334155;
            background: #0f172a;
            color: white;
            border-radius: 8px;
            font-size: 16px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: var(--accent);
        }
        button {
            padding: 14px 28px;
            background-color: var(--accent);
            color: #0f172a;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: 0.2s;
        }
        button:hover { opacity: 0.9; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        .card {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            min-height: 200px;
        }
        h2 {
            border-bottom: 2px solid #334155;
            padding-bottom: 10px;
            margin-top: 0;
            font-size: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-size: 14px;
        }
        th { color: var(--text-muted); font-weight: 600; }
        a { color: var(--accent); text-decoration: none; }
        a:hover { text-decoration: underline; }
        .badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-easy { background: rgba(74, 222, 128, 0.2); color: var(--success); }
        .badge-med { background: rgba(251, 191, 36, 0.2); color: var(--warning); }
        .loading { text-align: center; color: var(--text-muted); padding: 40px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Script36: Backlink Engine</h1>
            <p style="color: var(--text-muted);">Analyze live presence and unlock organic traffic opportunities</p>
        </header>

        <div class="search-box">
            <input type="text" id="domainInput" placeholder="Apni domain daalo (e.g., techfirm.com)" required>
            <button onclick="startAnalysis()">Analyze Backlinks</button>
        </div>

        <div class="loading" id="loader">🌐 Analyzing Google index footprints natively... Please wait...</div>

        <div class="grid" id="resultsGrid" style="display: none;">
            <div class="card">
                <h2 style="color: var(--success);">🎯 Existing Backlinks</h2>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Source Title</th>
                                <th>URL Path</th>
                            </tr>
                        </thead>
                        <tbody id="existingTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2 style="color: var(--warning);">🚀 Opportunities to Build</h2>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Platform</th>
                                <th>Type</th>
                                <th>Difficulty</th>
                            </tr>
                        </thead>
                        <tbody id="suggestedTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function startAnalysis() {
            const domain = document.getElementById('domainInput').value.trim();
            if(!domain) return alert("Bhai, domain fill karo pehle!");

            document.getElementById('loader').style.display = 'block';
            document.getElementById('resultsGrid').style.display = 'none';

            try {
                const formData = new FormData();
                formData.append('domain', domain);

                // FIXED: Using relative point query to prevent global blueprint route path breaking
                const response = await fetch('check-backlinks', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Server status returned error: ${response.status}`);
                }
                
                const data = await response.json();
                document.getElementById('loader').style.display = 'none';

                if(data.current_backlinks_found && data.current_backlinks_found.error) {
                    alert(data.current_backlinks_found.error);
                    return;
                }

                const existingBody = document.getElementById('existingTableBody');
                existingBody.innerHTML = '';
                if(!data.current_backlinks_found || data.current_backlinks_found.length === 0) {
                    existingBody.innerHTML = '<tr><td colspan="2" style="color: var(--text-muted);">Koi external links nahi mile abhi.</td></tr>';
                } else {
                    data.current_backlinks_found.forEach(item => {
                        existingBody.innerHTML += `<tr><td><b>${item.title}</b></td><td><a href="${item.url}" target="_blank">Visit Site</a></td></tr>`;
                    });
                }

                const suggestedBody = document.getElementById('suggestedTableBody');
                suggestedBody.innerHTML = '';
                data.where_to_create_suggestions.forEach(item => {
                    const badgeClass = item.difficulty === 'Easy' ? 'badge-easy' : 'badge-med';
                    suggestedBody.innerHTML += `<tr>
                        <td><a href="https://${item.site}" target="_blank">${item.site}</a></td>
                        <td>${item.type}</td>
                        <td><span class="badge ${badgeClass}">${item.difficulty}</span></td>
                    </tr>`;
                });

                document.getElementById('resultsGrid').style.display = 'grid';
            } catch(err) {
                document.getElementById('loader').style.display = 'none';
                alert("Kuch error aaya bhai: " + err.message);
            }
        }
    </script>
</body>
</html>
'''

# Routes tied to Blueprint
@script36_bp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@script36_bp.route('/check-backlinks', methods=['POST'])
def check_backlinks():
    target_domain = request.form.get('domain', '').strip().lower()
    if not target_domain:
        return jsonify({"current_backlinks_found": {"error": "Invalid Domain parameter value."}})
        
    target_domain = target_domain.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
    
    current_backlinks = find_existing_backlinks(target_domain)
    suggested_backlinks = []
    
    if isinstance(current_backlinks, list):
        found_domains = [link['url'] for link in current_backlinks]
        for source in POTENTIAL_BACKLINK_SOURCES:
            is_created = any(source['site'] in f_dom for f_dom in found_domains)
            if not is_created:
                suggested_backlinks.append(source)
    else:
        suggested_backlinks = POTENTIAL_BACKLINK_SOURCES

    return jsonify({
        "target_domain": target_domain,
        "current_backlinks_found": current_backlinks,
        "where_to_create_suggestions": suggested_backlinks
    })
