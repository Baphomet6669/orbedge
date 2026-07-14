import os
import json
import time
import random
import csv
import requests
import base64
from io import StringIO
from threading import Lock
from flask import Flask, Blueprint, render_template_string, request, jsonify, session, redirect, url_for

# =========================================================================
# INITIALIZE FLASK CORE & BLUEPRINT
# =========================================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

script34_bp = Blueprint('script34', __name__)

# GitHub Integration Configs (Render Env Variables से उठाएगा)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')  # Format: "username/repo"
GITHUB_BRANCH = os.environ.get('GITHUB_BRANCH', 'main')
DATA_FILE = 'crm_data.json'

AUTH_USER = 'admin'
AUTH_PASS = '5hsuusu78@#/@&hsb' 

db_lock = Lock()

# =========================================================================
# GITHUB STORAGE ENGINE (NO-MORE LOSS OF DATA ON SERVER RESTART)
# =========================================================================
def get_default_structure():
    return {
        'leads': [
            {"id": 1, "name": "Rahul Sharma", "email": "rahul@example.com", "phone": "+919876543210", "company": "Sharma Tech", "status": "New", "value": 45000, "date": "2026-07-10"},
            {"id": 2, "name": "Amit Verma", "email": "amit@example.com", "phone": "+918765432109", "company": "Verma Digital", "status": "Contacted", "value": 120000, "date": "2026-07-11"}
        ],
        'customers': [
            {"id": 3, "name": "Priya Singh", "email": "priya@example.com", "phone": "+917654321098", "company": "Singh Org", "revenue": 150000, "joined_date": "2026-07-11"}
        ],
        'tasks': [
            {"id": 1, "title": "Setup Marketing Automation Gateway", "due_date": "2026-07-15", "priority": "High", "status": "Pending"}
        ],
        'automation_queue': []
    }

def db_read():
    """GitHub API से फाइल का डेटा फेच करता है"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        # अगर टोकन सेट नहीं है, तो सेफ्टी के लिए लोकल फाइल पर फॉलबैक करेगा
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                try: return json.load(f)
                except: return get_default_structure()
        return get_default_structure()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}?ref={GITHUB_BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    with db_lock:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                content_b64 = res.json()['content']
                content_str = base64.b64decode(content_b64).decode('utf-8')
                return json.loads(content_str)
            elif res.status_code == 404:
                # अगर GitHub पर फाइल नहीं है, तो डिफॉल्ट स्ट्रक्चर अपलोड कर देगा
                default_data = get_default_structure()
                db_write_raw(default_data, None)
                return default_data
        except Exception as e:
            print(f"GitHub Read Error: {e}")
            
    return get_default_structure()

def db_write(data):
    """GitHub API पर डेटा पुश (Commit) करता है"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    with db_lock:
        try:
            # फाइल का 'sha' टोकन लेने के लिए पहले GET रिक्वेस्ट मारनी पड़ती है
            sha = None
            res_get = requests.get(f"{url}?ref={GITHUB_BRANCH}", headers=headers, timeout=10)
            if res_get.status_code == 200:
                sha = res_get.json()['sha']
            
            db_write_raw(data, sha)
        except Exception as e:
            print(f"GitHub Write Setup Error: {e}")

def db_write_raw(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    content_str = json.dumps(data, indent=4)
    content_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "CRM Database Auto-Sync Update",
        "content": content_b64,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload, timeout=10)

# =========================================================================
# MIDDLEWARE ENGINE
# =========================================================================
def is_authenticated():
    return session.get('crm_logged_in') is True

# =========================================================================
# FLASK ROUTING GATEWAYS
# =========================================================================
@script34_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == AUTH_USER and password == AUTH_PASS:
            session['crm_logged_in'] = True
            return render_template_string(HTML_LAYOUT, is_authenticated=True, login_error=None)
        else:
            return render_template_string(HTML_LAYOUT, is_authenticated=False, login_error="Invalid credentials! Please try again.")

    if not is_authenticated():
        return render_template_string(HTML_LAYOUT, is_authenticated=False, login_error=None)
    return render_template_string(HTML_LAYOUT, is_authenticated=True, login_error=None)

@script34_bp.route('/action/logout', methods=['GET'])
def action_logout():
    session.pop('crm_logged_in', None)
    return redirect(url_for('script34.index'))

# =========================================================================
# FLASK RESTFUL ASYNC API HOOKS
# =========================================================================
@script34_bp.route('/api/get_dashboard_stats', methods=['GET'])
def get_dashboard_stats():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    
    leads = db.get('leads', [])
    customers = db.get('customers', [])
    tasks = db.get('tasks', [])
    
    total_value = sum(float(l.get('value', 0) or 0) for l in leads)
    leads_count = len(leads)
    avg_value = total_value / leads_count if leads_count > 0 else 0
    total_revenue = sum(float(c.get('revenue', 0) or 0) for c in customers)
    high_value_leads_count = len([l for l in leads if float(l.get('value', 0) or 0) >= 100000])
    
    total_pipeline_entities = leads_count + len(customers)
    win_rate = (len(customers) / total_pipeline_entities * 100) if total_pipeline_entities > 0 else 0

    stats = {
        'total_leads': leads_count,
        'total_customers': len(customers),
        'pending_tasks': len([t for t in tasks if t.get('status') != 'Completed']),
        'total_pipeline_value': total_value,
        'average_deal_size': avg_value,
        'total_queued_messages': len(db.get('automation_queue', [])),
        'total_revenue_pool': total_revenue,
        'high_value_leads': high_value_leads_count,
        'win_rate': round(win_rate, 1),
        'lead_status_counts': {'New': 0, 'Contacted': 0, 'Proposal': 0, 'Lost': 0},
        'recent_activity': list(reversed(leads))[:6]
    }
    
    for l in leads:
        status = l.get('status', 'New')
        if status in stats['lead_status_counts']:
            stats['lead_status_counts'][status] += 1
            
    return jsonify(stats)

@script34_bp.route('/api/save_lead', methods=['POST'])
def save_lead():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    lead_id = request.form.get('id', '')
    
    lead_data = {
        'id': int(lead_id) if lead_id else int(time.time() + random.randint(1000, 9999)),
        'name': request.form.get('name', ''),
        'email': request.form.get('email', ''),
        'phone': request.form.get('phone', ''),
        'company': request.form.get('company', ''),
        'status': request.form.get('status', 'New'),
        'value': float(request.form.get('value', 0) or 0),
        'date': request.form.get('date') if (lead_id and request.form.get('date')) else time.strftime('%Y-%m-%d')
    }

    if lead_id:
        for idx, l in enumerate(db['leads']):
            if l['id'] == int(lead_id):
                db['leads'][idx] = lead_data
                break
    else:
        db['leads'].append(lead_data)
        
    db_write(db)
    return jsonify({'success': True, 'message': 'Lead saved successfully!'})

