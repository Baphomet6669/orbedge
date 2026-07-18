import os
import urllib.parse
from flask import Blueprint, render_template_string, request, jsonify
import requests

script36_bp = Blueprint('script36', __name__)

# Premium A-to-Z High-DA Platform Blueprint Catalog
MASTER_BACKLINK_CATALOG = [
    {
        "id": "github",
        "site": "github.com",
        "da": 97,
        "type": "Profile / Repository Readme",
        "difficulty": "Easy",
        "steps": "1. Sign up on GitHub.com.\\n2. Edit your Public Profile Settings and add your link in the 'Website' block.\\n3. Create a public repository with the same name as your username.\\n4. Initialize README.md.\\n5. Add a hyperlink: [My Site](https://yourdomain.com) inside the README to build a highly indexed link."
    },
    {
        "id": "crunchbase",
        "site": "crunchbase.com",
        "da": 91,
        "type": "Company Profile Listing",
        "difficulty": "Medium",
        "steps": "1. Create an individual contributor account on Crunchbase.\\n2. Navigate to 'Add New Profile' -> 'Organization'.\\n3. Enter your brand details and input your full link in the primary website domain section.\\n4. Save and verify coordinates."
    },
    {
        "id": "medium",
        "site": "medium.com",
        "da": 95,
        "type": "Article Content Blogging",
        "difficulty": "Medium",
        "steps": "1. Log in to Medium via Google.\\n2. Click 'Write' to draft a high-quality article related to your niche (min 600 words).\\n3. Naturally insert contextual links using descriptive anchors.\\n4. Hit publish to instantly trigger Google indexes."
    },
    {
        "id": "dev_to",
        "site": "dev.to",
        "da": 92,
        "type": "Tech Web 2.0 Article",
        "difficulty": "Easy",
        "steps": "1. Register on Dev.to using GitHub or email.\\n2. Edit user dashboard bios to pin your custom website address.\\n3. Publish an educational technical resource post and embed redirection contextual keywords links."
    },
    {
        "id": "reddit",
        "site": "reddit.com",
        "da": 91,
        "type": "Social Bookmarking Link",
        "difficulty": "Medium",
        "steps": "1. Setup a clean Reddit profile.\\n2. Find relevant Subreddits matching your core industry parameters.\\n3. Answer a query comprehensively and append your domain address link as an organic research source citation."
    },
    {
        "id": "linkedin",
        "site": "linkedin.com",
        "da": 98,
        "type": "Corporate Company Page",
        "difficulty": "Easy",
        "steps": "1. Open LinkedIn Page builder engine.\\n2. Select 'Create Company Page'.\\n3. Input company details, tags, and fill out the official website field with your absolute URL."
    },
    {
        "id": "quora",
        "site": "quora.com",
        "da": 93,
        "type": "Q&A Authority Answer",
        "difficulty": "Easy",
        "steps": "1. Find trending open questions relevant to your industry vertical.\\n2. Write a descriptive multi-paragraph answer.\\n3. Hyperlink your platform domain text references naturally inside the body."
    },
    {
        "id": "hashnode",
        "site": "hashnode.dev",
        "da": 88,
        "type": "Developer Blog Node",
        "difficulty": "Medium",
        "steps": "1. Deploy a dynamic developer blog profile dashboard on Hashnode.\\n2. Write case studies or product changelogs, adding outbound hyperlinks directly to your operational server landing page nodes."
    },
    {
        "id": "tumblr",
        "site": "tumblr.com",
        "da": 95,
        "type": "Microblog Media Backlink",
        "difficulty": "Easy",
        "steps": "1. Create a dashboard instance blog inside Tumblr.\\n2. Select the 'Link' format block dynamically.\\n3. Type your primary root domain inside the address grid mapping array, add meta context text, and publish."
    }
]

