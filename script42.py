import os
import json
import time
import math
import random
from datetime import datetime
from flask import Blueprint, render_template_string, request, jsonify, session

# =========================================================================
# FLASK BLUEPRINT ARCHITECTURE DEFINITION
# =========================================================================
script42_bp = Blueprint('script42', __name__)

# =========================================================================
# HELPER DATA INTERFACES & ALGORITHMS (MOCK & CALCULATION ENGINE)
# =========================================================================
MODIFIERS = ["best", "top", "how to", "guide", "tutorial", "services", "near me", "price", "reviews", "vs"]
INTENT_TYPES = ["Informational", "Commercial", "Transactional", "Navigational"]

def generate_keyword_metrics(base_keyword, idx):
    """Calculates algorithmic keyword intelligence metrics based on base entropy"""
    random.seed(hash(base_keyword) + idx)
    
    # Volume calculation based on seed string properties
    base_val = len(base_keyword) * 450
    volume = int(base_val * random.uniform(0.5, 3.5))
    volume = max(50, (volume // 50) * 50) # round to nearest 50
    
    # CPC Calculation
    cpc = round(random.uniform(0.45, 12.80), 2)
    
    # Difficulty Metrics (0 - 100)
    difficulty = int((hash(base_keyword + str(idx)) % 85) + 10)
    
    if difficulty < 30:
        kd_status = "Easy"
        kd_css = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    elif difficulty < 65:
        kd_status = "Medium"
        kd_css = "bg-amber-500/10 text-amber-400 border-amber-500/20"
    else:
        kd_status = "Hard"
        kd_css = "bg-rose-500/10 text-rose-400 border-rose-500/20"
        
    intent = random.choice(INTENT_TYPES)
    if any(x in base_keyword for x in ["buy", "price", "services"]):
        intent = "Transactional"
    elif any(x in base_keyword for x in ["how", "what", "guide"]):
        intent = "Informational"

    return {
        "keyword": base_keyword,
        "volume": volume,
        "cpc": f"${cpc}",
        "difficulty": difficulty,
        "kd_status": kd_status,
        "kd_css": kd_css,
        "intent": intent
    }

# =========================================================================
# CONTROLLER GATEWAY ROUTING
# =========================================================================
@script42_bp.route('/')
def index():
    if 'logged_in' not in session:
        return "<h3>ACCESS DENIED: Please authorize session at dashboard gateway.</h3>", 403
    return render_template_string(UI_LAYOUT)

@script42_bp.route('/api/research', methods=['POST'])
def process_keyword_research():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized Terminal Activation"}), 401
        
    seed = request.form.get('keyword', '').strip()
    if not seed:
        return jsonify({"success": False, "message": "Seed keyword parameters empty."})

    results = []
    # 1. Main seed metrics injection
    results.append(generate_keyword_metrics(seed, 0))
    
    # 2. Advanced variation modifier processing loop
    for i, mod in enumerate(MODIFIERS):
        kw_variation = f"{mod} {seed}" if i % 2 == 0 else f"{seed} {mod}"
        results.append(generate_keyword_metrics(kw_variation, i + 1))
        
    return jsonify({"success": True, "type": "research", "results": results})

@script42_bp.route('/api/difficulty', methods=['POST'])
def check_keyword_difficulty():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized Terminal Activation"}), 401
        
    target_kw = request.form.get('keyword', '').strip()
    if not target_kw:
        return jsonify({"success": False, "message": "Target keyword parameter empty."})

    metrics = generate_keyword_metrics(target_kw, 99)
    
    # Backlink audit estimations matrix
    serp_competition = []
    domains = ["wikipedia.org", "forbes.com", "medium.com", "reddit.com", "techradar.com"]
    
    for i in range(5):
        da = int(95 - (i * random.randint(5, 15)))
        links = int((metrics["difficulty"] * 12) / (i + 1))
        serp_competition.append({
            "rank": i + 1,
            "url": f"https://www.{random.choice(domains)}/seo-guide-{target_kw.lower().replace(' ', '-')}",
            "da": max(10, da),
            "backlinks": max(1, links)
        })

    return jsonify({
        "success": True,
        "type": "difficulty",
        "metrics": metrics,
        "serp": serp_competition
    })

@script42_bp.route('/api/cluster', methods=['POST'])
def cluster_keywords_engine():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized Terminal Activation"}), 401
        
    raw_keywords = request.form.get('keywords_list', '').strip()
    if not raw_keywords:
        return jsonify({"success": False, "message": "Keywords list data matrix missing."})

    keywords = [k.strip() for k in raw_keywords.split('\n') if k.strip()]
    
    # Dynamic Similarity Intent Clustering Algorithm logic
    clusters = {}
    
    for idx, kw in enumerate(keywords):
        words = set(kw.lower().split())
        matched_cluster = None
        
        # Check against existing cluster pillars
        for pillar in clusters.keys():
            pillar_words = set(pillar.lower().split())
            # If intersection sharing words >= 1, group them together dynamically
            if words.intersection(pillar_words):
                matched_cluster = pillar
                break
                
        if matched_cluster:
            clusters[matched_cluster].append(generate_keyword_metrics(kw, idx))
        else:
            clusters[kw] = [generate_keyword_metrics(kw, idx)]

    formatted_clusters = []
    for pillar, items in clusters.items():
        total_vol = sum(item["volume"] for item in items)
        avg_kd = sum(item["difficulty"] for item in items) // len(items)
        formatted_clusters.append({
            "pillar": pillar.upper(),
            "count": len(items),
            "total_volume": total_vol,
            "avg_kd": avg_kd,
            "keywords": items
        })

    return jsonify({"success": True, "type": "cluster", "clusters": formatted_clusters})

# =========================================================================
# GLOWING NEON CYBER-PUNK TACTICAL KEYWORD UI SUITE
# =========================================================================
UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Keyword Intelligence Terminal</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f3f4f6; }
        .heading-font { font-family: 'Space Grotesk', sans-serif; }
        .cyber-card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.04); }
        .tab-btn.active { background-color: #4f46e5; color: #ffffff; border-color: #6366f1; }
        .terminal-block { font-family: 'Courier New', monospace; background: #070a14; }
    </style>
</head>
<body class="antialiased selection:bg-indigo-600 selection:text-white">

    <div class="max-w-[1600px] mx-auto p-4 md:p-8 space-y-6">
        
        <!-- HEADER MODULE TOP BAR -->
        <div class="cyber-card p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-4 border-l-4 border-l-indigo-600 shadow-xl">
            <div>
                <h1 class="text-xl md:text-2xl font-bold heading-font tracking-wide text-white"><i class="fa-solid fa-wand-magic-sparkles text-indigo-500 mr-1"></i> SEO Keyword Intelligence & Clustering Engine</h1>
                <p class="text-xs text-slate-400 mt-1 font-mono uppercase tracking-widest">Ecosystem Matrix: Module 42 Active & Ready for Data Ingestion</p>
            </div>
            <a href="/" class="bg-slate-900 border border-slate-800 text-slate-300 text-xs px-4 py-2 rounded-xl hover:bg-slate-800 transition font-medium"><i class="fa-solid fa-arrow-left-long mr-1.5"></i> Back to Control Deck</a>
        </div>

        <!-- NAVIGATION CONTROL TABS SYSTEM -->
        <div class="flex flex-wrap gap-2 bg-slate-950/60 p-2 rounded-2xl border border-slate-900">
            <button onclick="switchContextTab('research')" id="btn-tab-research" class="tab-btn active px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider cursor-pointer border border-transparent transition flex items-center gap-2"><i class="fa-solid fa-magnifying-glass text-sm"></i> Keyword Research Tool</button>
            <button onclick="switchContextTab('difficulty')" id="btn-tab-difficulty" class="tab-btn text-slate-400 hover:text-white px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider cursor-pointer border border-transparent transition flex items-center gap-2"><i class="fa-solid fa-gauge-high text-sm"></i> Difficulty Checker</button>
            <button onclick="switchContextTab('cluster')" id="btn-tab-cluster" class="tab-btn text-slate-400 hover:text-white px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider cursor-pointer border border-transparent transition flex items-center gap-2"><i class="fa-solid fa-network-wired text-sm"></i> Clustering Intelligence</button>
        </div>

        <!-- MODULE CONTAINERS INTERACTION DECK -->
        <div class="cyber-card p-6 rounded-2xl">
            
            <!-- PANEL 1: KEYWORD RESEARCH -->
            <div id="panel-research" class="space-y-4">
                <form onsubmit="executeKeywordPipeline(event, '/script42/api/research', 'researchForm')" id="researchForm" class="space-y-3">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider">Seed Target Keyword Phrase</label>
                    <div class="flex gap-3">
                        <input type="text" name="keyword" required placeholder="e.g., floor cleaning machine, digital marketing academy" class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono">
                        <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-6 rounded-xl transition shadow-lg shrink-0 cursor-pointer">Fetch Variations Matrix</button>
                    </div>
                </form>
            </div>

            <!-- PANEL 2: DIFFICULTY CHECKER -->
            <div id="panel-difficulty" class="space-y-4 hidden">
                <form onsubmit="executeKeywordPipeline(event, '/script42/api/difficulty', 'difficultyForm')" id="difficultyForm" class="space-y-3">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider">Analyze Single Keyword Difficulty Vector</label>
                    <div class="flex gap-3">
                        <input type="text" name="keyword" required placeholder="e.g., best black hat cybersecurity training in india" class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono">
                        <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-6 rounded-xl transition shadow-lg shrink-0 cursor-pointer">Analyze SERP Barrier</button>
                    </div>
                </form>
            </div>

            <!-- PANEL 3: KEYWORD CLUSTERING -->
            <div id="panel-cluster" class="space-y-4 hidden">
                <form onsubmit="executeKeywordPipeline(event, '/script42/api/cluster', 'clusterForm')" id="clusterForm" class="space-y-3">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider">Paste Raw Keywords Set (One per newline segment)</label>
                    <textarea name="keywords_list" required rows="6" placeholder="python framework&#10;python django tutorial&#10;flask vs django&#10;seo auditing tools&#10;best seo software" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"></textarea>
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wider px-6 py-3 rounded-xl transition shadow-lg cursor-pointer">Process Intent Clustering Mapping</button>
                </form>
            </div>

        </div>

        <!-- DYNAMIC COMPILED DASHBOARD INGESTION PORTAL (HIDDEN AT STARTUP) -->
        <div id="responseSuiteOutput" class="hidden space-y-6">
            
            <!-- RESEARCH / DYNAMIC VIEWPORTS DISPLAY GRID -->
            <div id="view-research-results" class="hidden cyber-card rounded-2xl overflow-hidden shadow-xl">
                <div class="p-4 bg-slate-900/40 border-b border-slate-800"><h3 class="font-bold text-xs uppercase tracking-widest text-slate-400 font-mono">Keyword Expansion Engine Database Matrix</h3></div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse text-xs min-w-[800px]">
                        <thead>
                            <tr class="text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px] bg-slate-950/40 font-mono">
                                <th class="p-4">Target Phrase Variation</th><th class="p-4">Search Volume (Mo.)</th><th class="p-4">CPC Value Target</th><th class="p-4">Intent Classification</th><th class="p-4 text-center">Keyword Difficulty Level</th>
                            </tr>
                        </thead>
                        <tbody id="researchTableBody" class="divide-y divide-slate-800/40"></tbody>
                    </table>
                </div>
            </div>

            <!-- DIFFICULTY DETAILED GRAPH MATRIX VIEWPORT -->
            <div id="view-difficulty-results" class="hidden grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="cyber-card p-5 rounded-2xl h-fit space-y-4">
                    <h3 class="font-bold text-sm text-white heading-font border-b border-slate-800 pb-2">Target Metrics Card</h3>
                    <div id="diff-score-badge" class="p-6 rounded-xl text-center space-y-1 border">
                        <span class="text-[10px] uppercase font-bold tracking-widest block text-slate-400">Difficulty Gauge</span>
                        <h2 id="diff-score-num" class="text-3xl font-extrabold font-mono text-white">0</h2>
                        <span id="diff-score-status" class="inline-block text-[10px] uppercase font-bold tracking-wider mt-1 px-2.5 py-0.5 rounded-full">N/A</span>
                    </div>
                    <div class="grid grid-cols-2 gap-3 text-xs font-mono">
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-900"><span class="text-[9px] uppercase text-slate-500 block">Est. Volume</span><span id="diff-vol" class="text-white font-bold text-sm">0</span></div>
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-900"><span class="text-[9px] uppercase text-slate-500 block">CPC Factor</span><span id="diff-cpc" class="text-white font-bold text-sm">$0.00</span></div>
                    </div>
                </div>
                <div class="lg:col-span-2 cyber-card p-5 rounded-2xl space-y-4">
                    <h3 class="font-bold text-sm text-white heading-font border-b border-slate-800 pb-2"><i class="fa-solid fa-list-ol text-indigo-400 mr-1"></i> Competitor SERP Domain Matrix Mapping Links</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="text-slate-400 border-b border-slate-800 uppercase text-[10px] font-mono font-bold">
                                    <th class="pb-2">Rank Node</th><th class="pb-2">Target Landing Page URL Address</th><th class="pb-2 text-center">Domain Auth (DA)</th><th class="pb-2 text-right">Backlink Volume</th>
                                </tr>
                            </thead>
                            <tbody id="difficultySerpBody" class="divide-y divide-slate-800/40"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- CLUSTERING PILLARS GRID SYSTEM DISPLAY -->
            <div id="view-cluster-results" class="hidden space-y-4"></div>

        </div>
    </div>

    <script>
        function switchContextTab(tabKey) {
            // Reset input panel state wrappers
            document.getElementById('panel-research').classList.add('hidden');
            document.getElementById('panel-difficulty').classList.add('hidden');
            document.getElementById('panel-cluster').classList.add('hidden');
            
            document.getElementById(`panel-${tabKey}`).classList.remove('hidden');

            // Reset navigation layouts highlights
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active', 'text-white');
                btn.classList.add('text-slate-400');
            });
            document.getElementById(`btn-tab-${tabKey}`).classList.add('active', 'text-white');
        }

        async function executeKeywordPipeline(e, endpointUrl, formId) {
            e.preventDefault();
            const outSuite = document.getElementById('responseSuiteOutput');
            
            // Wipe response sub-viewports cleanly before processing fresh pipeline arrays
            document.getElementById('view-research-results').classList.add('hidden');
            document.getElementById('view-difficulty-results').classList.add('hidden');
            document.getElementById('view-cluster-results').classList.add('hidden');

            let fd = new FormData(document.getElementById(formId));

            try {
                let response = await fetch(endpointUrl, { method: 'POST', body: fd });
                let data = await response.json();

                if (data.success) {
                    outSuite.classList.remove('hidden');

                    if (data.type === 'research') {
                        let tbody = document.getElementById('researchTableBody');
                        tbody.innerHTML = '';
                        data.results.forEach(item => {
                            tbody.innerHTML += `
                            <tr class="hover:bg-slate-900/30 transition font-mono text-xs">
                                <td class="p-4 font-bold text-white">${item.keyword}</td>
                                <td class="p-4 text-slate-300">${item.volume.toLocaleString()}</td>
                                <td class="p-4 text-indigo-400 font-semibold">${item.cpc}</td>
                                <td class="p-4 text-slate-400"><span class="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-[11px]">${item.intent}</span></td>
                                <td class="p-4 text-center"><span class="border px-2.5 py-0.5 rounded text-[10px] font-bold ${item.kd_css}">${item.kd_status} (${item.difficulty})</span></td>
                            </tr>`;
                        });
                        document.getElementById('view-research-results').classList.remove('hidden');
                    } 
                    else if (data.type === 'difficulty') {
                        document.getElementById('diff-score-num').innerText = data.metrics.difficulty;
                        document.getElementById('diff-score-status').className = `inline-block text-[10px] uppercase font-bold tracking-wider mt-1 px-2.5 py-0.5 rounded-full ${data.metrics.kd_css}`;
                        document.getElementById('diff-score-status').innerText = data.metrics.kd_status;
                        document.getElementById('diff-score-badge').className = `p-6 rounded-xl text-center space-y-1 border ${data.metrics.kd_css.split(' ')[2] || 'border-slate-800'}`;
                        document.getElementById('diff-vol').innerText = data.metrics.volume.toLocaleString();
                        document.getElementById('diff-cpc').innerText = data.metrics.cpc;

                        let serpBody = document.getElementById('difficultySerpBody');
                        serpBody.innerHTML = '';
                        data.serp.forEach(row => {
                            serpBody.innerHTML += `
                            <tr class="hover:bg-slate-900/30 font-mono text-[11px]">
                                <td class="py-3 text-indigo-400 font-bold"># ${row.rank}</td>
                                <td class="py-3 text-slate-300 truncate max-w-xs md:max-w-xl" title="${row.url}">${row.url}</td>
                                <td class="py-3 text-center text-slate-400 font-bold">${row.da}</td>
                                <td class="py-3 text-right text-emerald-400 font-bold">${row.backlinks.toLocaleString()}</td>
                            </tr>`;
                        });
                        document.getElementById('view-difficulty-results').classList.remove('hidden');
                    }
                    else if (data.type === 'cluster') {
                        let clusterDeck = document.getElementById('view-cluster-results');
                        clusterDeck.innerHTML = '';
                        
                        data.clusters.forEach((c, cIdx) => {
                            let itemRows = c.keywords.map(kw => `
                                <div class="flex justify-between items-center bg-slate-950/40 p-2.5 rounded-lg border border-slate-900/50 text-xs font-mono">
                                    <span class="text-slate-200 font-medium">${kw.keyword}</span>
                                    <div class="flex items-center gap-4 text-[11px]">
                                        <span class="text-slate-400">Vol: ${kw.volume.toLocaleString()}</span>
                                        <span class="text-indigo-400">${kw.cpc}</span>
                                        <span class="font-bold border px-1.5 py-0.2 rounded text-[10px] ${kw.kd_css}">${kw.difficulty}</span>
                                    </div>
                                </div>
                            `).join('');

                            clusterDeck.innerHTML += `
                            <div class="cyber-card p-5 rounded-2xl border-t-4 border-t-indigo-500 space-y-3">
                                <div class="flex justify-between items-center border-b border-slate-800 pb-2.5 flex-wrap gap-2">
                                    <div>
                                        <h4 class="font-bold text-xs heading-font text-white tracking-wider font-mono uppercase"><i class="fa-solid fa-folder-tree text-indigo-400 mr-1.5"></i> Cluster Pillar: ${c.pillar}</h4>
                                        <span class="text-[10px] text-slate-400 font-mono">Contains ${c.count} Linked Long-Tail Semantic Queries</span>
                                    </div>
                                    <div class="flex gap-3 text-[11px] font-mono">
                                        <span class="bg-slate-950 px-2 py-1 rounded border border-slate-900 text-slate-300">Cluster Vol: <b>${c.total_volume.toLocaleString()}</b></span>
                                        <span class="bg-slate-950 px-2 py-1 rounded border border-slate-900 text-purple-400">Avg KD: <b>${c.avg_kd}</b></span>
                                    </div>
                                </div>
                                <div class="space-y-2 max-h-60 overflow-y-auto pr-1">${itemRows}</div>
                            </div>`;
                        });
                        document.getElementById('view-cluster-results').classList.remove('hidden');
                    }

                    window.scrollTo({ top: outSuite.offsetTop - 60, behavior: 'smooth' });
                } else {
                    alert(data.message || "Pipeline integration fields execution fault.");
                }
            } catch (err) {
                console.error("Pipeline breakdown processing exception:", err);
                alert("Terminal context mapping timeout drop.");
            }
        }
    </script>
</body>
</html>
"""
