import os
import json
import time
import random
import csv
from io import StringIO
from threading import Lock
from flask import Flask, Blueprint, render_template_string, request, jsonify, session, redirect, url_for

# =========================================================================
# INITIALIZE FLASK CORE & BLUEPRINT
# =========================================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

script34_bp = Blueprint('script34', __name__)

DATA_FILE = 'crm_data.json'

AUTH_USER = 'admin'
AUTH_PASS = '5hsuusu78@#/@&hsb' 

db_lock = Lock()

# =========================================================================
# LOCAL STORAGE ENGINE
# =========================================================================
def get_default_structure():
    return {
        'leads': [
            {"id": 1, "name": "Rahul Sharma", "email": "rahul@example.com", "phone": "+919876543210", "company": "Sharma Tech", "status": "New", "value": 45000, "date": "2026-07-10", "assigned_to": "Amit Singh"},
            {"id": 2, "name": "Amit Verma", "email": "amit@example.com", "phone": "+918765432109", "company": "Verma Digital", "status": "Contacted", "value": 120000, "date": "2026-07-11", "assigned_to": "Pooja Raj"}
        ],
        'customers': [
            {"id": 3, "name": "Priya Singh", "email": "priya@example.com", "phone": "+917654321098", "company": "Singh Org", "revenue": 150000, "joined_date": "2026-07-11", "history": ["Account provisioned perfectly", "Onboarding consultancy completed"], "purchases": [{"item": "Premium Cloud Server Setup", "cost": 150000, "date": "2026-07-11"}], "notes": "Prefers late evening direct updates.", "documents": ["service_level_agreement_v1.pdf"]}
        ],
        'tasks': [
            {"id": 1, "title": "Setup Marketing Automation Gateway", "due_date": "2026-07-15", "priority": "High", "status": "Pending", "type": "Task"}
        ],
        'automation_queue': [],
        'invoices': [
            {"id": 101, "client_name": "Priya Singh", "amount": 150000, "items": "Premium Cloud Server Setup", "date": "2026-07-11", "status": "Paid"}
        ],
        'quotations': [
            {"id": 201, "client_name": "Sharma Tech", "amount": 45000, "items": "Security Consultation Suite", "date": "2026-07-10", "status": "Draft"}
        ],
        'employees': [
            {"name": "Amit Singh", "deals_closed": 4, "revenue_brought": 280000},
            {"name": "Pooja Raj", "deals_closed": 6, "revenue_brought": 410000},
            {"name": "Vikram Malhotra", "deals_closed": 3, "revenue_brought": 195000}
        ]
    }

def db_read():
    """Local JSON Engine se data fetch karta hai"""
    with db_lock:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                try: 
                    data = json.load(f)
                    if 'invoices' not in data: data['invoices'] = []
                    if 'quotations' not in data: data['quotations'] = []
                    if 'employees' not in data: data['employees'] = get_default_structure()['employees']
                    return data
                except: 
                    return get_default_structure()
        return get_default_structure()

def db_write(data):
    """Local JSON Engine par data update (dump) karta hai"""
    with db_lock:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

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
    invoices = db.get('invoices', [])
    
    total_value = sum(float(l.get('value', 0) or 0) for l in leads)
    leads_count = len(leads)
    avg_value = total_value / leads_count if leads_count > 0 else 0
    total_revenue = sum(float(c.get('revenue', 0) or 0) for c in customers)
    high_value_leads_count = len([l for l in leads if float(l.get('value', 0) or 0) >= 100000])
    
    total_pipeline_entities = leads_count + len(customers)
    win_rate = (len(customers) / total_pipeline_entities * 100) if total_pipeline_entities > 0 else 0

    forecast_value = 0
    for l in leads:
        status = l.get('status', 'New')
        val = float(l.get('value', 0) or 0)
        if status == 'New': forecast_value += val * 0.15
        elif status == 'Contacted': forecast_value += val * 0.40
        elif status == 'Proposal': forecast_value += val * 0.75

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
        'sales_forecast': round(forecast_value, 2),
        'total_invoices': len(invoices),
        'lead_status_counts': {'New': 0, 'Contacted': 0, 'Proposal': 0, 'Lost': 0},
        'recent_activity': list(reversed(leads))[:6],
        'employees': db.get('employees', [])
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
        'assigned_to': request.form.get('assigned_to', 'Amit Singh'),
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
            'joined_date': time.strftime('%Y-%m-%d'),
            'history': [f"Converted from Lead Pipeline allocation. Target valuation closure: ₹{target_lead.get('value', 0)}"],
            'purchases': [{"item": "Initial Core Deal Pipeline Conversion Portfolio", "cost": float(target_lead.get('value', 0) or 0), "date": time.strftime('%Y-%m-%d')}],
            'notes': "Auto converted via pipeline interface module.",
            'documents': ["initial_invoice_allocation.pdf"]
        })
        
        # Performance mapping counter logic
        agent = target_lead.get('assigned_to', 'Amit Singh')
        for emp in db.get('employees', []):
            if emp['name'] == agent:
                emp['deals_closed'] += 1
                emp['revenue_brought'] += float(target_lead.get('value', 0) or 0)
                break
                
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

@script34_bp.route('/api/update_customer_profile', methods=['POST'])
def update_customer_profile():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    cid = int(request.form.get('id', 0))
    notes = request.form.get('notes', '')
    history_entry = request.form.get('history_entry', '')
    doc_entry = request.form.get('doc_entry', '')
    
    for c in db.get('customers', []):
        if c['id'] == cid:
            if notes: c['notes'] = notes
            if history_entry: c['history'].append(history_entry)
            if doc_entry: c['documents'].append(doc_entry)
            break
    db_write(db)
    return jsonify({'success': True, 'message': 'Customer profile matrix sync complete.'})