@script34_bp.route('/api/delete_lead', methods=['POST'])
def delete_lead():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    target_id = int(request.form.get('id', 0))
    db['leads'] = [l for l in db['leads'] if l['id'] != target_id]
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/convert_to_customer', methods=['POST'])
def convert_to_customer():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    target_id = int(request.form.get('id', 0))
    
    target_lead = None
    for l in db['leads']:
        if l['id'] == target_id:
            target_lead = l
            break
            
    if target_lead:
        db['leads'] = [l for l in db['leads'] if l['id'] != target_id]
        db['customers'].append({
            'id': int(time.time() + random.randint(1000, 9999)),
            'name': target_lead['name'],
            'email': target_lead['email'],
            'phone': target_lead['phone'],
            'company': target_lead['company'],
            'revenue': float(target_lead.get('value', 0) or 0),
            'joined_date': time.strftime('%Y-%m-%d')
        })
        db_write(db)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Lead not found'})

@script34_bp.route('/api/get_leads', methods=['GET'])
def get_leads():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(db_read().get('leads', []))

@script34_bp.route('/api/get_customers', methods=['GET'])
def get_customers():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(db_read().get('customers', []))

@script34_bp.route('/api/save_task', methods=['POST'])
def save_task():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    db['tasks'].append({
        'id': int(time.time() + random.randint(1000, 9999)),
        'title': request.form.get('title', ''),
        'due_date': request.form.get('due_date', ''),
        'priority': request.form.get('priority', 'Medium'),
        'status': 'Pending'
    })
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/get_tasks', methods=['GET'])
def get_tasks():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(db_read().get('tasks', []))

@script34_bp.route('/api/toggle_task', methods=['POST'])
def toggle_task():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    target_id = int(request.form.get('id', 0))
    for t in db['tasks']:
        if t['id'] == target_id:
            t['status'] = 'Pending' if t['status'] == 'Completed' else 'Completed'
            break
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/delete_task', methods=['POST'])
def delete_task():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    target_id = int(request.form.get('id', 0))
    db['tasks'] = [t for t in db['tasks'] if t['id'] != target_id]
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/get_automation_queue', methods=['GET'])
def get_automation_queue():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(db_read().get('automation_queue', []))

@script34_bp.route('/api/clear_automation_queue', methods=['GET', 'POST'])
def clear_automation_queue():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    db['automation_queue'] = []
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/process_lead_automation', methods=['POST'])
def process_lead_automation():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    selected_ids = request.form.getlist('lead_ids[]')
    message_template = request.form.get('message', '')
    
    if not selected_ids:
        return jsonify({'success': False, 'message': 'Koi leads select nahi kiye gaye.'})
        
    imported_count = 0
    for lead in db.get('leads', []):
        if str(lead['id']) in selected_ids:
            custom_message = message_template.replace('[Name]', lead['name'])
            
            db['automation_queue'].append({
                'id': f"{int(time.time())}_{random.randint(1000, 9999)}",
                'phone': lead['phone'],
                'name': lead['name'],
                'email': lead['email'],
                'message': custom_message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M')
            })
            imported_count += 1
            
    db_write(db)
    return jsonify({'success': True, 'message': f'Successfully deployed {imported_count} leads to broadcast engine.'})

# =========================================================================
# INTERLINKED CSV WORKFLOW UPLOADER (DIRECT GITHUB INGESTION)
# =========================================================================
@script34_bp.route('/api/upload_automation_sheet', methods=['POST'])
def upload_automation_sheet():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    if 'automation_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file detected.'})
        
    file = request.files['automation_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Empty spreadsheet selected.'})
        
    if file and file.filename.endswith('.csv'):
        stream = StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_input = csv.reader(stream)
        
        db = db_read()
        imported_count = 0
        
        try:
            first_row = next(csv_input)
            if first_row and ('phone' in first_row[0].lower() or 'name' in first_row[1].lower()):
                pass
            else:
                csv_rows = [first_row] + list(csv_input)
                csv_input = csv_rows
        except StopIteration:
            return jsonify({'success': False, 'message': 'Empty CSV layout structure.'})

        current_timestamp = int(time.time())

        if 'automation_queue' not in db: db['automation_queue'] = []
        if 'leads' not in db: db['leads'] = []

        for idx, row in enumerate(csv_input):
            if not row or len(row) < 2: continue
            
            phone = ''.join(c for c in row[0] if c.isdigit() or c == '+')
            name = row[1] if len(row) > 1 and row[1] else 'Valued Client'
            email = row[2] if len(row) > 2 else ''
            message = row[3] if len(row) > 3 else 'Hello, this is an automated broadcast alert.'
            
            company = row[4] if len(row) > 4 and row[4] else 'Bulk Ingested Corp'
            status = row[5] if len(row) > 5 and row[5] else 'New'
            try:
                value = float(row[6]) if len(row) > 6 else 65000.0
            except:
                value = 65000.0

            safe_js_id = int(current_timestamp + idx + random.randint(100, 999))

            db['automation_queue'].append({
                'id': f"{safe_js_id}_{random.randint(10, 99)}",
                'phone': phone,
                'name': name,
                'email': email,
                'message': message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M')
            })

            db['leads'].append({
                'id': safe_js_id,
                'name': name,
                'email': email,
                'phone': phone,
                'company': company,
                'status': status,
                'value': value,
                'date': time.strftime('%Y-%m-%d')
            })
            imported_count += 1
            
        db_write(db)
        return jsonify({'success': True, 'message': f'Successfully parsed {imported_count} contacts & perfectly linked into Pipeline system!'})
        
    return jsonify({'success': False, 'message': 'Invalid file layout format.'})

app.register_blueprint(script34_bp, url_for_security='/')

