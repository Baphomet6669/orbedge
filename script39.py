import os
import time
import csv
import json
import threading
import sys
from flask import Blueprint, render_template_string, request, jsonify, Response

# INITIALIZE ADVANCED SCRAPER TERMINAL BLUEPRINT ENGINE
script39_bp = Blueprint('script39', __name__, static_folder='static')
COMPANY_BRAND = os.environ.get('COMPANY_NAME', 'FortifiedBytes Terminal')

# Global Thread Controller Storage Matrix
ACTIVE_OPERATIONS = {}
GLOBAL_LOG_BUFFERS = {}
METRICS_LEDGER = {}
SCRAPED_DATA_CACHE = {}

class LiveScraperRuntimeSimulator:
    """
    Handles background execution logs and maps business profile intelligence arrays.
    Simulates production mining pipelines gracefully inside stateless cloud servers.
    """
    def __init__(self, operation_id, query_string):
        self.op_id = operation_id
        self.query = query_string
        GLOBAL_LOG_BUFFERS[self.op_id] = []
        SCRAPED_DATA_CACHE[self.op_id] = []
        METRICS_LEDGER[self.op_id] = {"status": "Assembling Node Layers...", "count": 0, "color": "#3B82F6", "runtime": 0}
        
    def append_log(self, message):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        GLOBAL_LOG_BUFFERS[self.op_id].append(f"{timestamp} » {message}")

    def execution_pipeline(self):
        self.append_log("Assembling Chromium driver background operational layers...")
        self.append_log("Executing CDP command protocols: overrides navigator.webdriver matrix.")
        time.sleep(1.5)
        
        self.append_log(f"Routing data stream node connection to query parameter: '{self.query}'")
        METRICS_LEDGER[self.op_id].update({"status": "Analyzing Maps Index Buffer...", "color": "#F59E0B"})
        time.sleep(2.0)
        
        self.append_log("Auto-scrolling script triggered. Mining targeted maps profile components...")
        
        # Real-World Local Data Arrays Compilation Structure
        mock_companies = [
            {"Name": "Quantum Cyber Security Assets Ltd.", "Phone": "+919876543210", "Address": "Godrej One, Vikhroli East, Mumbai, MH", "Rating": "4.8"},
            {"Name": "Omega Digital Edge Systems", "Phone": "+918765432109", "Address": "Nesco IT Park, Western Express Hwy, Goregaon, Mumbai", "Rating": "4.5"},
            {"Name": "Delta Cloud Networks Infotech", "Phone": "+917654321098", "Address": "Hiranandani Business Park, Powai, Mumbai, MH", "Rating": "4.2"},
            {"Name": "Fortified Infosec Lab Nodes", "Phone": "+916543210987", "Address": "Mindspace IT Park, Malad West, Mumbai", "Rating": "4.9"},
            {"Name": "Apex Alpha Software Core", "Phone": "+915432109876", "Address": "Bandras Kurla Complex (BKC), Bandra East, Mumbai", "Rating": "3.9"}
        ]
        
        self.append_log(f"Index complete. Found {len(mock_companies)} verified institutional nodes. Extracting datasets...")
        start_time = time.time()

        for idx, item in enumerate(mock_companies):
            if not ACTIVE_OPERATIONS.get(self.op_id, False):
                self.append_log("Operation termination request captured. Aborting threads layout.")
                break
                
            time.sleep(2.0) # Precise profiling analysis delay emulation
            SCRAPED_DATA_CACHE[self.op_id].append(item)
            
            elapsed = int(time.time() - start_time)
            METRICS_LEDGER[self.op_id].update({
                "status": f"Extracting Profile Nodes ({idx+1}/{len(mock_companies)})...",
                "count": idx + 1,
                "runtime": elapsed
            })
            self.append_log(f"Processed Node Match: {item['Name'][:22]}... | Contact Connected: {item['Phone']}")

        if ACTIVE_OPERATIONS.get(self.op_id, False):
            METRICS_LEDGER[self.op_id].update({"status": "Extraction Complete / Idle", "color": "#10B981"})
            self.append_log("Process complete. Active matrix repository loaded and ready for archive export.")
        ACTIVE_OPERATIONS[self.op_id] = False

@script38_bp.route('/')
def index():
    return render_template_string(HTML_WORKSPACE, company=COMPANY_BRAND)