@script34_bp.route('/api/save_task', methods=['POST'])
def save_task():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    db['tasks'].append({
        'id': int(time.time() + random.randint(1000, 9999)),
        'title': request.form.get('title', ''),
        'due_date': request.form.get('due_date', ''),
        'priority': request.form.get('priority', 'Medium'),
        'type': request.form.get('type', 'Task'),
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

@script34_bp.route('/api/get_financials', methods=['GET'])
def get_financials():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    return jsonify({
        'invoices': db.get('invoices', []),
        'quotations': db.get('quotations', [])
    })

@script34_bp.route('/api/save_document', methods=['POST'])
def save_document():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    doc_type = request.form.get('doc_type', 'invoice') 
    
    doc_data = {
        'id': int(time.time() + random.randint(1000, 9999)),
        'client_name': request.form.get('client_name', ''),
        'amount': float(request.form.get('amount', 0) or 0),
        'items': request.form.get('items', 'General Consultation'),
        'date': time.strftime('%Y-%m-%d'),
        'status': 'Unpaid' if doc_type == 'invoice' else 'Draft'
    }
    
    if doc_type == 'invoice':
        db['invoices'].append(doc_data)
    else:
        db['quotations'].append(doc_data)
        
    db_write(db)
    return jsonify({'success': True})

@script34_bp.route('/api/update_doc_status', methods=['POST'])
def update_doc_status():
    if not is_authenticated(): return jsonify({'error': 'Unauthorized'}), 401
    db = db_read()
    doc_id = int(request.form.get('id', 0))
    doc_type = request.form.get('doc_type', 'invoice')
    new_status = request.form.get('status', '')
    
    target_key = 'invoices' if doc_type == 'invoice' else 'quotations'
    for doc in db.get(target_key, []):
        if doc['id'] == doc_id:
            doc['status'] = new_status
            break
            
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
                'assigned_to': 'Amit Singh',
                'date': time.strftime('%Y-%m-%d')
            })
            imported_count += 1
            
        db_write(db)
        return jsonify({'success': True, 'message': f'Successfully parsed {imported_count} contacts & perfectly linked into Pipeline system!'})
        
    return jsonify({'success': False, 'message': 'Invalid file layout format.'})

app.register_blueprint(script34_bp, url_prefix='/')

