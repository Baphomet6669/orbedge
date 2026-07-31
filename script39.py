import os
import time
import json
import threading
import re
from flask import Flask, Blueprint, render_template_string, request, jsonify
from playwright.sync_api import sync_playwright

# Flask App Initialization
app = Flask(__name__)
script39_bp = Blueprint('script39', __name__, static_folder='static')
COMPANY_BRAND = os.environ.get('COMPANY_NAME', 'Data Mining Terminal')

# Global Thread Controller Storage Matrix
ACTIVE_OPERATIONS = {}
GLOBAL_LOG_BUFFERS = {}
METRICS_LEDGER = {}
SCRAPED_DATA_CACHE = {}

class RealPlaywrightMapsScraper:
    """
    Directly automates a browser via Playwright to scrape real live data 
    from Google Maps without any API keys.
    """
    def __init__(self, operation_id, query_string):
        self.op_id = operation_id
        self.query = query_string.strip()
        GLOBAL_LOG_BUFFERS[self.op_id] = []
        SCRAPED_DATA_CACHE[self.op_id] = []
        METRICS_LEDGER[self.op_id] = {
            "status": "Initializing Browser Engine...", 
            "count": 0, 
            "color": "#3B82F6", 
            "runtime": 0
        }
        
    def append_log(self, message):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        GLOBAL_LOG_BUFFERS[self.op_id].append(f"{timestamp} » {message}")

    def execution_pipeline(self):
        self.append_log(f"Launching automated Playwright instance for query: '{self.query}'")
        METRICS_LEDGER[self.op_id].update({"status": "Spawning Headless Browser...", "color": "#F59E0B"})
        start_time = time.time()

        try:
            with sync_playwright() as p:
                # Launch Headless Chromium
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                page = context.new_page()

                # Navigate to Google Maps
                search_url = f"https://www.google.com/maps/search/{self.query.replace(' ', '+')}"
                self.append_log(f"Navigating to live stream map grid...")
                page.goto(search_url, timeout=60000)
                page.wait_for_timeout(4000)

                # Scroll down results pane to load items
                self.append_log("Parsing live DOM element nodes...")
                try:
                    scrollable_div = page.locator('div[role="feed"]')
                    for _ in range(3):
                        scrollable_div.evaluate("node => node.scrollBy(0, 1000)")
                        page.wait_for_timeout(1000)
                except Exception:
                    pass # Continue if scrolling selector varies

                # Target business cards
                cards = page.locator('a[href*="/maps/place/"]').all()
                self.append_log(f"Detected {len(cards)} matching target business nodes.")

                extracted_count = 0
                seen_names = set()

                for idx, card in enumerate(cards):
                    if not ACTIVE_OPERATIONS.get(self.op_id, False):
                        self.append_log("Process execution halted by user command.")
                        break

                    try:
                        # Extract basic text info from card
                        aria_label = card.get_attribute("aria-label")
                        if aria_label and aria_label not in seen_names:
                            name = aria_label
                            seen_names.add(name)

                            # Click card to load detail side panel
                            card.click(timeout=3000)
                            page.wait_for_timeout(2000)

                            # Extract Rating
                            rating = "N/A"
                            try:
                                rating_elem = page.locator('span[aria-hidden="true"]').first
                                if rating_elem.is_visible():
                                    val = rating_elem.inner_text().strip()
                                    if re.match(r'^\d\.\d$', val):
                                        rating = val
                            except Exception:
                                pass

                            # Extract Phone Number
                            phone = "Contact Not Listed"
                            try:
                                phone_elem = page.locator('button[data-tooltip*="phone"], button[aria-label*="Phone"]').first
                                if phone_elem.is_visible():
                                    phone_text = phone_elem.get_attribute("aria-label") or phone_elem.inner_text()
                                    phone = phone_text.replace("Phone: ", "").strip()
                            except Exception:
                                pass

                            # Extract Address
                            address = "Address Available on Map"
                            try:
                                addr_elem = page.locator('button[data-item-id="address"]').first
                                if addr_elem.is_visible():
                                    addr_text = addr_elem.get_attribute("aria-label") or addr_elem.inner_text()
                                    address = addr_text.replace("Address: ", "").strip()
                            except Exception:
                                pass

                            item = {
                                "Name": name,
                                "Phone": phone,
                                "Address": address,
                                "Rating": rating
                            }

                            SCRAPED_DATA_CACHE[self.op_id].append(item)
                            extracted_count += 1

                            elapsed = int(time.time() - start_time)
                            METRICS_LEDGER[self.op_id].update({
                                "status": f"Mining Business Target ({extracted_count})...",
                                "count": extracted_count,
                                "runtime": elapsed
                            })
                            self.append_log(f"Extracted Entity: {name} | Phone: {phone}")

                    except Exception as e:
                        continue

                browser.close()

                if ACTIVE_OPERATIONS.get(self.op_id, False):
                    if extracted_count == 0:
                        METRICS_LEDGER[self.op_id].update({"status": "No Nodes Extracted", "color": "#EF4444"})
                        self.append_log("No structural data cards were found for this query.")
                    else:
                        METRICS_LEDGER[self.op_id].update({"status": "Extraction Complete / Idle", "color": "#10B981"})
                        self.append_log("Live data scraping finished successfully.")

        except Exception as err:
            self.append_log(f"Scraper Runtime Fault: {str(err)}")
            METRICS_LEDGER[self.op_id].update({"status": "Execution Error", "color": "#EF4444"})

        ACTIVE_OPERATIONS[self.op_id] = False