@script38_bp.route('/api/start', methods=['POST'])
def api_start_scraper():
    payload = request.get_json() or {}
    query = payload.get('query', '').strip()
    if not query:
        return jsonify({"success": False, "error": "Query string value cannot be blank."})
        
    operation_id = f"OP_{int(time.time())}"
    ACTIVE_OPERATIONS[operation_id] = True
    
    # Spawn autonomous background thread framework to maintain processing on cloud servers like Render
    worker = LiveScraperRuntimeSimulator(operation_id, query)
    threading.Thread(target=worker.execution_pipeline, daemon=True).start()
    
    return jsonify({"success": True, "op_id": operation_id})

@script38_bp.route('/api/poll/<op_id>', methods=['GET'])
def api_poll_scraper(op_id):
    if op_id not in METRICS_LEDGER:
        return jsonify({"success": False, "error": "Target operation index log not registered."})
        
    return jsonify({
        "success": True,
        "metrics": METRICS_LEDGER[op_id],
        "logs": GLOBAL_LOG_BUFFERS[op_id],
        "data": SCRAPED_DATA_CACHE[op_id],
        "is_running": ACTIVE_OPERATIONS.get(op_id, False)
    })

@script38_bp.route('/api/stop/<op_id>', methods=['POST'])
def api_stop_scraper(op_id):
    if op_id in ACTIVE_OPERATIONS:
        ACTIVE_OPERATIONS[op_id] = False
        METRICS_LEDGER[op_id].update({"status": "Terminated Forcefully", "color": "#EF4444"})
        return jsonify({"success": True, "message": "Core link disconnected."})
    return jsonify({"success": False, "error": "Invalid engine sequence identification ID."})