# HTML UI Layout Script (Excel, PDF Export & Tracking Markers Added Seamlessly)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdge Media | Enterprise CRM</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Heavy-Duty Client-Side Export Dependencies (Bypasses Server Load) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; transition: background-color 0.3s, color 0.3s; }
        .sidebar-link.active { background-color: #4f46e5; color: white; font-weight: 600; }
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
<body class="light-mode transition-all duration-300 antialiased selection:bg-indigo-500 selection:text-white">

{% if not is_authenticated %}
    <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
        <div class="w-full max-w-md bg-gray-900 border border-gray-800 p-8 rounded-2xl shadow-2xl relative overflow-hidden">
            <div class="absolute -top-10 -right-10 w-32 h-32 bg-indigo-600/10 rounded-full blur-2xl pointer-events-none"></div>
            
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-xl shadow-indigo-500/30 mb-4">
                    <i class="fa-solid fa-chart-line text-2xl text-white"></i>
                </div>
                <h1 class="text-2xl font-extrabold text-white tracking-tight">OrbitEdge Media</h1>
                <p class="text-gray-400 text-sm mt-1">Management Portal Enterprise v4.0</p>
            </div>

            {% if login_error %}
                <div class="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm p-3 rounded-xl mb-5">
                    <i class="fa-solid fa-circle-exclamation text-rose-500"></i> {{ login_error }}
                </div>
            {% endif %}

            <form action="" method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">Username</label>
                    <input type="text" name="username" required placeholder="admin" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">Password</label>
                    <input type="password" name="password" required placeholder="••••••••" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3.5 rounded-xl transition duration-200 cursor-pointer mt-2">Login Engine</button>
            </form>
        </div>
    </div>
{% else %}
    <!-- MOBILE TOP HEADER (BAR) -->
    <div class="md:hidden bg-gray-950 text-white flex items-center justify-between p-4 border-b border-gray-900 sticky top-0 z-50">
        <div class="flex items-center gap-2">
            <div class="p-2 bg-indigo-600 rounded-lg"><i class="fa-solid fa-bolt text-sm text-white"></i></div>
            <span class="font-bold text-sm tracking-wide">OrbitEdge</span>
        </div>
        <button onclick="toggleMobileSidebar()" class="text-white text-xl focus:outline-none p-1">
            <i id="mobile-menu-icon" class="fa-solid fa-bars"></i>
        </button>
    </div>

    <div class="min-h-screen flex flex-col md:flex-row relative">
        <!-- SIDEBAR -->
        <aside id="sidebar-container" class="hidden md:flex fixed md:sticky top-[53px] md:top-0 left-0 bottom-0 w-full md:w-64 bg-gray-950 text-white flex-col border-r border-gray-900 z-40 transition-all duration-300 overflow-y-auto">
            <div class="p-6 border-b border-gray-900 hidden md:flex items-center gap-3">
                <div class="p-2.5 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl"><i class="fa-solid fa-bolt text-lg text-white"></i></div>
                <div>
                    <h2 class="font-bold text-base tracking-wide leading-none text-white">OrbitEdge</h2>
                    <span class="text-[10px] text-gray-400 uppercase tracking-widest mt-1 block">Media CRM</span>
                </div>
            </div>
            <nav class="flex-1 p-4 space-y-1.5">
                <button onclick="switchTab('dashboard')" id="btn-dashboard" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-gauge w-5 text-center"></i> Dashboard</button>
                <button onclick="switchTab('leads')" id="btn-leads" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-bullseye w-5 text-center"></i> Pipeline & Leads</button>
                <button onclick="switchTab('customers')" id="btn-customers" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-users w-5 text-center"></i> Active Customers</button>
                <button onclick="switchTab('automation')" id="btn-automation" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-paper-plane w-5 text-center"></i> Bulk Automation</button>
                <button onclick="switchTab('tasks')" id="btn-tasks" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-list-check w-5 text-center"></i> Tasks Matrix</button>
                <button onclick="switchTab('reports')" id="btn-reports" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-chart-pie w-5 text-center"></i> Advanced Reports</button>
            </nav>
            <div class="p-4 border-t border-gray-900 space-y-2">
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-gray-900 text-xs font-semibold cursor-pointer text-gray-300">
                    <span>Appearance</span><i id="theme-icon" class="fa-solid fa-moon"></i>
                </button>
                <a href="action/logout" class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-500/10"><i class="fa-solid fa-right-from-bracket"></i> Clear Session</a>
            </div>
        </aside>

        <!-- MAIN CONTAINER -->
        <main class="flex-1 p-4 md:p-8 overflow-y-auto max-h-screen w-full" id="exportable-main-area">
            <div id="toast" class="fixed bottom-5 right-5 z-50 transform translate-y-20 opacity-0 bg-gray-900 border border-emerald-500/30 text-white px-5 py-3.5 rounded-xl shadow-2xl flex items-center gap-3 transition-all duration-300">
                <i class="fa-solid fa-circle-check text-emerald-400 text-lg"></i> <span id="toast-text" class="text-sm font-semibold"></span>
            </div>

            <!-- DASHBOARD TAB -->
            <div id="tab-dashboard" class="tab-content hidden space-y-8">
                <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                    <div>
                        <h1 class="text-2xl font-bold text-custom-main">Main Command Dashboard</h1>
                        <p class="text-sm text-custom-muted">Live operational analytical monitoring ecosystem.</p>
                    </div>
                    
                    <!-- Advanced Document Exports -->
                    <div class="flex flex-wrap items-center gap-3">
                        <button onclick="exportFullCRMDataToExcel()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 cursor-pointer transition shadow-md">
                            <i class="fa-solid fa-file-excel"></i> Export XLSX Reports
                        </button>
                        <button onclick="exportFullCRMToPDF()" class="bg-rose-600 hover:bg-rose-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 cursor-pointer transition shadow-md">
                            <i class="fa-solid fa-file-pdf"></i> Export PDF Dashboard
                        </button>
                        <div class="bg-indigo-500/10 text-indigo-500 px-4 py-2 rounded-xl text-xs font-bold border border-indigo-500/20 flex items-center gap-2">
                            <span class="flex h-2 w-2 relative">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            GitHub Sync Server Active <span id="conversion-win-rate" class="ml-2 bg-indigo-600 text-white px-1.5 py-0.5 rounded text-[10px]">Win Rate: 0%</span>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-indigo-500/10 text-indigo-600 rounded-xl"><i class="fa-solid fa-bolt text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Leads</p><h3 id="stat-leads" class="text-xl font-extrabold text-custom-main">0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-emerald-500/10 text-emerald-600 rounded-xl"><i class="fa-solid fa-wallet text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Clients</p><h3 id="stat-customers" class="text-xl font-extrabold text-custom-main">0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-amber-500/10 text-amber-600 rounded-xl"><i class="fa-solid fa-list-check text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Tasks</p><h3 id="stat-tasks" class="text-xl font-extrabold text-custom-main">0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-blue-500/10 text-blue-600 rounded-xl"><i class="fa-solid fa-chart-line text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Pipeline</p><h3 id="stat-pipeline-value" class="text-xl font-extrabold text-custom-main">₹0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-purple-500/10 text-purple-600 rounded-xl"><i class="fa-solid fa-calculator text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Avg Deal</p><h3 id="stat-avg-deal" class="text-xl font-extrabold text-custom-main">₹0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-rose-500/10 text-rose-500 rounded-xl"><i class="fa-solid fa-paper-plane text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Queued</p><h3 id="stat-queued-messages" class="text-xl font-extrabold text-custom-main">0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-emerald-500/20 text-emerald-600 rounded-xl"><i class="fa-solid fa-gavel text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Revenue</p><h3 id="stat-revenue-pool" class="text-xl font-extrabold text-emerald-500">₹0</h3></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2 panel-card p-6 rounded-2xl border flex flex-col justify-between">
                        <h3 class="font-bold text-base mb-4 text-custom-main"><i class="fa-solid fa-chart-simple text-indigo-600"></i> Pipeline Status Analysis</h3>
                        <div class="w-full h-72 relative"><canvas id="dashboardPipelineChart"></canvas></div>
                    </div>
                    <div class="panel-card p-6 rounded-2xl border flex flex-col">
                        <h3 class="font-bold text-base mb-4 text-custom-main"><i class="fa-solid fa-clock-rotate-left text-indigo-600"></i> Recent Activities</h3>
                        <div id="recent-activity-list" class="space-y-3 overflow-y-auto max-h-[288px] flex-1"></div>
                    </div>
                </div>
            </div>

            <!-- LEADS TAB -->
            <div id="tab-leads" class="tab-content hidden space-y-6">
                <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                    <div><h1 class="text-2xl font-bold text-custom-main">Sales Funnel Pipeline</h1><p class="text-sm text-custom-muted">Track and optimize incoming inquiries.</p></div>
                    <div class="flex flex-wrap gap-2.5">
                        <button onclick="exportLeadsToCSV()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 cursor-pointer transition shadow-md"><i class="fa-solid fa-file-csv"></i> Export CSV</button>
                        <button onclick="openLeadModal()" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 cursor-pointer transition shadow-md"><i class="fa-solid fa-plus"></i> New Lead</button>
                    </div>
                </div>
                
                <div class="panel-card p-4 rounded-xl border grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
                    <div class="relative w-full">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400"><i class="fa-solid fa-magnifying-glass text-xs"></i></span>
                        <input type="text" id="leadSearch" onkeyup="renderLeadsTable()" placeholder="Search client name..." class="w-full input-custom border rounded-xl pl-9 pr-4 py-2 text-xs focus:outline-none">
                    </div>
                    <div>
                        <select id="leadFilterStatus" onchange="renderLeadsTable()" class="w-full input-custom border rounded-xl px-3 py-2 text-xs focus:outline-none">
                            <option value="All">All Statuses</option><option value="New">New</option><option value="Contacted">Contacted</option><option value="Proposal">Proposal</option><option value="Lost">Lost</option>
                        </select>
                    </div>
                    <div>
                        <select id="leadFilterValueTier" onchange="renderLeadsTable()" class="w-full input-custom border rounded-xl px-3 py-2 text-xs focus:outline-none">
                            <option value="All">All Deal Sizes</option><option value="High">VIP Deals (≥ ₹1,00,000)</option><option value="Mid">Standard Deals (< ₹1,00,000)</option>
                        </select>
                    </div>
                </div>
                <div class="panel-card rounded-xl border overflow-x-auto shadow-sm">
                    <table class="w-full text-left border-collapse min-w-[600px]">
                        <thead>
                            <tr class="border-b border-custom text-custom-muted text-[11px] font-bold uppercase bg-gray-500/5">
                                <th class="p-4">Client / Company</th><th class="p-4">Est Value</th><th class="p-4">Dynamic Tier</th><th class="p-4">Funnel Position</th><th class="p-4">Date Added</th><th class="p-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="leads-table-body" class="divide-y divide-custom text-xs text-custom-main"></tbody>
                    </table>
                </div>
            </div>

            <!-- CUSTOMERS TAB -->
            <div id="tab-customers" class="tab-content hidden space-y-6">
                <div><h1 class="text-2xl font-bold text-custom-main">Active Accounts Database</h1><p class="text-sm text-custom-muted">Converted official revenue generators.</p></div>
                <div class="panel-card rounded-xl border overflow-x-auto shadow-sm">
                    <table class="w-full text-left border-collapse min-w-[600px]">
                        <thead>
                            <tr class="border-b border-custom text-custom-muted text-[11px] font-bold uppercase bg-gray-500/5">
                                <th class="p-4">Customer Entity</th><th class="p-4">Corporate Brand</th><th class="p-4">Contact Logic</th><th class="p-4">Revenue Generated</th><th class="p-4">Acquisition Date</th>
                            </tr>
                        </thead>
                        <tbody id="customers-table-body" class="divide-y divide-custom text-xs text-custom-main"></tbody>
                    </table>
                </div>
            </div>

            <!-- AUTOMATION TAB -->
            <div id="tab-automation" class="tab-content hidden space-y-6">
                <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                    <div>
                        <h1 class="text-2xl font-bold text-custom-main">Bulk Marketing & Message Automation</h1>
                        <p class="text-sm text-custom-muted">Select live CRM leads or ingest spreadsheets to dispatch workflows.</p>
                    </div>
                    <button onclick="clearAutomationLogs()" class="bg-rose-600/10 text-rose-500 border border-rose-500/20 hover:bg-rose-500/20 px-3 py-2 rounded-xl text-xs font-bold cursor-pointer transition flex items-center gap-2 self-start sm:self-center">
                        <i class="fa-solid fa-trash-can"></i> Clear Broadcast Records
                    </button>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="panel-card p-6 rounded-2xl border h-fit space-y-5 shadow-sm">
                        <div>
                            <h3 class="font-bold text-base text-indigo-500 mb-2"><i class="fa-solid fa-gears"></i> Engine Composer</h3>
                            <p class="text-xs text-custom-muted">Compose your text template below. Use token <span class="font-mono text-indigo-500 font-bold">[Name]</span> for dynamic lead customization.</p>
                        </div>
                        
                        <div>
                            <label class="block text-xs font-bold text-custom-muted mb-1.5">Message Template</label>
                            <textarea id="auto_msg_template" rows="4" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none focus:border-indigo-500 resize-none" placeholder="Namaste [Name], check out our new automation update!"></textarea>
                        </div>

                        <div class="border-t border-custom pt-4">
                            <h4 class="text-xs font-bold text-custom-main mb-3 flex items-center gap-1.5"><i class="fa-solid fa-users text-indigo-500"></i> Option A: Inject Live Funnel Leads</h4>
                            <div id="automation-leads-injector-list" class="space-y-2 max-h-40 overflow-y-auto border border-custom p-2.5 rounded-xl bg-gray-500/5"></div>
                            <button onclick="deployLiveLeadsToAutomation()" class="w-full mt-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 rounded-xl text-xs cursor-pointer transition shadow-sm">
                                🚀 Process Selected Leads
                            </button>
                        </div>

                        <div class="border-t border-custom pt-4">
                            <h4 class="text-xs font-bold text-custom-main mb-2"><i class="fa-solid fa-file-excel text-emerald-500"></i> Option B: External CSV Ingest (Interlinked)</h4>
                            <form id="automation-upload-form" onsubmit="handleSheetUpload(event)" class="space-y-3">
                                <div class="border border-dashed border-custom rounded-xl p-4 text-center relative bg-gray-500/5 cursor-pointer">
                                    <input type="file" id="automation_file" name="automation_file" accept=".csv" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
                                    <p class="text-[11px] text-custom-muted">Click to browse sheet document (.csv)</p>
                                </div>
                                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 rounded-xl text-xs cursor-pointer transition shadow-sm">
                                    <i class="fa-solid fa-cloud-arrow-up"></i> Upload & Sync to Pipeline
                                </button>
                            </form>
                        </div>
                    </div>

                    <div class="lg:col-span-2 panel-card p-6 rounded-2xl border flex flex-col shadow-sm">
                        <h3 class="font-bold text-base mb-4 text-custom-main"><i class="fa-solid fa-satellite-dish text-indigo-600"></i> Dispatched Broadcast Operational Grid</h3>
                        <div class="overflow-x-auto flex-1 max-h-[520px]">
                            <table class="w-full text-left border-collapse text-xs min-w-[500px]">
                                <thead>
                                    <tr class="border-b border-custom text-custom-muted font-bold uppercase bg-gray-500/5">
                                        <th class="p-3">Client Target</th><th class="p-3">Automated Message Body</th><th class="p-3 text-right">Dispatch Channels</th>
                                    </tr>
                                </thead>
                                <tbody id="automation-queue-body" class="divide-y divide-custom text-custom-main"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TASKS TAB -->
            <div id="tab-tasks" class="tab-content hidden space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="panel-card p-6 rounded-2xl border h-fit shadow-sm">
                        <h3 class="font-bold text-base mb-4 text-indigo-500">Register New Objective</h3>
                        <form id="task-form" onsubmit="handleTaskSubmit(event)" class="space-y-4">
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Objective Title</label>
                                <input type="text" id="task_title" required placeholder="E.g., Review Dashboard System" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-bold text-custom-muted mb-1.5">Due Deadline</label>
                                    <input type="date" id="task_due" required class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-custom-muted mb-1.5">Priority Weight</label>
                                    <select id="task_priority" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                                        <option value="High">High</option><option value="Medium" selected>Medium</option><option value="Low">Low</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl text-xs cursor-pointer transition">Inject Task Engine</button>
                        </form>
                    </div>
                    <div class="lg:col-span-2 panel-card p-6 rounded-2xl border flex flex-col shadow-sm">
                        <h3 class="font-bold text-base mb-4 text-custom-main">Active Strategic Roadmap</h3>
                        <div id="tasks-list" class="space-y-3 flex-1 overflow-y-auto max-h-[450px]"></div>
                    </div>
                </div>
            </div>

            <!-- REPORTS TAB -->
            <div id="tab-reports" class="tab-content hidden space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main">Funnels Pipeline Breakdown</h3>
                        <div class="w-full max-w-[260px] mx-auto relative"><canvas id="reportPieChart"></canvas></div>
                    </div>
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main">Gross Conversion Velocity</h3>
                        <div class="w-full max-w-[260px] mx-auto relative"><canvas id="reportDoughnutChart"></canvas></div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- MODAL SPECIFICATIONS -->
    <div id="leadModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-all duration-300 px-4">
        <div class="w-full max-w-lg bg-[var(--bg-panel)] border border-[var(--border-color)] rounded-2xl shadow-2xl overflow-hidden transform scale-95 transition-all duration-300">
            <div class="bg-indigo-600 px-6 py-4 text-white flex justify-between items-center">
                <h3 id="modalTitle" class="font-bold text-sm tracking-wide">Initialize Core Funnel Record</h3>
                <button onclick="closeLeadModal()" class="text-white/70 hover:text-white text-lg cursor-pointer"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <form id="lead-form" onsubmit="handleLeadSubmit(event)" class="p-6 space-y-4">
                <input type="hidden" id="lead_id">
                <input type="hidden" id="lead_date">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Lead Name</label>
                        <input type="text" id="lead_name" required class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Corporate Brand</label>
                        <input type="text" id="lead_company" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Email ID</label>
                        <input type="email" id="lead_email" required class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Phone Number</label>
                        <input type="text" id="lead_phone" required class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Funnel Status</label>
                        <select id="lead_status" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            <option value="New">New</option><option value="Contacted">Contacted</option><option value="Proposal">Proposal</option><option value="Lost">Lost</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-custom-muted mb-1.5">Estimated Capital</label>
                        <input type="number" step="0.01" min="0" id="lead_value" required class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                    </div>
                </div>
                <div class="flex justify-end gap-2.5 pt-3 border-t border-custom mt-5">
                    <button type="button" onclick="closeLeadModal()" class="px-4 py-2 border border-custom text-xs font-bold rounded-xl cursor-pointer text-custom-main transition">Terminate</button>
                    <button type="submit" class="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-xl cursor-pointer transition">Commit Database Entry</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let activeTab = 'dashboard';
        let rawLeads = [];
        let rawCustomers = [];
        let rawTasks = [];
        let rawAutomation = [];
        let pipelineChartInstance = null;
        let reportPieChartInstance = null;
        let reportDoughnutChartInstance = null;

        function getBlueprintPrefix() {
            let path = window.location.pathname;
            if(path.endsWith('/')) return path;
            return path + '/';
        }

        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar-container');
            const icon = document.getElementById('mobile-menu-icon');
            if(sidebar.classList.contains('hidden')) {
                sidebar.classList.remove('hidden');
                sidebar.classList.add('flex');
                icon.className = "fa-solid fa-xmark";
            } else {
                sidebar.classList.remove('flex');
                sidebar.classList.add('hidden');
                icon.className = "fa-solid fa-bars";
            }
        }

        async function fetchAPI(endpoint, postData = null) {
            try {
                let options = postData ? { method: 'POST', body: postData } : { method: 'GET' };
                let response = await fetch(`${getBlueprintPrefix()}api/${endpoint}`, options);
                return await response.json();
            } catch (err) {
                console.error("AJAX Telemetry system broken down:", err);
            }
        }

        function popToast(msg) {
            const el = document.getElementById('toast');
            document.getElementById('toast-text').innerText = msg;
            el.classList.remove('translate-y-20', 'opacity-0');
            setTimeout(() => el.classList.add('translate-y-20', 'opacity-0'), 3000);
        }

        window.addEventListener('DOMContentLoaded', () => {
            if (localStorage.getItem('theme') === 'dark') toggleDarkMode(true);
            switchTab('dashboard');
            
            setInterval(() => {
                if (activeTab === 'dashboard') loadDashboardEngine(true);
            }, 5000);
        });

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
            if (activeTab === 'dashboard') loadDashboardEngine(); 
            if (activeTab === 'reports') loadReportsEngine();
        }

        function switchTab(target) {
            activeTab = target;
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
            
            document.getElementById(`tab-${target}`).classList.remove('hidden');
            document.getElementById(`btn-${target}`).classList.add('active');

            if(window.innerWidth < 768) {
                const sidebar = document.getElementById('sidebar-container');
                sidebar.classList.remove('flex');
                sidebar.classList.add('hidden');
                document.getElementById('mobile-menu-icon').className = "fa-solid fa-bars";
            }

            if (target === 'dashboard') loadDashboardEngine();
            if (target === 'leads') loadLeadsEngine();
            if (target === 'customers') loadCustomersEngine();
            if (target === 'automation') loadAutomationEngine();
            if (target === 'tasks') loadTasksEngine();
            if (target === 'reports') loadReportsEngine();
        }

        async function loadDashboardEngine(isSilent = false) {
            let stats = await fetchAPI('get_dashboard_stats');
            if(!stats) return;

            document.getElementById('stat-leads').innerText = stats.total_leads || 0;
            document.getElementById('stat-customers').innerText = stats.total_customers || 0;
            document.getElementById('stat-tasks').innerText = stats.pending_tasks || 0;
            document.getElementById('stat-queued-messages').innerText = stats.total_queued_messages || 0;
            document.getElementById('stat-pipeline-value').innerText = '₹' + parseFloat(stats.total_pipeline_value || 0).toLocaleString('en-IN');
            document.getElementById('stat-avg-deal').innerText = '₹' + parseFloat(stats.average_deal_size || 0).toLocaleString('en-IN', {maximumFractionDigits: 0});
            document.getElementById('stat-revenue-pool').innerText = '₹' + parseFloat(stats.total_revenue_pool || 0).toLocaleString('en-IN', {maximumFractionDigits: 0});
            
            if(document.getElementById('conversion-win-rate')) {
                document.getElementById('conversion-win-rate').innerText = `Win Rate: ${stats.win_rate}%`;
            }

            if (!isSilent) {
                let actList = document.getElementById('recent-activity-list');
                actList.innerHTML = '';
                if(!stats.recent_activity || stats.recent_activity.length === 0) {
                    actList.innerHTML = `<p class="text-xs text-gray-500 text-center py-6">No recent logs.</p>`;
                } else {
                    stats.recent_activity.forEach(act => {
                        actList.innerHTML += `
                        <div class="flex items-center justify-between p-3 bg-gray-500/5 rounded-xl border border-custom gap-2">
                            <div class="truncate"><p class="text-xs font-bold text-custom-main truncate">${act.name}</p><span class="text-[10px] text-custom-muted truncate block">${act.company || 'Individual'}</span></div>
                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 shrink-0">${act.status}</span>
                        </div>`;
                    });
                }
            }
            
            renderPipelineGraph(stats.lead_status_counts);
        }

        function renderPipelineGraph(counts) {
            let chartEl = document.getElementById('dashboardPipelineChart');
            if(!chartEl) return;
            let ctx = chartEl.getContext('2d');
            if (pipelineChartInstance) pipelineChartInstance.destroy();
            let isDark = document.body.classList.contains('dark-mode');
            
            pipelineChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(counts || {}),
                    datasets: [{
                        data: Object.values(counts || {}),
                        backgroundColor: ['#6366f1', '#3b82f6', '#10b981', '#f43f5e'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: isDark ? '#9ca3af' : '#6b7280', font: { family: 'Plus Jakarta Sans', size: 11 } }, grid: { display: false } },
                        y: { ticks: { color: isDark ? '#9ca3af' : '#6b7280', precision: 0 }, grid: { color: isDark ? '#1f2937' : '#e5e7eb' } }
                    }
                }
            });
        }

        async function loadLeadsEngine() {
            rawLeads = await fetchAPI('get_leads') || [];
            renderLeadsTable();
        }

        function renderLeadsTable() {
            let query = document.getElementById('leadSearch').value.toLowerCase();
            let filter = document.getElementById('leadFilterStatus').value;
            let valueTierFilter = document.getElementById('leadFilterValueTier').value;
            let tbody = document.getElementById('leads-table-body');
            tbody.innerHTML = '';

            let targetList = rawLeads.filter(l => {
                let mq = l.name.toLowerCase().includes(query) || l.company.toLowerCase().includes(query);
                let mf = filter === 'All' || l.status === filter;
                let mv = true;
                if(valueTierFilter === 'High') mv = parseFloat(l.value || 0) >= 100000;
                if(valueTierFilter === 'Mid') mv = parseFloat(l.value || 0) < 100000;
                return mq && mf && mv;
            });

            if(targetList.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-500 font-medium">No records found.</td></tr>`;
                return;
            }

            targetList.forEach(l => {
                let isVip = parseFloat(l.value || 0) >= 100000;
                tbody.innerHTML += `
                <tr class="hover:bg-gray-500/5 transition">
                    <td class="p-4 font-semibold text-custom-main"><div class="text-xs font-bold">${l.name}</div><div class="text-[11px] text-custom-muted mt-0.5">${l.email} | ${l.phone}</div></td>
                    <td class="p-4 font-bold text-indigo-500">₹${parseFloat(l.value || 0).toLocaleString('en-IN')}</td>
                    <td class="p-4"><span class="text-[10px] px-2 py-0.5 rounded-lg ${isVip?'bg-amber-500/10 text-amber-500':'bg-gray-500/10 text-custom-muted'}">${isVip?'💎 VIP':'Standard'}</span></td>
                    <td class="p-4"><span class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-indigo-500/10 text-indigo-600">${l.status}</span></td>
                    <td class="p-4 text-[11px] text-custom-muted">${l.date}</td>
                    <td class="p-4 text-right space-x-1 whitespace-nowrap">
                        <button onclick="convertLead(${l.id})" class="text-[10px] font-bold text-emerald-600 bg-emerald-500/10 hover:bg-emerald-500/20 px-2 py-1 rounded-lg cursor-pointer">Convert</button>
                        <button onclick='editLeadModal(${JSON.stringify(l)})' class="text-[10px] text-blue-600 bg-blue-500/10 hover:bg-blue-500/20 px-2 py-1 rounded-lg cursor-pointer"><i class="fa-solid fa-pen"></i></button>
                        <button onclick="deleteLead(${l.id})" class="text-[10px] text-rose-600 bg-rose-500/10 hover:bg-rose-500/20 px-2 py-1 rounded-lg cursor-pointer"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>`;
            });
        }

        function openLeadModal() {
            document.getElementById('lead-form').reset();
            document.getElementById('lead_id').value = '';
            let m = document.getElementById('leadModal');
            m.classList.remove('opacity-0', 'pointer-events-none');
            m.firstElementChild.classList.remove('scale-95');
        }

        function closeLeadModal() {
            let m = document.getElementById('leadModal');
            m.classList.add('opacity-0', 'pointer-events-none');
            m.firstElementChild.classList.add('scale-95');
        }

        function editLeadModal(lead) {
            openLeadModal();
            document.getElementById('lead_id').value = lead.id;
            document.getElementById('lead_name').value = lead.name;
            document.getElementById('lead_company').value = lead.company;
            document.getElementById('lead_email').value = lead.email;
            document.getElementById('lead_phone').value = lead.phone;
            document.getElementById('lead_status').value = lead.status;
            document.getElementById('lead_value').value = lead.value;
            document.getElementById('lead_date').value = lead.date;
        }

        async function handleLeadSubmit(e) {
            e.preventDefault();
            let fd = new FormData();
            fd.append('id', document.getElementById('lead_id').value);
            fd.append('name', document.getElementById('lead_name').value);
            fd.append('company', document.getElementById('lead_company').value);
            fd.append('email', document.getElementById('lead_email').value);
            fd.append('phone', document.getElementById('lead_phone').value);
            fd.append('status', document.getElementById('lead_status').value);
            fd.append('value', document.getElementById('lead_value').value);
            fd.append('date', document.getElementById('lead_date').value);

            let res = await fetchAPI('save_lead', fd);
            if(res && res.success) { closeLeadModal(); popToast("Database Registry Updated!"); loadLeadsEngine(); }
        }

        async function deleteLead(id) {
            if(!confirm("Are you sure?")) return;
            let fd = new FormData(); fd.append('id', id);
            await fetchAPI('delete_lead', fd);
            popToast("Entry wiped out.");
            loadLeadsEngine();
        }

        async function convertLead(id) {
            let fd = new FormData(); fd.append('id', id);
            let res = await fetchAPI('convert_to_customer', fd);
            if(res && res.success) { popToast("Converted to Customer!"); loadLeadsEngine(); }
        }

        async function loadCustomersEngine() {
            rawCustomers = await fetchAPI('get_customers') || [];
            let tbody = document.getElementById('customers-table-body');
            tbody.innerHTML = '';
            if(rawCustomers.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-gray-500 font-medium">No converted clients.</td></tr>`;
                return;
            }
            rawCustomers.forEach(c => {
                tbody.innerHTML += `
                <tr class="hover:bg-gray-500/5 transition">
                    <td class="p-4 font-bold text-custom-main">${c.name}</td><td class="p-4 text-custom-muted">${c.company || 'N/A'}</td>
                    <td class="p-4 text-[11px] text-indigo-600">${c.email} <br> ${c.phone}</td>
                    <td class="p-4 font-extrabold text-emerald-500">₹${parseFloat(c.revenue || 0).toLocaleString('en-IN')}</td>
                    <td class="p-4 text-[11px] text-custom-muted">${c.joined_date}</td>
                </tr>`;
            });
        }

        async function loadAutomationEngine() {
            rawAutomation = await fetchAPI('get_automation_queue') || [];
            rawLeads = await fetchAPI('get_leads') || []; 
            
            let injectorList = document.getElementById('automation-leads-injector-list');
            injectorList.innerHTML = '';
            if(rawLeads.length === 0) {
                injectorList.innerHTML = `<p class="text-[10px] text-gray-500 text-center py-2">No active leads found.</p>`;
            } else {
                rawLeads.forEach(l => {
                    injectorList.innerHTML += `
                    <label class="flex items-center gap-2 text-[11px] font-medium p-1 hover:bg-gray-500/10 rounded cursor-pointer text-custom-main">
                        <input type="checkbox" name="automation_leads_checked" value="${l.id}" class="rounded text-indigo-600 focus:ring-0">
                        <span>${l.name} (${l.phone})</span>
                    </label>`;
                });
            }
            renderAutomationTable();
        }

        // =========================================================================
        // WHATSAPP & MAIL PIN SYSTEM LOGIC
        // =========================================================================
        function getDispatchLog() {
            try {
                return JSON.parse(localStorage.getItem('crm_dispatch_pins') || '{}');
            } catch {
                return {};
            }
        }

        function markDispatched(id, channel) {
            let logs = getDispatchLog();
            logs[id] = { channel: channel, timestamp: new Date().toLocaleTimeString() };
            localStorage.setItem('crm_dispatch_pins', JSON.stringify(logs));
            renderAutomationTable();
        }

        function renderAutomationTable() {
            let tbody = document.getElementById('automation-queue-body');
            tbody.innerHTML = '';
            if (rawAutomation.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="p-6 text-center text-gray-500 font-medium">No records inside the queue dashboard grid.</td></tr>`;
                return;
            }

            let dispatchPins = getDispatchLog();

            rawAutomation.forEach(item => {
                let encodedText = encodeURIComponent(item.message);
                let waLink = `https://api.whatsapp.com/send?phone=${item.phone}&text=${encodedText}`;
                let mailLink = `mailto:${item.email}?subject=Broadcast&body=${encodedText}`;

                // Sent Tracking Pin Configuration
                let dispatchInfo = dispatchPins[item.id];
                let pinHtml = '';
                if (dispatchInfo) {
                    let pinColor = dispatchInfo.channel === 'whatsapp' ? 'text-rose-500' : 'text-red-600';
                    let pinTitle = `Sent via ${dispatchInfo.channel.toUpperCase()} at ${dispatchInfo.timestamp}`;
                    pinHtml = `<span class="ml-1.5 inline-flex items-center" title="${pinTitle}"><i class="fa-solid fa-location-pin ${pinColor} animate-bounce text-[14px]"></i></span>`;
                }

                tbody.innerHTML += `
                <tr class="hover:bg-gray-500/5 transition border-b border-custom text-xs">
                    <td class="p-3 font-semibold text-custom-main">
                        <div class="flex items-center font-bold">
                            ${item.name} ${pinHtml}
                        </div>
                        <div class="text-[10px] text-custom-muted mt-0.5">${item.phone}</div>
                    </td>
                    <td class="p-3 text-custom-muted max-w-[220px] truncate" title="${item.message}">${item.message}</td>
                    <td class="p-3 text-right space-x-1 whitespace-nowrap">
                        <a href="${waLink}" target="_blank" onclick="markDispatched('${item.id}', 'whatsapp')" class="inline-flex items-center gap-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 px-2 py-0.5 rounded text-[10px] font-bold transition"><i class="fa-brands fa-whatsapp"></i> Chat</a>
                        <a href="${mailLink}" onclick="markDispatched('${item.id}', 'email')" class="inline-flex items-center gap-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 px-2 py-0.5 rounded text-[10px] font-bold transition"><i class="fa-solid fa-envelope"></i> Email</a>
                    </td>
                </tr>`;
            });
        }

        async function deployLiveLeadsToAutomation() {
            let checkedBoxes = document.querySelectorAll('input[name="automation_leads_checked"]:checked');
            let template = document.getElementById('auto_msg_template').value;
            
            if(checkedBoxes.length === 0) return alert("Please select at least one live funnel lead!");
            if(!template) return alert("Please compose your marketing message blueprint!");
            
            let fd = new FormData();
            checkedBoxes.forEach(cb => fd.append('lead_ids[]', cb.value));
            fd.append('message', template);
            
            let res = await fetchAPI('process_lead_automation', fd);
            if(res && res.success) { popToast(res.message); loadAutomationEngine(); }
        }

        async function handleSheetUpload(e) {
            e.preventDefault();
            let fileInput = document.getElementById('automation_file');
            if (fileInput.files.length === 0) return alert("Please select a file first!");
            let fd = new FormData(); fd.append('automation_file', fileInput.files[0]);
            let res = await fetchAPI('upload_automation_sheet', fd);
            if (res && res.success) { 
                popToast(res.message); 
                document.getElementById('automation-upload-form').reset(); 
                loadAutomationEngine(); 
            } else {
                alert(res.message || "Upload failed.");
            }
        }

        async function clearAutomationLogs() {
            if(!confirm("Flush records?")) return;
            let res = await fetchAPI('clear_automation_queue');
            if (res && res.success) { 
                // LocalStorage pins register ko bhi clear kar dete hain safety ke liye
                localStorage.removeItem('crm_dispatch_pins');
                popToast("Queue reset."); 
                loadAutomationEngine(); 
            }
        }

        async function loadTasksEngine() {
            rawTasks = await fetchAPI('get_tasks') || [];
            let container = document.getElementById('tasks-list'); container.innerHTML = '';
            if(rawTasks.length === 0) {
                container.innerHTML = `<p class="text-xs text-gray-500 text-center py-4">No pending objectives.</p>`; return;
            }
            rawTasks.forEach(t => {
                let isComp = t.status === 'Completed';
                container.innerHTML += `
                <div class="flex items-center justify-between p-3 bg-gray-500/5 border border-custom rounded-xl ${isComp?'opacity-40 line-through':''}">
                    <div class="flex items-center gap-3">
                        <input type="checkbox" ${isComp?'checked':''} onclick="toggleTask(${t.id})" class="w-4 h-4 text-indigo-600 rounded focus:ring-0">
                        <div><p class="text-xs font-bold text-custom-main">${t.title}</p><span class="text-[10px] text-custom-muted">Due: ${t.due_date}</span></div>
                    </div>
                    <button onclick="deleteTask(${t.id})" class="text-gray-400 hover:text-rose-500 text-xs transition p-1"><i class="fa-solid fa-trash-can"></i></button>
                </div>`;
            });
        }

        async function handleTaskSubmit(e) {
            e.preventDefault();
            let fd = new FormData();
            fd.append('title', document.getElementById('task_title').value);
            fd.append('due_date', document.getElementById('task_due').value);
            fd.append('priority', document.getElementById('task_priority').value);
            await fetchAPI('save_task', fd); document.getElementById('task-form').reset(); loadTasksEngine();
        }

        async function toggleTask(id) { let fd = new FormData(); fd.append('id', id); await fetchAPI('toggle_task', fd); loadTasksEngine(); }
        async function deleteTask(id) { let fd = new FormData(); fd.append('id', id); await fetchAPI('delete_task', fd); loadTasksEngine(); }

        async function loadReportsEngine() {
            let stats = await fetchAPI('get_dashboard_stats');
            if(!stats) return;
            let ctxPie = document.getElementById('reportPieChart').getContext('2d');
            let ctxDoughnut = document.getElementById('reportDoughnutChart').getContext('2d');

            if (reportPieChartInstance) reportPieChartInstance.destroy();
            if (reportDoughnutChartInstance) reportDoughnutChartInstance.destroy();
            let isDark = document.body.classList.contains('dark-mode');

            let chartOptions = { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: isDark ? '#9ca3af' : '#6b7280', font: { size: 10 } } } } };

            reportPieChartInstance = new Chart(ctxPie, {
                type: 'pie',
                data: { labels: Object.keys(stats.lead_status_counts || {}), datasets: [{ data: Object.values(stats.lead_status_counts || {}), backgroundColor: ['#6366f1', '#3b82f6', '#10b981', '#f43f5e'] }] },
                options: chartOptions
            });

            reportDoughnutChartInstance = new Chart(ctxDoughnut, {
                type: 'doughnut',
                data: { labels: ['Leads', 'Clients'], datasets: [{ data: [stats.total_leads || 0, stats.total_customers || 0], backgroundColor: ['#6366f1', '#10b981'] }] },
                options: chartOptions
            });
        }
        
        function exportLeadsToCSV() {
            if (rawLeads.length === 0) return alert("No entries found!");
            let csv = "ID,Name,Company,Email,Phone,Status,Value\\n";
            rawLeads.forEach(l => { csv += `${l.id},"${l.name}","${l.company}",${l.email},${l.phone},${l.status},${l.value}\\n`; });
            let link = document.createElement("a"); link.setAttribute("href", encodeURI("data:text/csv;charset=utf-8," + csv));
            link.setAttribute("download", "CRM_Leads.csv"); document.body.appendChild(link); link.click(); document.body.removeChild(link);
        }

        // =========================================================================
        // HIGH PERFORMANCE CLIENT EXPORT ENGINES (XLSX & PDF GENERATION)
        // =========================================================================
        async function exportFullCRMDataToExcel() {
            try {
                let stats = await fetchAPI('get_dashboard_stats') || {};
                let leads = await fetchAPI('get_leads') || [];
                let customers = await fetchAPI('get_customers') || [];
                let tasks = await fetchAPI('get_tasks') || [];

                let wb = XLSX.utils.book_new();

                // Sheet 1: General Stats & Metric Summary Overview
                let summaryData = [
                    ["KPI / Metrics Parameter", "Registry Values"],
                    ["Total Leads Captured", stats.total_leads || leads.length],
                    ["Active Customers Converted", stats.total_customers || customers.length],
                    ["Uncompleted Objectives", stats.pending_tasks || 0],
                    ["Pipeline Valuation Pool", stats.total_pipeline_value || 0],
                    ["Average Active Deal Size", stats.average_deal_size || 0],
                    ["Aggregate Gross Revenue Pool", stats.total_revenue_pool || 0],
                    ["Conversion Velocity Rate (%)", `${stats.win_rate || 0}%`]
                ];
                let wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
                XLSX.utils.book_append_sheet(wb, wsSummary, "Dashboard Overview");

                // Sheet 2: Leads Registry Datatable 
                let leadsData = [["Database ID", "Client Name", "Corporate Company", "Email Link", "Mobile Contact", "Funnel Status", "Est Value", "Date Created"]];
                leads.forEach(l => {
                    leadsData.push([l.id, l.name, l.company || "N/A", l.email, l.phone, l.status, l.value, l.date]);
                });
                let wsLeads = XLSX.utils.aoa_to_sheet(leadsData);
                XLSX.utils.book_append_sheet(wb, wsLeads, "Leads Matrix");

                // Sheet 3: Converted Customer Database Records
                let customerData = [["Database ID", "Customer Entity Name", "Corporate Company", "Email ID", "Mobile Contact", "Calculated Revenue Generated", "Retention Date"]];
                customers.forEach(c => {
                    customerData.push([c.id, c.name, c.company || "N/A", c.email, c.phone, c.revenue, c.joined_date]);
                });
                let wsCustomers = XLSX.utils.aoa_to_sheet(customerData);
                XLSX.utils.book_append_sheet(wb, wsCustomers, "Active Customers");

                // Save Workbook Output Link
                XLSX.writeFile(wb, `CRM_System_Export_Metrics_${new Date().toISOString().slice(0, 10)}.xlsx`);
                popToast("Excel Database Compiled Successfully!");
            } catch (err) {
                console.error("Critical Excel Packaging Exception:", err);
                alert("Failed to export Excel report sheets.");
            }
        }

        async function exportFullCRMToPDF() {
            const mainContainer = document.getElementById('exportable-main-area');
            if (!mainContainer) return alert("System Anchor reference broken down.");
            
            popToast("Preparing High-Res Executive PDF document structure...");

            // Optimal configuration logic keeping canvas and graphs completely readable
            let pdfOptions = {
                margin: [10, 10, 10, 10],
                filename: `OrbitEdge_CRM_Executive_Summary_${new Date().toISOString().slice(0,10)}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { 
                    scale: 2, 
                    useCORS: true, 
                    backgroundColor: document.body.classList.contains('dark-mode') ? '#030712' : '#f3f4f6' 
                },
                jsPDF: { unit: 'mm', format: 'a3', orientation: 'landscape' }
            };

            html2pdf().set(pdfOptions).from(mainContainer).save().then(() => {
                popToast("Executive PDF Export completed!");
            });
        }
    </script>
{% endif %}
</body>
</html>
"""

# =========================================================================
# APPLICATION GATEWAY INITIALIZATION RUNNER
# =========================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