# HTML UI Layout Injecting dynamic layouts & Financial stacks
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
                <button onclick="switchTab('leads')" id="btn-leads" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-bullseye w-5 text-center"></i> Pipeline & Deals</button>
                <button onclick="switchTab('customers')" id="btn-customers" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-users w-5 text-center"></i> Active Customers</button>
                <button onclick="switchTab('automation')" id="btn-automation" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-paper-plane w-5 text-center"></i> Bulk Automation</button>
                <button onclick="switchTab('tasks')" id="btn-tasks" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-list-check w-5 text-center"></i> Tasks & Reminders</button>
                <button onclick="switchTab('sales_finance')" id="btn-sales_finance" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-file-invoice-dollar w-5 text-center"></i> Financial Matrix</button>
                <button onclick="switchTab('reports')" id="btn-reports" class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-900 hover:text-white cursor-pointer"><i class="fa-solid fa-chart-pie w-5 text-center"></i> Advanced Reports</button>
            </nav>
            <div class="p-4 border-t border-gray-900 space-y-2">
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-gray-900 text-xs font-semibold cursor-pointer text-gray-300">
                    <span>Appearance</span><i id="theme-icon" class="fa-solid fa-moon"></i>
                </button>
                <a href="action/logout" class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-500/10"><i class="fa-solid fa-right-from-bracket"></i> Clear Session</a>
            </div>
        </aside>

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
                            Local Sync Engine Active <span id="conversion-win-rate" class="ml-2 bg-indigo-600 text-white px-1.5 py-0.5 rounded text-[10px]">Win Rate: 0%</span>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
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
                    <div class="panel-card p-4 rounded-2xl border bg-gradient-to-br from-indigo-900/20 to-violet-900/20 flex items-center gap-3">
                        <div class="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl"><i class="fa-solid fa-crystal-ball text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-indigo-400">Forecast</p><h3 id="stat-forecast-value" class="text-base font-extrabold text-indigo-300">₹0</h3></div>
                    </div>
                    <div class="panel-card p-4 rounded-2xl border flex items-center gap-3">
                        <div class="p-2.5 bg-emerald-500/20 text-emerald-600 rounded-xl"><i class="fa-solid fa-gavel text-lg"></i></div>
                        <div><p class="text-[10px] font-bold uppercase text-custom-muted">Revenue</p><h3 id="stat-revenue-pool" class="text-xl font-extrabold text-emerald-500">₹0</h3></div>
                    </div>
                </div>

                <!-- SUB DASHBOARD SPLITS (SALES, LEADS & REVENUE HEADS) -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="panel-card p-5 rounded-2xl border">
                        <h3 class="font-bold text-sm mb-3 text-indigo-500"><i class="fa-solid fa-money-bill-trend-up"></i> Sales Performance Matrix</h3>
                        <div class="text-xs space-y-2 text-custom-main">
                            <div class="flex justify-between border-b border-custom pb-1"><span>Target Close Ratio:</span><span class="font-bold">78%</span></div>
                            <div class="flex justify-between border-b border-custom pb-1"><span>Quarterly Velocity:</span><span class="font-bold text-emerald-500">+14.2%</span></div>
                            <div class="flex justify-between"><span>Pipeline Efficiency:</span><span class="font-bold text-indigo-400">Optimal</span></div>
                        </div>
                    </div>
                    <div class="panel-card p-5 rounded-2xl border">
                        <h3 class="font-bold text-sm mb-3 text-amber-500"><i class="fa-solid fa-magnet"></i> Marketing Lead Capture</h3>
                        <div class="text-xs space-y-2 text-custom-main">
                            <div class="flex justify-between border-b border-custom pb-1"><span>Organic Channels:</span><span class="font-bold">45%</span></div>
                            <div class="flex justify-between border-b border-custom pb-1"><span>Bulk Sheet Sync Ingest:</span><span class="font-bold">35%</span></div>
                            <div class="flex justify-between"><span>Referral Network Acquisition:</span><span class="font-bold text-purple-500">20%</span></div>
                        </div>
                    </div>
                    <div class="panel-card p-5 rounded-2xl border">
                        <h3 class="font-bold text-sm mb-3 text-emerald-500"><i class="fa-solid fa-vault"></i> Real-time Revenue Operations</h3>
                        <div class="text-xs space-y-2 text-custom-main">
                            <div class="flex justify-between border-b border-custom pb-1"><span>Invoiced Clearances:</span><span class="font-bold text-emerald-500">100% Secure</span></div>
                            <div class="flex justify-between border-b border-custom pb-1"><span>Outstanding Collections:</span><span class="font-bold">₹0.00</span></div>
                            <div class="flex justify-between"><span>Liquidity Index Value:</span><span class="font-bold">1.0 Core</span></div>
                        </div>
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

                <!-- EMPLOYEE PERFORMANCE ANALYSIS SYSTEM -->
                <div class="panel-card p-6 rounded-2xl border">
                    <h3 class="font-bold text-base mb-4 text-custom-main"><i class="fa-solid fa-graduation-cap text-indigo-500"></i> Employee Conversion Performance Ecosystem</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs">
                            <thead>
                                <tr class="border-b border-custom text-custom-muted font-bold uppercase bg-gray-500/5">
                                    <th class="p-3">Consultant/Representative Name</th>
                                    <th class="p-3">Deals Successfully Closed</th>
                                    <th class="p-3">Total Capital Revenue Injected</th>
                                    <th class="p-3">Operational Progress Rank</th>
                                </tr>
                            </thead>
                            <tbody id="employee-performance-body" class="divide-y divide-custom text-custom-main"></tbody>
                        </table>
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
                
                <div class="panel-card p-4 rounded-xl border grid grid-cols-1 sm:grid-cols-4 gap-4 items-center">
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
                    <div>
                        <select id="leadFilterEmployee" onchange="renderLeadsTable()" class="w-full input-custom border rounded-xl px-3 py-2 text-xs focus:outline-none">
                            <option value="All">All Owners/Agents</option>
                            <option value="Amit Singh">Amit Singh</option>
                            <option value="Pooja Raj">Pooja Raj</option>
                            <option value="Vikram Malhotra">Vikram Malhotra</option>
                        </select>
                    </div>
                </div>
                <div class="panel-card rounded-xl border overflow-x-auto shadow-sm">
                    <table class="w-full text-left border-collapse min-w-[600px]">
                        <thead>
                            <tr class="border-b border-custom text-custom-muted text-[11px] font-bold uppercase bg-gray-500/5">
                                <th class="p-4">Client / Company</th><th class="p-4">Est Value</th><th class="p-4">Dynamic Tier</th><th class="p-4">Funnel Position</th><th class="p-4">Owner Assignment</th><th class="p-4">Date Added</th><th class="p-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="leads-table-body" class="divide-y divide-custom text-xs text-custom-main"></tbody>
                    </table>
                </div>
            </div>

            <!-- CUSTOMERS TAB & ADVANCED USER PROFILE SUITE -->
            <div id="tab-customers" class="tab-content hidden space-y-6">
                <div><h1 class="text-2xl font-bold text-custom-main">Active Accounts Profile Database</h1><p class="text-sm text-custom-muted">Converted official revenue generators, profiles, tracking records and documentation modules.</p></div>
                
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    <div class="xl:col-span-2 panel-card rounded-xl border overflow-x-auto shadow-sm h-fit">
                        <table class="w-full text-left border-collapse min-w-[600px]">
                            <thead>
                                <tr class="border-b border-custom text-custom-muted text-[11px] font-bold uppercase bg-gray-500/5">
                                    <th class="p-4">Customer Entity</th><th class="p-4">Corporate Brand</th><th class="p-4">Contact Logic</th><th class="p-4">Revenue Generated</th><th class="p-4 text-right">System Action</th>
                                </tr>
                            </thead>
                            <tbody id="customers-table-body" class="divide-y divide-custom text-xs text-custom-main"></tbody>
                        </table>
                    </div>

                    <!-- SIDEWAYS CONTEXTUAL INTERACTIVE PROFILE CONFIGURATOR -->
                    <div class="panel-card p-6 rounded-2xl border space-y-6 hidden" id="customer-profile-panel">
                        <div class="flex justify-between items-center border-b border-custom pb-3">
                            <div>
                                <h3 class="font-bold text-base text-indigo-500" id="profile-pane-name">Client Core Profile</h3>
                                <p class="text-[10px] text-custom-muted" id="profile-pane-brand">Company Brand Assignment</p>
                            </div>
                            <button onclick="document.getElementById('customer-profile-panel').classList.add('hidden')" class="text-custom-muted hover:text-rose-500"><i class="fa-solid fa-xmark"></i></button>
                        </div>

                        <!-- PURCHASE MATRIX HISTORY LISTING -->
                        <div>
                            <h4 class="text-xs font-bold uppercase text-custom-muted tracking-wider mb-2"><i class="fa-solid fa-cart-flatbed-suitcases"></i> Validated Purchase Ledger</h4>
                            <div id="profile-pane-purchases" class="space-y-2 max-h-32 overflow-y-auto text-xs bg-gray-500/5 p-2 rounded-xl border border-custom"></div>
                        </div>

                        <!-- OPERATIONAL ACTION CHRONOLOGY HISTORY -->
                        <div>
                            <h4 class="text-xs font-bold uppercase text-custom-muted tracking-wider mb-2"><i class="fa-solid fa-timeline"></i> Action Log Chronicles</h4>
                            <div id="profile-pane-history" class="space-y-1.5 max-h-32 overflow-y-auto text-[11px] text-custom-main"></div>
                            <div class="mt-2 flex gap-2">
                                <input type="text" id="new-history-entry" placeholder="Log interactions..." class="w-full input-custom border text-xs px-2.5 py-1.5 rounded-lg focus:outline-none">
                                <button onclick="appendCustomerHistory()" class="bg-indigo-600 text-white text-xs px-3 rounded-lg"><i class="fa-solid fa-plus"></i></button>
                            </div>
                        </div>

                        <!-- NOTE MANAGEMENT MATRIX -->
                        <div>
                            <h4 class="text-xs font-bold uppercase text-custom-muted tracking-wider mb-2"><i class="fa-solid fa-note-sticky text-amber-500"></i> Corporate Overview Notes</h4>
                            <textarea id="profile-pane-notes" rows="3" class="w-full input-custom border text-xs p-2 rounded-xl focus:outline-none resize-none"></textarea>
                            <button onclick="saveCustomerNotes()" class="w-full mt-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-1.5 rounded-lg text-xs transition">Save Profile Notes</button>
                        </div>

                        <!-- SECURE DIGITAL DOCUMENT STORAGE MAPPING -->
                        <div>
                            <h4 class="text-xs font-bold uppercase text-custom-muted tracking-wider mb-2"><i class="fa-solid fa-folder-open text-blue-500"></i> Managed Document Records</h4>
                            <div id="profile-pane-docs" class="space-y-1 text-[11px] font-mono text-indigo-400 mb-2"></div>
                            <div class="flex gap-2">
                                <input type="text" id="new-doc-entry" placeholder="E.g., contract_final.pdf" class="w-full input-custom border text-xs px-2.5 py-1.5 rounded-lg focus:outline-none">
                                <button onclick="appendCustomerDoc()" class="bg-blue-600 text-white text-xs px-3 rounded-lg">Link</button>
                            </div>
                        </div>
                    </div>
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
                        <h3 class="font-bold text-base mb-4 text-indigo-500"><i class="fa-solid fa-calendar-check"></i> Register Objective / Reminder</h3>
                        <form id="task-form" onsubmit="handleTaskSubmit(event)" class="space-y-4">
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Objective Title</label>
                                <input type="text" id="task_title" required placeholder="E.g., Review Dashboard System" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Objective Type</label>
                                <select id="task_type" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                                    <option value="Task">📅 General Task Assignment</option>
                                    <option value="Follow-up">🔔 Follow-up Reminder</option>
                                    <option value="Call">📞 Call Reminder</option>
                                    <option value="Meeting">🤝 Meeting Assignment</option>
                                </select>
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
                            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl text-xs cursor-pointer transition">Inject Objective Engine</button>
                        </form>
                    </div>
                    <div class="lg:col-span-2 panel-card p-6 rounded-2xl border flex flex-col shadow-sm">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="font-bold text-base text-custom-main">Active Strategic Roadmap</h3>
                            <button onclick="syncToLocalCalendar()" class="bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 px-3 py-1 rounded-xl text-xs font-bold hover:bg-indigo-500/20 transition">
                                <i class="fa-solid fa-calendar-days"></i> Local Calendar Sync
                            </button>
                        </div>
                        <div id="tasks-list" class="space-y-3 flex-1 overflow-y-auto max-h-[450px]"></div>
                    </div>
                </div>
            </div>

            <!-- FINANCIAL TAB -->
            <div id="tab-sales_finance" class="tab-content hidden space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="panel-card p-6 rounded-2xl border h-fit shadow-sm">
                        <h3 class="font-bold text-base mb-4 text-emerald-500"><i class="fa-solid fa-file-invoice"></i> Generate Financial Record</h3>
                        <form id="doc-form" onsubmit="handleDocSubmit(event)" class="space-y-4">
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Document Framework</label>
                                <select id="doc_type" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                                    <option value="invoice">📄 Invoice Generator</option>
                                    <option value="quotation">📝 Quotation Generator</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Client Target Name</label>
                                <input type="text" id="doc_client" required placeholder="E.g., Shikhotech Academy" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Line Items Description</label>
                                <input type="text" id="doc_items" required placeholder="E.g., Security Auditing Program" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-custom-muted mb-1.5">Valuation Amount (₹)</label>
                                <input type="number" id="doc_amount" required placeholder="50000" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                            </div>
                            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-xl text-xs cursor-pointer transition">Commit Financial Entry</button>
                        </form>
                    </div>

                    <div class="lg:col-span-2 space-y-6">
                        <div class="panel-card p-6 rounded-2xl border flex flex-col shadow-sm">
                            <h3 class="font-bold text-sm text-custom-main mb-3"><i class="fa-solid fa-receipt text-emerald-500"></i> Issued Invoices Stack</h3>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs">
                                    <thead>
                                        <tr class="border-b border-custom text-custom-muted font-bold bg-gray-500/5">
                                            <th class="p-2.5">Client</th><th class="p-2.5">Description</th><th class="p-2.5">Amount</th><th class="p-2.5">Status</th><th class="p-2.5 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="invoice-table-body" class="divide-y divide-custom text-custom-main"></tbody>
                                </table>
                            </div>
                        </div>

                        <div class="panel-card p-6 rounded-2xl border flex flex-col shadow-sm">
                            <h3 class="font-bold text-sm text-custom-main mb-3"><i class="fa-solid fa-file-lines text-indigo-500"></i> Open Active Quotations</h3>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs">
                                    <thead>
                                        <tr class="border-b border-custom text-custom-muted font-bold bg-gray-500/5">
                                            <th class="p-2.5">Client</th><th class="p-2.5">Description</th><th class="p-2.5">Amount</th><th class="p-2.5">Status</th><th class="p-2.5 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="quotation-table-body" class="divide-y divide-custom text-custom-main"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- REPORTS TAB -->
            <div id="tab-reports" class="tab-content hidden space-y-8">
                <div>
                    <h1 class="text-2xl font-bold text-custom-main">Advanced Operational Reports Suite</h1>
                    <p class="text-sm text-custom-muted">Visual charts detailing Lead, Revenue, Conversion, and Employee Performance logs.</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main"><i class="fa-solid fa-magnet text-indigo-500"></i> Lead Funnels Pipeline Breakdown</h3>
                        <div class="w-full max-w-[260px] mx-auto relative"><canvas id="reportPieChart"></canvas></div>
                    </div>
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main"><i class="fa-solid fa-percent text-emerald-500"></i> Gross Conversion Velocity Rate</h3>
                        <div class="w-full max-w-[260px] mx-auto relative"><canvas id="reportDoughnutChart"></canvas></div>
                    </div>
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main"><i class="fa-solid fa-vault text-blue-500"></i> Realized Capital Revenue Pool</h3>
                        <div class="w-full h-48 relative"><canvas id="reportRevenueBarChart"></canvas></div>
                    </div>
                    <div class="panel-card p-6 rounded-2xl border shadow-sm">
                        <h3 class="font-bold text-base mb-6 text-center text-custom-main"><i class="fa-solid fa-people-group text-purple-500"></i> Employee Conversion Metrics</h3>
                        <div class="w-full h-48 relative"><canvas id="reportEmployeeChart"></canvas></div>
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
                <div>
                    <label class="block text-xs font-bold text-custom-muted mb-1.5">Assigned Employee/Agent</label>
                    <select id="lead_assigned_to" class="w-full input-custom border rounded-xl p-2.5 text-xs focus:outline-none">
                        <option value="Amit Singh">Amit Singh</option>
                        <option value="Pooja Raj">Pooja Raj</option>
                        <option value="Vikram Malhotra">Vikram Malhotra</option>
                    </select>
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
        let reportRevenueChartInstance = null;
        let reportEmployeeChartInstance = null;
        let currentLeadStatusCounts = { 'New': 0, 'Contacted': 0, 'Proposal': 0, 'Lost': 0 };
        let activeProfileCustomerId = null;

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
            if (target === 'sales_finance') loadSalesFinanceEngine();
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
            document.getElementById('stat-forecast-value').innerText = '₹' + parseFloat(stats.sales_forecast || 0).toLocaleString('en-IN', {maximumFractionDigits: 0});
            
            if(document.getElementById('conversion-win-rate')) {
                document.getElementById('conversion-win-rate').innerText = `Win Rate: ${stats.win_rate}%`;
            }

            currentLeadStatusCounts = stats.lead_status_counts || { 'New': 0, 'Contacted': 0, 'Proposal': 0, 'Lost': 0 };

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

                // Render Employee List
                let empBody = document.getElementById('employee-performance-body');
                empBody.innerHTML = '';
                stats.employees.forEach((emp, idx) => {
                    empBody.innerHTML += `
                    <tr>
                        <td class="p-3 font-semibold">${emp.name}</td>
                        <td class="p-3">${emp.deals_closed} Targets</td>
                        <td class="p-3 font-bold text-emerald-500">₹${parseFloat(emp.revenue_brought).toLocaleString('en-IN')}</td>
                        <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/15 text-indigo-500">Rank #${idx+1}</span></td>
                    </tr>`;
                });
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
            let empFilter = document.getElementById('leadFilterEmployee').value;
            let tbody = document.getElementById('leads-table-body');
            tbody.innerHTML = '';

            let targetList = rawLeads.filter(l => {
                let mq = l.name.toLowerCase().includes(query) || l.company.toLowerCase().includes(query);
                let mf = filter === 'All' || l.status === filter;
                let mv = true;
                if(valueTierFilter === 'High') mv = parseFloat(l.value || 0) >= 100000;
                if(valueTierFilter === 'Mid') mv = parseFloat(l.value || 0) < 100000;
                let me = empFilter === 'All' || l.assigned_to === empFilter;
                return mq && mf && mv && me;
            });

            if(targetList.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-gray-500 font-medium">No records found.</td></tr>`;
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
                    <td class="p-4 font-medium text-custom-muted">${l.assigned_to || 'Unassigned'}</td>
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
            document.getElementById('lead_assigned_to').value = lead.assigned_to || 'Amit Singh';
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
            fd.append('assigned_to', document.getElementById('lead_assigned_to').value);
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
                    <td class="p-4 text-right">
                        <button onclick='openCustomerProfilePane(${JSON.stringify(c)})' class="bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1 rounded text-[10px]">Open History Profile</button>
                    </td>
                </tr>`;
            });
        }

        function openCustomerProfilePane(customer) {
            activeProfileCustomerId = customer.id;
            document.getElementById('profile-pane-name').innerText = customer.name;
            document.getElementById('profile-pane-brand').innerText = customer.company || 'Individual Profile';
            document.getElementById('profile-pane-notes').value = customer.notes || '';
            
            // Render Chronology
            let histList = document.getElementById('profile-pane-history');
            histList.innerHTML = '';
            if(customer.history && customer.history.length > 0) {
                customer.history.forEach(h => {
                    histList.innerHTML += `<div class="p-1 border-b border-custom text-custom-main">• ${h}</div>`;
                });
            } else {
                histList.innerHTML = `<span class="text-gray-500 text-[10px]">No historical entries.</span>`;
            }

            // Render Purchases
            let purList = document.getElementById('profile-pane-purchases');
            purList.innerHTML = '';
            if(customer.purchases && customer.purchases.length > 0) {
                customer.purchases.forEach(p => {
                    purList.innerHTML += `<div class="flex justify-between font-medium"><span>${p.item}</span><span class="text-emerald-500 font-bold">₹${p.cost}</span></div>`;
                });
            } else {
                purList.innerHTML = `<span class="text-gray-500 text-[10px]">No recorded purchase history.</span>`;
            }

            // Render Document Links
            let docList = document.getElementById('profile-pane-docs');
            docList.innerHTML = '';
            if(customer.documents && customer.documents.length > 0) {
                customer.documents.forEach(d => {
                    docList.innerHTML += `<div class="flex items-center gap-1"><i class="fa-solid fa-file-pdf text-rose-500"></i> <span>${d}</span></div>`;
                });
            } else {
                docList.innerHTML = `<span class="text-gray-500 text-[10px]">No link documents embedded.</span>`;
            }

            document.getElementById('customer-profile-panel').classList.remove('hidden');
        }

        async function appendCustomerHistory() {
            let val = document.getElementById('new-history-entry').value;
            if(!val) return alert("Write historical summary.");
            let fd = new FormData();
            fd.append('id', activeProfileCustomerId);
            fd.append('history_entry', val);
            await fetchAPI('update_customer_profile', fd);
            document.getElementById('new-history-entry').value = '';
            popToast("History allocation log appended.");
            await loadCustomersEngine();
            refreshActiveProfilePane();
        }

        async function appendCustomerDoc() {
            let val = document.getElementById('new-doc-entry').value;
            if(!val) return alert("Write document text string context name.");
            let fd = new FormData();
            fd.append('id', activeProfileCustomerId);
            fd.append('doc_entry', val);
            await fetchAPI('update_customer_profile', fd);
            document.getElementById('new-doc-entry').value = '';
            popToast("Document profile linkage recorded.");
            await loadCustomersEngine();
            refreshActiveProfilePane();
        }

        async function saveCustomerNotes() {
            let val = document.getElementById('profile-pane-notes').value;
            let fd = new FormData();
            fd.append('id', activeProfileCustomerId);
            fd.append('notes', val);
            await fetchAPI('update_customer_profile', fd);
            popToast("Notes management parameters updated.");
            await loadCustomersEngine();
        }

        function refreshActiveProfilePane() {
            let target = rawCustomers.find(c => c.id === activeProfileCustomerId);
            if(target) openCustomerProfilePane(target);
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
                let typeBadgeColor = 'bg-gray-500/10 text-custom-muted';
                if(t.type === 'Follow-up') typeBadgeColor = 'bg-amber-500/10 text-amber-500';
                if(t.type === 'Call') typeBadgeColor = 'bg-emerald-500/10 text-emerald-500';
                if(t.type === 'Meeting') typeBadgeColor = 'bg-purple-500/10 text-purple-500';

                container.innerHTML += `
                <div class="flex items-center justify-between p-3 bg-gray-500/5 border border-custom rounded-xl ${isComp?'opacity-40 line-through':''}">
                    <div class="flex items-center gap-3">
                        <input type="checkbox" ${isComp?'checked':''} onclick="toggleTask(${t.id})" class="w-4 h-4 text-indigo-600 rounded focus:ring-0">
                        <div>
                            <p class="text-xs font-bold text-custom-main">${t.title}</p>
                            <div class="flex gap-2 items-center mt-1">
                                <span class="text-[9px] font-bold px-1.5 py-0.2 rounded ${typeBadgeColor}">${t.type || 'Task'}</span>
                                <span class="text-[10px] text-custom-muted">Due: ${t.due_date}</span>
                            </div>
                        </div>
                    </div>
                    <button onclick="deleteTask(${t.id})" class="text-gray-400 hover:text-rose-500 text-xs transition p-1"><i class="fa-solid fa-trash-can"></i></button>
                </div>`;
            });
        }

        async function handleTaskSubmit(e) {
            e.preventDefault();
            let fd = new FormData();
            fd.append('title', document.getElementById('task_title').value);
            fd.append('type', document.getElementById('task_type').value);
            fd.append('due_date', document.getElementById('task_due').value);
            fd.append('priority', document.getElementById('task_priority').value);
            await fetchAPI('save_task', fd); 
            document.getElementById('task-form').reset(); 
            loadTasksEngine();
            popToast("Objective Registered!");
        }

        async function toggleTask(id) { let fd = new FormData(); fd.append('id', id); await fetchAPI('toggle_task', fd); loadTasksEngine(); }
        async function deleteTask(id) { let fd = new FormData(); fd.append('id', id); await fetchAPI('delete_task', fd); loadTasksEngine(); }

        function syncToLocalCalendar() {
            if(rawTasks.length === 0) return alert("No operational strategic milestones found to export.");
            let icsContent = "BEGIN:VCALENDAR\\nVERSION:2.0\\nPRODID:-//OrbitEdge Media CRM//EN\\n";
            rawTasks.forEach(t => {
                let cleanDate = t.due_date.replace(/-/g, "");
                icsContent += "BEGIN:VEVENT\\n";
                icsContent += `SUMMARY:[${t.type || 'Task'}] ${t.title}\\n`;
                icsContent += `DTSTART:${cleanDate}T090000\\n`;
                icsContent += `DTEND:${cleanDate}T100000\\n`;
                icsContent += "DESCRIPTION:Automated Synchronization Rule from OrbitEdge CRM Platform Layout.\\n";
                icsContent += "END:VEVENT\\n";
            });
            icsContent += "END:VCALENDAR";
            let link = document.createElement("a");
            link.setAttribute("href", "data:text/calendar;charset=utf-8," + encodeURIComponent(icsContent));
            link.setAttribute("download", "OrbitEdge_CRM_Calendar_Matrix.ics");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            popToast("Calendar engine file package exported successfully!");
        }

        async function loadSalesFinanceEngine() {
            let res = await fetchAPI('get_financials');
            if(!res) return;
            
            let invBody = document.getElementById('invoice-table-body');
            let qtnBody = document.getElementById('quotation-table-body');
            invBody.innerHTML = ''; qtnBody.innerHTML = '';
            
            if(res.invoices.length === 0) invBody.innerHTML = `<tr><td colspan="5" class="p-3 text-center text-gray-500">No Invoices generated.</td></tr>`;
            res.invoices.forEach(inv => {
                let colorClass = inv.status === 'Paid' ? 'text-emerald-500 bg-emerald-500/10' : 'text-amber-500 bg-amber-500/10';
                invBody.innerHTML += `
                <tr class="hover:bg-gray-500/5 transition border-b border-custom">
                    <td class="p-2.5 font-bold">${inv.client_name}</td><td class="p-2.5 text-custom-muted">${inv.items}</td>
                    <td class="p-2.5 font-bold text-emerald-500">₹${inv.amount}</td>
                    <td class="p-2.5"><span class="text-[9px] px-2 py-0.5 rounded font-bold ${colorClass}">${inv.status}</span></td>
                    <td class="p-2.5 text-right space-x-1 whitespace-nowrap">
                        ${inv.status !== 'Paid' ? `<button onclick="updateDocStatus(${inv.id}, 'invoice', 'Paid')" class="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-600 font-bold px-2 py-0.5 rounded text-[10px] cursor-pointer">Mark Paid</button>`:''}
                        <button onclick="triggerPaymentReminder('${inv.client_name}', ${inv.amount})" class="bg-rose-500/20 hover:bg-rose-500/30 text-rose-600 font-bold px-2 py-0.5 rounded text-[10px] cursor-pointer"><i class="fa-solid fa-bell"></i> Remind</button>
                    </td>
                </tr>`;
            });

            if(res.quotations.length === 0) qtnBody.innerHTML = `<tr><td colspan="5" class="p-3 text-center text-gray-500">No Quotations compiled.</td></tr>`;
            res.quotations.forEach(qtn => {
                qtnBody.innerHTML += `
                <tr class="hover:bg-gray-500/5 transition border-b border-custom">
                    <td class="p-2.5 font-bold">${qtn.client_name}</td><td class="p-2.5 text-custom-muted">${qtn.items}</td>
                    <td class="p-2.5 font-bold text-indigo-500">₹${qtn.amount}</td>
                    <td class="p-2.5"><span class="text-[9px] px-2 py-0.5 rounded bg-gray-500/10 text-custom-muted font-bold">${qtn.status}</span></td>
                    <td class="p-2.5 text-right whitespace-nowrap">
                        <button onclick="updateDocStatus(${qtn.id}, 'quotation', 'Approved')" class="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-600 font-bold px-2 py-0.5 rounded text-[10px] cursor-pointer">Accept Proposal</button>
                    </td>
                </tr>`;
            });
        }

        async function handleDocSubmit(e) {
            e.preventDefault();
            let fd = new FormData();
            fd.append('doc_type', document.getElementById('doc_type').value);
            fd.append('client_name', document.getElementById('doc_client').value);
            fd.append('items', document.getElementById('doc_items').value);
            fd.append('amount', document.getElementById('doc_amount').value);
            
            await fetchAPI('save_document', fd);
            document.getElementById('doc-form').reset();
            loadSalesFinanceEngine();
            popToast("Financial Instrument Dispatched to Stack Ledger!");
        }

        async function updateDocStatus(id, docType, status) {
            let fd = new FormData();
            fd.append('id', id);
            fd.append('doc_type', docType);
            fd.append('status', status);
            await fetchAPI('update_doc_status', fd);
            loadSalesFinanceEngine();
            popToast("Status sync updated perfectly!");
        }

        function triggerPaymentReminder(client, amount) {
            let alertMsg = `Dear ${client}, this is an automated courtesy prompt regarding pending invoice balance payload of ₹${amount}. Kindly process the settlement channels.`;
            alert(`Payment Reminder Triggered:\\n\\n"${alertMsg}"`);
        }

        async function loadReportsEngine() {
            let stats = await fetchAPI('get_dashboard_stats');
            if(!stats) return;
            let ctxPie = document.getElementById('reportPieChart').getContext('2d');
            let ctxDoughnut = document.getElementById('reportDoughnutChart').getContext('2d');
            let ctxBar = document.getElementById('reportRevenueBarChart').getContext('2d');
            let ctxEmp = document.getElementById('reportEmployeeChart').getContext('2d');

            if (reportPieChartInstance) reportPieChartInstance.destroy();
            if (reportDoughnutChartInstance) reportDoughnutChartInstance.destroy();
            if (reportRevenueChartInstance) reportRevenueChartInstance.destroy();
            if (reportEmployeeChartInstance) reportEmployeeChartInstance.destroy();
            
            let isDark = document.body.classList.contains('dark-mode');
            let textTextColor = isDark ? '#9ca3af' : '#6b7280';
            let gridColorLine = isDark ? '#1f2937' : '#e5e7eb';

            let chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: textTextColor, font: { size: 10 } } } } };

            reportPieChartInstance = new Chart(ctxPie, {
                type: 'pie',
                data: { labels: Object.keys(stats.lead_status_counts || {}), datasets: [{ data: Object.values(stats.lead_status_counts || {}), backgroundColor: ['#6366f1', '#3b82f6', '#10b981', '#f43f5e'] }] },
                options: chartOptions
            });

            reportDoughnutChartInstance = new Chart(ctxDoughnut, {
                type: 'doughnut',
                data: { labels: ['Pipeline Closed', 'Leads Remaining'], datasets: [{ data: [stats.total_customers || 0, stats.total_leads || 0], backgroundColor: ['#10b981', '#6366f1'] }] },
                options: chartOptions
            });

            // Revenue Stream Realized Bar Chart
            reportRevenueChartInstance = new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: ['Realized Income', 'Pipeline Valuations', 'Forecasted Targets'],
                    datasets: [{
                        label: 'Capital Mapping Pool (₹)',
                        data: [stats.total_revenue_pool, stats.total_pipeline_value, stats.sales_forecast],
                        backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: textTextColor } },
                        y: { ticks: { color: textTextColor }, grid: { color: gridColorLine } }
                    }
                }
            });

            // Employee Analytics mapping chart
            let empNames = stats.employees.map(e => e.name);
            let empRev = stats.employees.map(e => e.revenue_brought);
            
            reportEmployeeChartInstance = new Chart(ctxEmp, {
                type: 'bar',
                data: {
                    labels: empNames,
                    datasets: [{
                        label: 'Gross Volume Brought (₹)',
                        data: empRev,
                        backgroundColor: '#f59e0b',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: textTextColor } },
                        y: { ticks: { color: textTextColor }, grid: { color: gridColorLine } }
                    }
                }
            });
        }
        
        function exportLeadsToCSV() {
            if (rawLeads.length === 0) return alert("No entries found!");
            let csv = "ID,Name,Company,Email,Phone,Status,Value\\n";
            rawLeads.forEach(l => { csv += `${l.id},"${l.name}","${l.company}",${l.email},${l.phone},${l.status},${l.value}\\n`; });
            let link = document.createElement("a"); link.setAttribute("href", encodeURI("data:text/csv;charset=utf-8," + csv));
            link.setAttribute("download", "CRM_Leads.csv"); document.body.appendChild(link); link.click(); document.body.removeChild(link);
        }

        async function exportFullCRMDataToExcel() {
            try {
                let stats = await fetchAPI('get_dashboard_stats') || {};
                let leads = await fetchAPI('get_leads') || [];
                let customers = await fetchAPI('get_customers') || [];
                let tasks = await fetchAPI('get_tasks') || [];

                let wb = XLSX.utils.book_new();

                let dashboardSummary = [
                    ["ORBITEDGE SYSTEM GENERAL OPERATIONAL SUMMARY", ""],
                    ["Metric Parameter Component", "Current Registered Value"],
                    ["Total Leads Captured", stats.total_leads || leads.length],
                    ["Active Customers Converted", stats.total_customers || customers.length],
                    ["Uncompleted Pipeline Objectives", stats.pending_tasks || 0],
                    ["Pipeline Valuation Pool", stats.total_pipeline_value || 0],
                    ["Average Active Deal Size Value", stats.average_deal_size || 0],
                    ["Aggregate Gross Revenue Pool", stats.total_revenue_pool || 0],
                    ["Conversion Velocity Rate", `${stats.win_rate || 0}%`],
                    ["Sales Weighted Forecast Pool", stats.sales_forecast || 0],
                    ["", ""],
                    ["PIPELINE BREAKDOWN (CHART COUNTS)", ""],
                    ["Lead Status Funnel Stage", "Total Counter Logged"],
                    ["New Leads Stage", currentLeadStatusCounts['New'] || 0],
                    ["Contacted Interactions", currentLeadStatusCounts['Contacted'] || 0],
                    ["Proposal Pitch Matrix", currentLeadStatusCounts['Proposal'] || 0],
                    ["Lost Leads Counter", currentLeadStatusCounts['Lost'] || 0]
                ];
                let wsSummary = XLSX.utils.aoa_to_sheet(dashboardSummary);
                XLSX.utils.book_append_sheet(wb, wsSummary, "Dashboard Analytics");

                let leadsData = [["Database ID", "Client Name", "Corporate Company Brand", "Email Address", "Mobile Number Contact", "Funnel Status Position", "Estimated Capital Deal Value", "Assigned Owner", "Date Created Log"]];
                leads.forEach(l => {
                    leadsData.push([l.id, l.name, l.company || "N/A", l.email, l.phone, l.status, l.value, l.assigned_to, l.date]);
                });
                let wsLeads = XLSX.utils.aoa_to_sheet(leadsData);
                XLSX.utils.book_append_sheet(wb, wsLeads, "Leads Pipeline");

                let customerData = [["Database ID", "Customer Entity Name", "Corporate Company Brand", "Email ID Address", "Mobile Contact Connection", "Revenue Pool Generated", "Acquisition Notes"]];
                customers.forEach(c => {
                    customerData.push([c.id, c.name, c.company || "N/A", c.email, c.phone, c.revenue, c.notes || '']);
                });
                let wsCustomers = XLSX.utils.aoa_to_sheet(customerData);
                XLSX.utils.book_append_sheet(wb, wsCustomers, "Active Customers Profiles");

                let tasksData = [["Task ID Reference", "Objective Strategic Title", "Type", "Target Calendar Deadline", "Priority Weight Status", "Operational State"]];
                tasks.forEach(t => {
                    tasksData.push([t.id, t.title, t.type || 'Task', t.due_date, t.priority, t.status]);
                });
                let wsTasks = XLSX.utils.aoa_to_sheet(tasksData);
                XLSX.utils.book_append_sheet(wb, wsTasks, "Operational Roadmap");

                XLSX.writeFile(wb, `OrbitEdge_Complete_CRM_Report_${new Date().toISOString().slice(0, 10)}.xlsx`);
                popToast("Excel Multi-Sheet compiled perfectly!");
            } catch (err) {
                console.error("Critical Excel Packaging Exception:", err);
                alert("Failed to export complete Excel report data layers.");
            }
        }

        async function exportFullCRMToPDF() {
            const mainContainer = document.getElementById('exportable-main-area');
            if (!mainContainer) return alert("System Anchor reference broken down.");
            
            popToast("Preparing High-Res Executive PDF document structure...");

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