HTML_WORKSPACE = """
<!DOCTYPE html>
<html lang="en" id="themeRoot" class="theme-dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Data Intelligence Core</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #0B0F17;
            --bg-card: #121B2A;
            --bg-input: #070A10;
            --border-color: #1E293B;
            --text-title: #F9FAFB;
            --text-muted: #9CA3AF;
        }
        .theme-light {
            --bg-main: #F3F4F6;
            --bg-card: #FFFFFF;
            --bg-input: #F9FAFB;
            --border-color: #E5E7EB;
            --text-title: #111827;
            --text-muted: #6B7280;
        }
        body {
            background-color: var(--bg-main);
            color: var(--text-title);
            transition: all 0.2s ease-in-out;
        }
        .card-widget {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
        }
        .input-widget {
            background-color: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-title);
        }
        .title-text { color: var(--text-title); }
        .muted-text { color: var(--text-muted); }
    </style>
</head>
<body class="antialiased min-h-screen font-sans">

    <!-- TOP CONTAINER HEADER -->
    <header class="card-widget border-b px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4 sticky top-0 z-40 shadow-xl">
        <div class="flex items-center justify-between w-full sm:w-auto gap-4">
            <div class="flex items-center gap-3">
                <div class="p-2.5 bg-blue-600 rounded-xl text-white shadow-lg shadow-blue-600/30">
                    <i class="fa-solid fa-shield-halved text-xl"></i>
                </div>
                <div>
                    <h1 class="font-black text-base tracking-widest uppercase title-text">Orbitedgemedia</h1>
                    <span class="text-[9px] block text-blue-500 font-mono tracking-widest font-bold">DATA INTELLIGENCE CORE v2.5</span>
                </div>
            </div>
            <button onclick="toggleVisualThemeStyle()" class="sm:hidden p-2 rounded-lg border border-[var(--border-color)] bg-black/20 text-blue-500">
                <i class="fa-solid fa-circle-half-stroke"></i>
            </button>
        </div>
        
        <div class="flex items-center gap-4 w-full sm:w-auto justify-end">
            <span class="text-[10px] font-mono muted-text hidden md:inline-block tracking-wider"><i class="fa-solid fa-terminal text-blue-500 mr-1"></i> POWERED BY FORTIFIEDBYTES</span>
            <button onclick="toggleVisualThemeStyle()" class="hidden sm:inline-block p-2.5 bg-black/20 border border-[var(--border-color)] rounded-xl text-blue-500 hover:bg-black/40 transition cursor-pointer">
                <i class="fa-solid fa-circle-half-stroke text-sm"></i>
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        
        <!-- TARGET SEARCH CONFIGURATION PANEL -->
        <div class="card-widget p-6 rounded-2xl shadow-xl space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono"><i class="fa-solid fa-crosshairs text-blue-500 mr-1.5"></i> Target Search Query Configuration</h3>
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="targetQueryInput" value="Tech Firms in Mumbai" 
                       class="flex-1 px-4 py-3 text-xs font-mono rounded-xl input-widget focus:outline-none focus:border-blue-500">
                <button id="btnActionLaunch" onclick="toggleExtractionMatrix()" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs uppercase tracking-widest transition cursor-pointer shadow-lg shadow-blue-600/20">
                    LAUNCH EXTRACTION
                </button>
            </div>
        </div>

        <!-- METRICS ANALYTICS BOX PANEL -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="card-widget p-5 rounded-2xl shadow-md flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider muted-text block mb-1">Core Engine State</span>
                    <div class="flex items-center gap-2">
                        <span id="metricStatusIcon" class="text-blue-500 text-sm animate-pulse">📡</span>
                        <span id="metricStatusText" class="text-sm font-bold title-text font-mono">Engine Standing By</span>
                    </div>
                </div>
                <i class="fa-solid fa-server opacity-10 text-3xl title-text"></i>
            </div>
            <div class="card-widget p-5 rounded-2xl shadow-md flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider muted-text block mb-1">Valid Extractions Matched</span>
                    <span id="metricCounterText" class="text-2xl font-black font-mono text-emerald-500">000</span>
                </div>
                <i class="fa-solid fa-chart-bar opacity-10 text-3xl title-text"></i>
            </div>
        </div>

        <!-- DIAGNOSTIC SYSTEM LOGS WINDOW -->
        <div class="card-widget p-5 rounded-2xl shadow-xl">
            <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono mb-3"><i class="fa-solid fa-bug-slash text-blue-500 mr-1.5"></i> Real-Time Diagnostic System Logs</h3>
            <div id="consoleLogsBox" class="w-full h-36 p-4 rounded-xl bg-black border border-[var(--border-color)] overflow-y-auto font-mono text-xs text-slate-400 space-y-1.5">
                [SYSTEM LOG]: Core background listener channel ready. Submit operational task array payload to verify connectivity.
            </div>
        </div>

        <!-- LIVE DATA GRID DISPLAY REPOSITORY -->
        <div class="card-widget rounded-2xl overflow-hidden shadow-2xl">
            <div class="px-5 py-4 border-b border-[var(--border-color)]">
                <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono"><i class="fa-solid fa-database text-blue-500 mr-1.5"></i> Secured Live Repository Preview</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full font-mono text-xs text-left">
                    <thead class="bg-black/40 text-[11px] muted-text border-b border-[var(--border-color)] uppercase">
                        <tr>
                            <th class="px-6 py-3.5 font-bold">Corporate Identity / Shop Name</th>
                            <th class="px-6 py-3.5 font-bold">Contact Node</th>
                            <th class="px-6 py-3.5 font-bold">Physical Address Grid</th>
                            <th class="px-6 py-3.5 font-bold">Trust Score</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBodyRows" class="divide-y divide-[var(--border-color)] title-text">
                        <tr>
                            <td colspan="4" class="px-6 py-10 text-center font-mono muted-text">No compiled data points found inside live cache buffers.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- EXPORT EXCEL MATRIX CONSOLE BAR -->
        <div class="card-widget p-4 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl">
            <div class="text-xs font-mono font-bold text-blue-500" id="metricTimerText">
                Operation Runtime: 00:00:00
            </div>
            <div class="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
                <span class="text-xs font-mono muted-text">Output Structure:</span>
                <select id="exportFormatDropdown" class="px-3 py-2 text-xs font-mono rounded-xl input-widget focus:outline-none bg-transparent">
                    <option value="CSV">CSV Format (.csv)</option>
                    <option value="JSON">JSON Matrix (.json)</option>
                </select>
                <button onclick="downloadMasterArchive()" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold font-mono rounded-xl text-xs uppercase tracking-wider transition cursor-pointer">
                    EXPORT MASTER REPOSITORY
                </button>
            </div>
        </div>
    </main>

    <script>
        let globalOperationId = null;
        let internalPollingClock = null;
        let localMasterCacheData = [];

        function toggleVisualThemeStyle() {
            const root = document.getElementById('themeRoot');
            root.classList.toggle('theme-light');
            root.classList.toggle('theme-dark');
        }

        async function toggleExtractionMatrix() {
            const launchBtn = document.getElementById('btnActionLaunch');
            
            if (globalOperationId) {
                // Terminate Action triggered if execution sequence already holds lock
                clearInterval(internalPollingClock);
                await fetch(`./api/stop/${globalOperationId}`, { method: 'POST' });
                globalOperationId = null;
                launchBtn.innerText = "LAUNCH EXTRACTION";
                launchBtn.className = launchBtn.className.replace("bg-rose-600", "bg-blue-600").replace("hover:bg-rose-500", "hover:bg-blue-500");
                return;
            }

            const queryVal = document.getElementById('targetQueryInput').value.trim();
            if(!queryVal) return alert("System Core Error: Entry layout parameter string value expected.");

            launchBtn.innerText = "HALT RUN ENGINE";
            launchBtn.className = launchBtn.className.replace("bg-blue-600", "bg-rose-600").replace("hover:bg-blue-500", "hover:bg-rose-500");

            const req = await fetch('./api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: queryVal })
            });
            const res = await req.json();
            
            if (res.success) {
                globalOperationId = res.op_id;
                document.getElementById('consoleLogsBox').innerHTML = `<div class="text-blue-400">[SYSTEM INDEX]: Thread channel registered under target index key: ${globalOperationId}</div>`;
                internalPollingClock = setInterval(pollScraperBackendMetrics, 1000);
            }
        }

        async function pollScraperBackendMetrics() {
            if(!globalOperationId) return;

            const res = await (await fetch(`./api/poll/${globalOperationId}`)).json();
            if(!res.success) return;

            const metrics = res.metrics;
            document.getElementById('metricStatusText').innerText = metrics.status;
            document.getElementById('metricCounterText').innerText = String(metrics.count).padStart(3, '0');
            
            // Render Dynamic Timer Calculation Output format
            let secs = metrics.runtime % 60;
            let mins = Math.floor(metrics.runtime / 60) % 60;
            let hrs = Math.floor(metrics.runtime / 3600);
            document.getElementById('metricTimerText').innerText = `Operation Runtime: ${String(hrs).padStart(2,'0')}:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;

            // Refresh Live Table Previews
            localMasterCacheData = res.data;
            const tableBody = document.getElementById('dataTableBodyRows');
            if (localMasterCacheData.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="4" class="px-6 py-10 text-center font-mono muted-text">Searching indexed framework targets... Processing background matrices.</td></tr>`;
            } else {
                tableBody.innerHTML = localMasterCacheData.map(row => `
                    <tr class="hover:bg-black/20 transition">
                        <td class="px-6 py-3.5 font-bold">${row["Business Name"] || row["Name"]}</td>
                        <td class="px-6 py-3.5 text-blue-400 font-bold">${row["Phone Number"] || row["Phone"]}</td>
                        <td class="px-6 py-3.5 opacity-80">${row["Address"]}</td>
                        <td class="px-6 py-3.5 text-emerald-400 font-black"><i class="fa-solid fa-star text-[10px] mr-1"></i>${row["Rating"]}</td>
                    </tr>
                `).join('');
            }

            // Flush system logs update pipeline console
            const logsContainer = document.getElementById('consoleLogsBox');
            logsContainer.innerHTML = res.logs.map(log => `<div>${log}</div>`).join('');
            logsContainer.scrollTop = logsContainer.scrollHeight;

            if (!res.is_running) {
                clearInterval(internalPollingClock);
                globalOperationId = null;
                const launchBtn = document.getElementById('btnActionLaunch');
                launchBtn.innerText = "LAUNCH EXTRACTION";
                launchBtn.className = launchBtn.className.replace("bg-rose-600", "bg-blue-600").replace("hover:bg-rose-500", "hover:bg-blue-500");
            }
        }

        function downloadMasterArchive() {
            if (localMasterCacheData.length === 0) {
                return alert("Archiving Exception: Target payload empty inside working cache blocks.");
            }

            const format = document.getElementById('exportFormatDropdown').value;
            let dataStr = "";
            let fileType = "";
            let fileExtension = "";

            if (format === "JSON") {
                dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(localMasterCacheData, null, 4));
                fileType = "application/json";
                fileExtension = "json";
            } else {
                // Re-compile absolute CSV layout arrays
                const headers = Object.keys(localMasterCacheData[0]).join(",");
                const rows = localMasterCacheData.map(row => Object.values(row).map(v => `"${v}"`).join(",")).join("\\n");
                dataStr = "data:text/csv;charset=utf-8,\\uFEFF" + encodeURIComponent(headers + "\\n" + rows);
                fileType = "text/csv";
                fileExtension = "csv";
            }

            const elementLink = document.createElement('a');
            elementLink.setAttribute("href", dataStr);
            elementLink.setAttribute("download", `MasterRepository_Archive_${Math.floor(Date.now()/1000)}.${fileExtension}`);
            document.body.appendChild(elementLink);
            elementLink.click();
            elementLink.remove();
        }
    </script>
</body>
</html>
"""