@script39_bp.route('/')
def index():
    return render_template_string(HTML_WORKSPACE, company=COMPANY_BRAND)

@script39_bp.route('/api/start', methods=['POST'])
def api_start_scraper():
    try:
        payload = request.get_json() or {}
        query = payload.get('query', '').strip()
        if not query:
            return jsonify({"success": False, "error": "Query string value cannot be blank."}), 400
            
        operation_id = f"OP_{int(time.time() * 1000)}"
        ACTIVE_OPERATIONS[operation_id] = True
        
        worker = RealPlaywrightMapsScraper(operation_id, query)
        threading.Thread(target=worker.execution_pipeline, daemon=True).start()
        
        return jsonify({"success": True, "op_id": operation_id}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@script39_bp.route('/api/poll/<op_id>', methods=['GET'])
def api_poll_scraper(op_id):
    try:
        if op_id not in METRICS_LEDGER:
            return jsonify({"success": False, "error": "Target operation index log not registered."}), 404
            
        return jsonify({
            "success": True,
            "metrics": METRICS_LEDGER[op_id],
            "logs": GLOBAL_LOG_BUFFERS.get(op_id, []),
            "data": SCRAPED_DATA_CACHE.get(op_id, []),
            "is_running": ACTIVE_OPERATIONS.get(op_id, False)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@script39_bp.route('/api/stop/<op_id>', methods=['POST'])
def api_stop_scraper(op_id):
    try:
        if op_id in ACTIVE_OPERATIONS:
            ACTIVE_OPERATIONS[op_id] = False
            METRICS_LEDGER[op_id].update({"status": "Terminated Forcefully", "color": "#EF4444"})
            return jsonify({"success": True, "message": "Core link disconnected."}), 200
        return jsonify({"success": False, "error": "Invalid engine sequence identification ID."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

HTML_WORKSPACE = """
<!DOCTYPE html>
<html lang="en" id="themeRoot" class="theme-dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Live Data Intelligence Core</title>
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

    <header class="card-widget border-b px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4 sticky top-0 z-40 shadow-xl">
        <div class="flex items-center justify-between w-full sm:w-auto gap-4">
            <div class="flex items-center gap-3">
                <div class="p-2.5 bg-blue-600 rounded-xl text-white shadow-lg shadow-blue-600/30">
                    <i class="fa-solid fa-magnifying-glass-location text-xl"></i>
                </div>
                <div>
                    <h1 class="font-black text-base tracking-widest uppercase title-text">Orbitedgemedia</h1>
                    <span class="text-[9px] block text-blue-500 font-mono tracking-widest font-bold">REAL-TIME NO-API MAPS SCRAPER</span>
                </div>
            </div>
            <button onclick="toggleVisualThemeStyle()" class="sm:hidden p-2 rounded-lg border border-[var(--border-color)] bg-black/20 text-blue-500">
                <i class="fa-solid fa-circle-half-stroke"></i>
            </button>
        </div>
        
        <div class="flex items-center gap-4 w-full sm:w-auto justify-end">
            <button onclick="toggleVisualThemeStyle()" class="hidden sm:inline-block p-2.5 bg-black/20 border border-[var(--border-color)] rounded-xl text-blue-500 hover:bg-black/40 transition cursor-pointer">
                <i class="fa-solid fa-circle-half-stroke text-sm"></i>
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        
        <div class="card-widget p-6 rounded-2xl shadow-xl space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono"><i class="fa-solid fa-crosshairs text-blue-500 mr-1.5"></i> Target Search Query Configuration</h3>
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="targetQueryInput" placeholder="e.g., Hotels in Mumbai" value="Hotels in Mumbai" 
                       class="flex-1 px-4 py-3 text-xs font-mono rounded-xl input-widget focus:outline-none focus:border-blue-500">
                <button id="btnActionLaunch" onclick="toggleExtractionMatrix()" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs uppercase tracking-widest transition cursor-pointer shadow-lg shadow-blue-600/20">
                    LAUNCH EXTRACTION
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="card-widget p-5 rounded-2xl shadow-md flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider muted-text block mb-1">Engine Status</span>
                    <div class="flex items-center gap-2">
                        <span id="metricStatusText" class="text-sm font-bold title-text font-mono">Engine Standing By</span>
                    </div>
                </div>
                <i class="fa-solid fa-server opacity-10 text-3xl title-text"></i>
            </div>
            <div class="card-widget p-5 rounded-2xl shadow-md flex items-center justify-between">
                <div>
                    <span class="text-[10px] font-mono uppercase tracking-wider muted-text block mb-1">Live Records Scraping</span>
                    <span id="metricCounterText" class="text-2xl font-black font-mono text-emerald-500">000</span>
                </div>
                <i class="fa-solid fa-chart-bar opacity-10 text-3xl title-text"></i>
            </div>
        </div>

        <div class="card-widget p-5 rounded-2xl shadow-xl">
            <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono mb-3"><i class="fa-solid fa-bug-slash text-blue-500 mr-1.5"></i> Diagnostic Live Logs</h3>
            <div id="consoleLogsBox" class="w-full h-36 p-4 rounded-xl bg-black border border-[var(--border-color)] overflow-y-auto font-mono text-xs text-slate-400 space-y-1.5">
                [SYSTEM LOG]: Core engine ready. Launch extraction process.
            </div>
        </div>

        <div class="card-widget rounded-2xl overflow-hidden shadow-2xl">
            <div class="px-5 py-4 border-b border-[var(--border-color)]">
                <h3 class="text-xs font-bold uppercase tracking-wider muted-text font-mono"><i class="fa-solid fa-database text-blue-500 mr-1.5"></i> Real-Time Scraped Data</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full font-mono text-xs text-left">
                    <thead class="bg-black/40 text-[11px] muted-text border-b border-[var(--border-color)] uppercase">
                        <tr>
                            <th class="px-6 py-3.5 font-bold">Business Name</th>
                            <th class="px-6 py-3.5 font-bold">Contact Phone</th>
                            <th class="px-6 py-3.5 font-bold">Physical Address</th>
                            <th class="px-6 py-3.5 font-bold">Rating</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBodyRows" class="divide-y divide-[var(--border-color)] title-text">
                        <tr>
                            <td colspan="4" class="px-6 py-10 text-center font-mono muted-text">No active entries harvested yet.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card-widget p-4 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl">
            <div class="text-xs font-mono font-bold text-blue-500" id="metricTimerText">
                Operation Runtime: 00:00:00
            </div>
            <div class="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
                <select id="exportFormatDropdown" class="px-3 py-2 text-xs font-mono rounded-xl input-widget focus:outline-none bg-transparent">
                    <option value="CSV">CSV Format (.csv)</option>
                    <option value="JSON">JSON Matrix (.json)</option>
                </select>
                <button onclick="downloadMasterArchive()" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold font-mono rounded-xl text-xs uppercase tracking-wider transition cursor-pointer">
                    EXPORT DATA ARCHIVE
                </button>
            </div>
        </div>
    </main>

    <script>
        let globalOperationId = null;
        let internalPollingClock = null;
        let localMasterCacheData = [];
        let isOperationRunning = false;

        function toggleVisualThemeStyle() {
            const root = document.getElementById('themeRoot');
            root.classList.toggle('theme-light');
            root.classList.toggle('theme-dark');
        }

        async function toggleExtractionMatrix() {
            const launchBtn = document.getElementById('btnActionLaunch');
            
            if (isOperationRunning && globalOperationId) {
                clearInterval(internalPollingClock);
                await fetch(`/api/stop/${globalOperationId}`, { method: 'POST' });
                globalOperationId = null;
                isOperationRunning = false;
                resetButton();
                return;
            }

            const queryVal = document.getElementById('targetQueryInput').value.trim();
            if(!queryVal) return alert("Validation Error: Please configure a query target parameter first.");

            launchBtn.innerText = "HALT RUN ENGINE";
            launchBtn.classList.remove("bg-blue-600", "hover:bg-blue-500");
            launchBtn.classList.add("bg-rose-600", "hover:bg-rose-500");

            try {
                const req = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ query: queryVal })
                });
                const res = await req.json();
                
                if (res.success) {
                    globalOperationId = res.op_id;
                    isOperationRunning = true;
                    document.getElementById('consoleLogsBox').innerHTML = `<div class="text-blue-400">[SYSTEM INDEX]: Browser automation process initiated (ID: ${globalOperationId})</div>`;
                    internalPollingClock = setInterval(pollScraperBackendMetrics, 1000);
                } else {
                    alert('Error: ' + res.error);
                    resetButton();
                }
            } catch(error) {
                console.error('Error:', error);
                alert('Error: ' + error.message);
                resetButton();
            }
        }

        function resetButton() {
            const launchBtn = document.getElementById('btnActionLaunch');
            launchBtn.innerText = "LAUNCH EXTRACTION";
            launchBtn.classList.remove("bg-rose-600", "hover:bg-rose-500");
            launchBtn.classList.add("bg-blue-600", "hover:bg-blue-500");
            isOperationRunning = false;
        }

        async function pollScraperBackendMetrics() {
            if(!globalOperationId) return;

            try {
                const response = await fetch(`/api/poll/${globalOperationId}`);
                const res = await response.json();
                
                if(!res.success) return;

                const metrics = res.metrics;
                document.getElementById('metricStatusText').innerText = metrics.status;
                document.getElementById('metricCounterText').innerText = String(metrics.count).padStart(3, '0');
                
                let secs = metrics.runtime % 60;
                let mins = Math.floor(metrics.runtime / 60) % 60;
                let hrs = Math.floor(metrics.runtime / 3600);
                document.getElementById('metricTimerText').innerText = `Operation Runtime: ${String(hrs).padStart(2,'0')}:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;

                localMasterCacheData = res.data;
                const tableBody = document.getElementById('dataTableBodyRows');
                if (localMasterCacheData.length === 0) {
                    tableBody.innerHTML = `<tr><td colspan="4" class="px-6 py-10 text-center font-mono muted-text">Scraping elements from live Google Maps pane... Please wait.</td></tr>`;
                } else {
                    tableBody.innerHTML = localMasterCacheData.map(row => `
                        <tr class="hover:bg-black/20 transition">
                            <td class="px-6 py-3.5 font-bold">${row["Name"]}</td>
                            <td class="px-6 py-3.5 text-blue-400 font-bold">${row["Phone"]}</td>
                            <td class="px-6 py-3.5 opacity-80">${row["Address"]}</td>
                            <td class="px-6 py-3.5 text-emerald-400 font-black"><i class="fa-solid fa-star text-[10px] mr-1"></i>${row["Rating"]}</td>
                        </tr>
                    `).join('');
                }

                const logsContainer = document.getElementById('consoleLogsBox');
                logsContainer.innerHTML = (res.logs || []).map(log => `<div>${log}</div>`).join('');
                logsContainer.scrollTop = logsContainer.scrollHeight;

                if (!res.is_running) {
                    clearInterval(internalPollingClock);
                    globalOperationId = null;
                    resetButton();
                }
            } catch(error) {
                console.error('Poll error:', error);
            }
        }

        function downloadMasterArchive() {
            if (localMasterCacheData.length === 0) {
                return alert("Export Exception: Local dataset allocation block is currently empty.");
            }

            const format = document.getElementById('exportFormatDropdown').value;
            let dataStr = "";
            let fileExtension = "";

            if (format === "JSON") {
                dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(localMasterCacheData, null, 4));
                fileExtension = "json";
            } else {
                const headers = Object.keys(localMasterCacheData[0]).join(",");
                const rows = localMasterCacheData.map(row => Object.values(row).map(v => `"${v}"`).join(",")).join("\n");
                dataStr = "data:text/csv;charset=utf-8," + encodeURIComponent(headers + "\n" + rows);
                fileExtension = "csv";
            }

            const elementLink = document.createElement('a');
            elementLink.setAttribute("href", dataStr);
            elementLink.setAttribute("download", `ScrapedData_Archive_${Math.floor(Date.now()/1000)}.${fileExtension}`);
            document.body.appendChild(elementLink);
            elementLink.click();
            document.body.removeChild(elementLink);
        }
    </script>
</body>
</html>
"""

# Register Blueprint & Launch App
app.register_blueprint(script39_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