def fetch_accurate_backlinks(target_domain):
    """
    Fetches actual real-time Google search indices using Serper.dev API
    To use this, get a free key from https://serper.dev
    """
    # ⚠️ APNI API KEY YAHAN DAALO
    SERPER_API_KEY = "YOUR_SERPER_API_KEY_HERE"
    
    if SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE" or not SERPER_API_KEY:
        # Fallback tracking indicator if key is missing
        return []

    url = "https://google.serper.dev/search"
    query = f'"{target_domain}" -site:{target_domain}'
    
    payload = {
        "q": query,
        "num": 40
    }
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    results = []
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            search_data = response.json()
            # Parse organic results safely
            for item in search_data.get('organic', []):
                link = item.get('link', '')
                title = item.get('title', 'Indexed Context Link')
                if link and target_domain not in link:
                    results.append({"title": title, "url": link})
        return results
    except Exception:
        return []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accurate Backlink Matrix Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #f9fafb; }
        .dashboard-card { background-color: #111827; border: 1px solid #1f2937; }
        .inner-input { background-color: #0b0f19; border: 1px solid #1f2937; color: #f9fafb; }
    </style>
</head>
<body class="min-h-screen antialiased font-sans">

    <header class="dashboard-card border-b px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4 shadow-2xl">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-sky-600 rounded-xl text-white shadow-lg shadow-sky-600/30">
                <i class="fa-solid fa-chart-network text-xl"></i>
            </div>
            <div>
                <h1 class="font-extrabold text-sm tracking-widest uppercase">Script36 Architecture</h1>
                <span class="text-[9px] block text-sky-400 font-mono font-bold tracking-wider">A-TO-Z SEO MATRIX PIPELINE</span>
            </div>
        </div>
        <div class="text-xs font-mono text-emerald-400"><i class="fa-solid fa-circle-check animate-pulse"></i> HIGHLY ACCURATE SEARCH API NODE</div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        
        <div class="dashboard-card p-6 rounded-2xl shadow-xl space-y-4">
            <h3 class="text-xs font-mono uppercase tracking-wider text-gray-400 font-bold">
                <i class="fa-solid fa-terminal text-sky-500 mr-2"></i> Targeted Link Auditing Console
            </h3>
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="siteUrlInput" placeholder="Apna domain enter karo (e.g., example.com)" value="mysite.com"
                       class="flex-1 px-4 py-3 text-xs font-mono rounded-xl inner-input focus:outline-none focus:border-sky-500">
                <button onclick="triggerVerificationPipeline()" class="px-6 py-3 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-sky-600/20">
                    ANALYZE ALL BACKLINKS
                </button>
            </div>
            <p id="apiKeyWarning" class="text-[11px] font-mono text-yellow-500 hidden"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Note: Please make sure you have added your Serper API Key in the python script for 100% accurate live scraping.</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="dashboard-card p-5 rounded-2xl flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider text-gray-400 block mb-1">Total Found Backlinks Count</span>
                    <span id="cntTotalLinks" class="text-3xl font-black font-mono text-emerald-400">0</span>
                </div>
                <div class="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl"><i class="fa-solid fa-link text-xl"></i></div>
            </div>
            <div class="dashboard-card p-5 rounded-2xl flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider text-gray-400 block mb-1">High-DA Unbuilt Targets</span>
                    <span id="cntMissing" class="text-3xl font-black font-mono text-yellow-500">0</span>
                </div>
                <div class="p-3 bg-yellow-500/10 text-yellow-500 rounded-xl"><i class="fa-solid fa-layer-group text-xl"></i></div>
            </div>
            <div class="dashboard-card p-5 rounded-2xl flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider text-gray-400 block mb-1">Audit Index Status</span>
                    <span id="cntStatus" class="text-lg font-black font-mono text-sky-400">IDLE PIPELINE</span>
                </div>
                <div class="p-3 bg-sky-500/10 text-sky-400 rounded-xl"><i class="fa-solid fa-microscope text-xl"></i></div>
            </div>
        </div>

        <div id="loadingWorkspace" class="hidden py-16 text-center text-xs font-mono text-gray-400">
            <i class="fa-solid fa-circle-notch animate-spin text-3xl text-sky-500 mb-4 block"></i>
            Executing index validation via API node... Fetching accurate live datasets... Please wait...
        </div>

        <div id="dataDashboardWrapper" class="grid grid-cols-1 lg:grid-cols-12 gap-6 hidden">
            
            <!-- LEFT SECTION: EXISTING TRACKING -->
            <div class="lg:col-span-5 dashboard-card rounded-2xl overflow-hidden flex flex-col justify-between shadow-2xl">
                <div>
                    <div class="px-5 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/40">
                        <h4 class="text-xs font-mono font-bold tracking-wider text-emerald-400"><i class="fa-solid fa-circle-nodes mr-1.5"></i> Live Referral Link Coordinates</h4>
                        <span class="text-[9px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded font-bold uppercase">LIVE COUNT</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left font-mono text-xs">
                            <thead class="bg-black/30 text-[10px] uppercase text-gray-400 border-b border-gray-800">
                                <tr>
                                    <th class="px-4 py-3">Source Anchor Context</th>
                                    <th class="px-4 py-3">Location Destination</th>
                                </tr>
                            </thead>
                            <tbody id="existingRowsContainer" class="divide-y divide-gray-800/60"></tbody>
                        </table>
                    </div>
                </div>
                <div class="p-3 bg-black/20 text-[9px] text-gray-500 font-mono">Live API indices validation layer analysis complete.</div>
            </div>

            <!-- RIGHT SECTION: EXHAUSTIVE TARGET CHECKS (A to Z BUILDER) -->
            <div class="lg:col-span-7 dashboard-card rounded-2xl overflow-hidden flex flex-col justify-between shadow-2xl">
                <div>
                    <div class="px-5 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/40">
                        <h4 class="text-xs font-mono font-bold tracking-wider text-yellow-400"><i class="fa-solid fa-map-location-dot mr-1.5"></i> A-to-Z High-DA Link Creation Playbook</h4>
                        <span class="text-[9px] font-mono bg-yellow-500/10 text-yellow-400 px-2 py-0.5 rounded font-bold uppercase">STRATEGY</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left font-mono text-xs">
                            <thead class="bg-black/30 text-[10px] uppercase text-gray-400 border-b border-gray-800">
                                <tr>
                                    <th class="px-4 py-3">Platform Domain Target</th>
                                    <th class="px-4 py-3">Trust Score (DA)</th>
                                    <th class="px-4 py-3">Link Architecture Category</th>
                                    <th class="px-4 py-3 text-center">Action Guide</th>
                                </tr>
                            </thead>
                            <tbody id="catalogOpportunitiesContainer" class="divide-y divide-gray-800/60"></tbody>
                        </table>
                    </div>
                </div>
                <div class="p-3 bg-black/20 text-[9px] text-gray-400 font-mono text-right"><i class="fa-solid fa-circle-info text-sky-400 mr-1"></i> Click 'Reveal Build Steps' to inspect structural setup guides.</div>
            </div>
        </div>
    </main>

    <!-- STEP BLUEPRINT MODAL -->
    <div id="modalInstructionsPopup" class="fixed inset-0 bg-black/80 backdrop-blur-xs z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-gray-900 border border-gray-800 w-full max-w-lg rounded-2xl overflow-hidden shadow-2xl p-6 space-y-4">
            <div class="flex justify-between items-start border-b border-gray-800 pb-3">
                <div>
                    <h3 id="lblTargetPlatform" class="text-sm font-bold font-mono text-sky-400">—</h3>
                    <span class="text-[9px] font-mono text-gray-500 tracking-wider block">PREMIUM BLUEPRINT STEP CONFIGURATION SYSTEM</span>
                </div>
                <button onclick="hideInstructionsPopup()" class="text-gray-400 hover:text-white p-1 text-sm cursor-pointer"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-4 text-xs font-mono">
                <div>
                    <span class="text-gray-500 text-[9px] uppercase font-bold tracking-widest block mb-1">Link Target Type Structure</span>
                    <div id="lblLinkType" class="bg-black/40 border border-gray-800 p-2 rounded-xl text-emerald-400 font-bold">—</div>
                </div>
                <div>
                    <span class="text-gray-500 text-[9px] uppercase font-bold tracking-widest block mb-1">A-to-Z Execution Procedure Steps</span>
                    <p id="lblStepGuidelines" class="bg-black/20 border border-gray-800 p-3.5 rounded-xl text-gray-300 leading-relaxed whitespace-pre-line text-[11px] font-sans">—</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let globalSuggestionsData = [];

        async function triggerVerificationPipeline() {
            const valDomain = document.getElementById('siteUrlInput').value.trim();
            if(!valDomain) return alert("Bhai, domain enter karo pehle!");

            document.getElementById('loadingWorkspace').classList.remove('hidden');
            document.getElementById('dataDashboardWrapper').classList.add('hidden');

            try {
                const formData = new FormData();
                formData.append('domain', valDomain);

                const response = await fetch('check-backlinks', { method: 'POST', body: formData });
                const data = await response.json();

                document.getElementById('loadingWorkspace').classList.add('hidden');
                document.getElementById('dataDashboardWrapper').classList.remove('hidden');

                if (data.is_mocked) {
                    document.getElementById('apiKeyWarning').classList.remove('hidden');
                } else {
                    document.getElementById('apiKeyWarning').classList.add('hidden');
                }

                const existingLinks = data.current_backlinks_found || [];
                globalSuggestionsData = data.where_to_create_suggestions || [];

                document.getElementById('cntTotalLinks').innerText = data.total_backlinks_count;
                document.getElementById('cntMissing').innerText = globalSuggestionsData.length;
                
                const statLabel = document.getElementById('cntStatus');
                if(existingLinks.length > 0 && !data.is_mocked) {
                    statLabel.innerText = "ACTIVE BACKLINKS";
                    statLabel.className = "text-lg font-black font-mono text-emerald-400";
                } else {
                    statLabel.innerText = "SETUP REQUIRED";
                    statLabel.className = "text-lg font-black font-mono text-amber-500";
                }

                const blockEx = document.getElementById('existingRowsContainer');
                blockEx.innerHTML = '';
                if(existingLinks.length === 0) {
                    blockEx.innerHTML = `<tr><td colspan="2" class="p-5 text-center text-gray-500 italic">No live record matches found. Please add API Key for real-time fetch.</td></tr>`;
                } else {
                    existingLinks.forEach(row => {
                        blockEx.innerHTML += `
                            <tr class="hover:bg-black/20 transition">
                                <td class="px-4 py-3.5 font-bold truncate max-w-[150px]">${row.title}</td>
                                <td class="px-4 py-3.5 text-sky-400 truncate max-w-[180px]"><a href="${row.url}" target="_blank" class="hover:underline">${row.url}</a></td>
                            </tr>
                        `;
                    });
                }

                const blockOpp = document.getElementById('catalogOpportunitiesContainer');
                blockOpp.innerHTML = '';
                globalSuggestionsData.forEach(row => {
                    blockOpp.innerHTML += `
                        <tr class="hover:bg-black/20 transition">
                            <td class="px-4 py-3.5 font-extrabold text-gray-200">${row.site}</td>
                            <td class="px-4 py-3.5 font-black text-emerald-400 text-sm">${row.da}</td>
                            <td class="px-4 py-3.5 text-[11px] font-medium text-gray-400">${row.type}</td>
                            <td class="px-4 py-3.5 text-center">
                                <button onclick="triggerPopupInspection('${row.id}')" class="px-2 py-1 border border-sky-500/30 text-sky-400 bg-sky-500/5 hover:bg-sky-500 hover:text-white rounded text-[10px] font-bold tracking-wider transition cursor-pointer">
                                    Reveal Build Steps
                                </button>
                            </td>
                        </tr>
                    `;
                });

            } catch(err) {
                document.getElementById('loadingWorkspace').classList.add('hidden');
                alert("Error handling pipeline: " + err.message);
            }
        }

        function triggerPopupInspection(targetId) {
            const datasetObj = globalSuggestionsData.find(x => x.id === targetId);
            if(!datasetObj) return;

            document.getElementById('lblTargetPlatform').innerText = `${datasetObj.site.toUpperCase()} (DA: ${datasetObj.da}/100)`;
            document.getElementById('lblLinkType').innerText = `${datasetObj.type} Setup`;
            document.getElementById('lblStepGuidelines').innerText = datasetObj.steps;

            document.getElementById('modalInstructionsPopup').classList.remove('hidden');
        }

        function hideInstructionsPopup() {
            document.getElementById('modalInstructionsPopup').classList.add('hidden');
        }
    </script>
</body>
</html>
'''

@script36_bp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@script36_bp.route('/check-backlinks', methods=['POST'])
def check_backlinks():
    raw_domain = request.form.get('domain', '').strip().lower()
    if not raw_domain:
        return jsonify({"current_backlinks_found": [], "where_to_create_suggestions": [], "total_backlinks_count": 0})
        
    clean_domain = raw_domain.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
    
    # Accurate Fetch Layer
    live_backlinks = fetch_accurate_backlinks(clean_domain)
    is_mocked = False
    
    # If API key is not configured yet, use structured simulation to prevent system crash
    if not live_backlinks:
        is_mocked = True
        live_backlinks = [
            {"title": f"Sample Profile Context (Configure API Key for live sync)", "url": f"https://github.com/sample-repo-link"},
            {"title": f"Sample Tech Blog Pointer Reference", "url": f"https://dev.to/sample-blog-post"}
        ]
        
    total_count = len(live_backlinks) if not is_mocked else 0
        
    # Process Remaining Opportunities
    final_suggestions = []
    found_urls_flattened = [link['url'].lower() for link in live_backlinks]
    
    for potential_target in MASTER_BACKLINK_CATALOG:
        is_already_created = any(potential_target['id'] in flat_url for flat_url in found_urls_flattened)
        if not is_already_created and not (is_mocked and potential_target['id'] in ['github', 'dev_to']):
            final_suggestions.append(potential_target)
            
    return jsonify({
        "target_domain": clean_domain,
        "current_backlinks_found": live_backlinks,
        "where_to_create_suggestions": final_suggestions,
        "total_backlinks_count": total_count,
        "is_mocked": is_mocked
    })

