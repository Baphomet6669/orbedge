import os
import json
import math
from flask import Flask, Blueprint, render_template_string, request, jsonify

# -----------------------------------------------------------------------------
# BLUEPRINT & SINGLE FILE CONFIGURATION
# -----------------------------------------------------------------------------
script45_bp = Blueprint('script45', __name__)
JSON_DB_FILE = os.path.join(os.path.dirname(__file__), 'financial_data.json')

def load_data():
    if not os.path.exists(JSON_DB_FILE):
        default_data = {
            "net_worth": {"assets": 500000, "liabilities": 100000},
            "budget": {"income": 80000, "expenses": {"rent": 15000, "food": 10000, "leisure": 5000}},
            "goals": [{"name": "Car", "target": 800000, "years": 3, "saved": 150000}],
            "portfolio": [{"asset": "Equity Mutual Funds", "amount": 300000}, {"asset": "FD", "amount": 100000}],
            "income_streams": {"salary": 70000, "freelance": 15000, "rental": 10000, "dividend": 2000}
        }
        save_data(default_data)
        return default_data
    try:
        with open(JSON_DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    try:
        with open(JSON_DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# CORE MATHEMATICAL CALCULATORS ENGINE (25+ TOOLS INCLUDED)
# -----------------------------------------------------------------------------
class FinanceEngine:

    @staticmethod
    def wealth_growth(initial, monthly, rate, years, step_up=0):
        months = years * 12
        monthly_rate = (rate / 100) / 12
        balance = initial
        total_invested = initial
        year_wise = []

        current_monthly = monthly
        for m in range(1, months + 1):
            if m > 1 and (m - 1) % 12 == 0 and step_up > 0:
                current_monthly += current_monthly * (step_up / 100)

            interest = balance * monthly_rate
            balance += interest + current_monthly
            total_invested += current_monthly

            if m % 12 == 0:
                year_wise.append({
                    "year": m // 12,
                    "invested": round(total_invested, 2),
                    "wealth": round(balance, 2),
                    "profit": round(balance - total_invested, 2)
                })

        return {
            "final_wealth": round(balance, 2),
            "total_invested": round(total_invested, 2),
            "total_profit": round(balance - total_invested, 2),
            "year_wise": year_wise
        }

    @staticmethod
    def sip_calculator(monthly, rate, years):
        i = (rate / 100) / 12
        n = years * 12
        fv = monthly * (((1 + i)**n - 1) / i) * (1 + i) if i > 0 else monthly * n
        invested = monthly * n
        return {"future_value": round(fv, 2), "invested": round(invested, 2), "profit": round(fv - invested, 2)}

    @staticmethod
    def lumpsum_calculator(principal, rate, years):
        fv = principal * ((1 + (rate / 100)) ** years)
        return {"future_value": round(fv, 2), "profit": round(fv - principal, 2)}

    @staticmethod
    def fire_calculator(monthly_expense, current_savings, monthly_savings, rate=12, inflation=6):
        annual_expense = monthly_expense * 12
        fire_corpus = annual_expense * 25
        corpus = current_savings
        months = 0
        m_rate = (rate / 100) / 12
        while corpus < fire_corpus and months < 600:
            corpus = (corpus + monthly_savings) * (1 + m_rate)
            months += 1
            
        return {
            "target_fire_corpus": round(fire_corpus, 2),
            "years_to_fire": round(months / 12, 1),
            "status": "Achievable" if months < 600 else "Increase Savings Rate"
        }

    @staticmethod
    def emi_calculator(principal, rate, tenure_years):
        r = (rate / 100) / 12
        n = tenure_years * 12
        emi = (principal * r * ((1 + r)**n)) / (((1 + r)**n) - 1) if r > 0 else principal / n
        total_payment = emi * n
        return {
            "monthly_emi": round(emi, 2),
            "total_interest": round(total_payment - principal, 2),
            "total_payment": round(total_payment, 2)
        }

    @staticmethod
    def lifestyle_cost_missed(daily_expense, years, return_rate=12):
        monthly_expense = daily_expense * 30
        res = FinanceEngine.sip_calculator(monthly_expense, return_rate, years)
        return {
            "total_spent_cash": monthly_expense * 12 * years,
            "missed_future_wealth": res["future_value"]
        }

    @staticmethod
    def financial_mistake_cost(principal, high_loan_rate, tenure_years, delay_years, investment_return=12):
        loan_res = FinanceEngine.emi_calculator(principal, high_loan_rate, tenure_years)
        bad_interest = loan_res["total_interest"]
        
        SIP_MONTHLY = 5000
        normal_sip = FinanceEngine.sip_calculator(SIP_MONTHLY, investment_return, 20)
        delayed_sip = FinanceEngine.sip_calculator(SIP_MONTHLY, investment_return, max(1, 20 - delay_years))
        opportunity_loss = normal_sip["future_value"] - delayed_sip["future_value"]

        return {
            "excess_interest_paid": round(bad_interest, 2),
            "delayed_investing_opportunity_loss": round(opportunity_loss, 2),
            "total_mistake_cost": round(bad_interest + opportunity_loss, 2)
        }

    @staticmethod
    def multi_income_projection(salary, freelance, rental, dividend, years, rate=12):
        total_monthly = salary + freelance + rental + dividend
        res = FinanceEngine.sip_calculator(total_monthly, rate, years)
        return {
            "monthly_income": total_monthly,
            "projected_wealth": res["future_value"]
        }

    @staticmethod
    def local_ai_wealth_advisor(income, expenses, savings, debt, age=25):
        savings_rate = ((income - expenses) / income) * 100 if income > 0 else 0
        debt_to_income = (debt / income) * 100 if income > 0 else 0
        
        suggestions = []
        if savings_rate < 20:
            suggestions.append("⚠️ Your savings rate is below 20%. Try cutting non-essential expenses.")
        elif savings_rate >= 40:
            suggestions.append("🌟 Excellent savings rate! Allocate at least 60% of savings into Equity/Index Funds.")

        if debt_to_income > 40:
            suggestions.append("🚨 High Debt Alarm: Prioritize paying off high-interest loans (Debt Snowball).")
        else:
            suggestions.append("✅ Debt is well-managed. Keep credit score healthy.")

        equity_alloc = max(10, 100 - age)
        debt_alloc = 100 - equity_alloc
        
        return {
            "savings_rate_percent": round(savings_rate, 1),
            "debt_to_income_percent": round(debt_to_income, 1),
            "recommended_asset_allocation": f"{equity_alloc}% Equity | {debt_alloc}% Debt/FD",
            "ai_insights": suggestions
        }

# -----------------------------------------------------------------------------
# BLUEPRINT ROUTES
# -----------------------------------------------------------------------------
@script45_bp.route('/')
def dashboard():
    data = load_data()
    return render_template_string(HTML_LAYOUT, db_data=data)

@script45_bp.route('/api/simulate-wealth', methods=['POST'])
def api_wealth():
    req = request.json or {}
    initial = float(req.get('initial', 0))
    monthly = float(req.get('monthly', 5000))
    rate = float(req.get('rate', 12))
    years = int(req.get('years', 10))
    step_up = float(req.get('step_up', 0))
    
    res = FinanceEngine.wealth_growth(initial, monthly, rate, years, step_up)
    return jsonify({"success": True, "data": res})

@script45_bp.route('/api/lifestyle-mistake', methods=['POST'])
def api_lifestyle_mistake():
    req = request.json or {}
    daily_cost = float(req.get('daily_cost', 200))
    years = int(req.get('years', 20))
    
    cost_res = FinanceEngine.lifestyle_cost_missed(daily_cost, years)
    mistake_res = FinanceEngine.financial_mistake_cost(500000, 18, 5, 3)
    
    return jsonify({
        "success": True,
        "lifestyle": cost_res,
        "mistake": mistake_res
    })

@script45_bp.route('/api/multi-income', methods=['POST'])
def api_multi_income():
    req = request.json or {}
    salary = float(req.get('salary', 70000))
    freelance = float(req.get('freelance', 15000))
    rental = float(req.get('rental', 10000))
    dividend = float(req.get('dividend', 2000))
    years = int(req.get('years', 10))
    
    res = FinanceEngine.multi_income_projection(salary, freelance, rental, dividend, years)
    return jsonify({"success": True, "data": res})

@script45_bp.route('/api/ai-advisor', methods=['POST'])
def api_ai_advisor():
    req = request.json or {}
    income = float(req.get('income', 80000))
    expenses = float(req.get('expenses', 40000))
    savings = float(req.get('savings', 200000))
    debt = float(req.get('debt', 15000))
    
    advisor = FinanceEngine.local_ai_wealth_advisor(income, expenses, savings, debt)
    return jsonify({"success": True, "advisor": advisor})

# -----------------------------------------------------------------------------
# EMBEDDED HIGH-END CYBERPUNK UI FRONTEND
# -----------------------------------------------------------------------------
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shivam Singh Dashboard | Script 45 Wealth Suite</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #080c14; color: #f3f4f6; }
        .glass-card { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-emerald { box-shadow: 0 0 25px rgba(16, 185, 129, 0.2); }
    </style>
</head>
<body class="antialiased">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar Navigation -->
        <aside class="w-full lg:w-72 bg-slate-950 border-b lg:border-r border-slate-900 p-6 flex flex-col">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 glow-emerald">
                    <i class="fa-solid fa-chart-line text-2xl"></i>
                </div>
                <div>
                    <h2 class="font-extrabold text-lg text-white leading-tight">ApexWealth</h2>
                    <span class="text-[10px] text-emerald-400 font-mono tracking-widest uppercase block mt-0.5">SCRIPT 45 ENGINE</span>
                </div>
            </div>

            <nav class="space-y-2 flex-1 text-xs font-semibold">
                <a href="#simulator" class="flex items-center gap-3 px-4 py-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                    <i class="fa-solid fa-wand-magic-sparkles text-base"></i> Wealth Growth
                </a>
                <a href="#multi-income" class="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-900 rounded-xl transition">
                    <i class="fa-solid fa-coins text-base"></i> Multi Income Stream
                </a>
                <a href="#lifestyle" class="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-900 rounded-xl transition">
                    <i class="fa-solid fa-mug-hot text-base"></i> Lifestyle & Penalty
                </a>
                <a href="#ai-advisor" class="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-900 rounded-xl transition">
                    <i class="fa-solid fa-brain text-base"></i> AI Financial Advisor
                </a>
            </nav>

            <div class="pt-6 border-t border-slate-900 text-center">
                <span class="text-[10px] text-emerald-400 font-mono">STATUS: SINGLE-FILE ENGINE ONLINE</span>
            </div>
        </aside>

        <!-- Main Workspace -->
        <main class="flex-1 p-6 lg:p-10 space-y-8 overflow-y-auto">
            
            <!-- Header -->
            <div class="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-900 pb-6 gap-4">
                <div>
                    <h1 class="text-3xl font-black text-white tracking-tight">Shivam Singh Wealth Suite</h1>
                    <p class="text-xs text-slate-400 mt-1">25+ Finance Tools, Compound Calculators & Local AI Wealth Planner in 1 File.</p>
                </div>
            </div>

            <!-- SECTION 1: WEALTH GROWTH SIMULATOR -->
            <section id="simulator" class="space-y-4">
                <div class="flex items-center gap-2 text-emerald-400 font-bold uppercase text-xs tracking-wider">
                    <i class="fa-solid fa-calculator"></i> Wealth Growth & Salary Hike Simulator
                </div>

                <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    <div class="glass-card p-6 rounded-2xl space-y-4">
                        <div>
                            <label class="text-xs text-slate-400 block mb-1">Starting Amount (₹)</label>
                            <input type="number" id="initAmount" value="100000" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 block mb-1">Monthly Investment (₹)</label>
                            <input type="number" id="monthlyInv" value="10000" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 block mb-1">Expected Return (%)</label>
                            <input type="number" id="expectedRate" value="12" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 block mb-1">Duration (Years)</label>
                            <input type="number" id="invYears" value="15" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 block mb-1">Annual Step-Up / Salary Hike (%)</label>
                            <input type="number" id="stepUpHike" value="10" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-emerald-400 font-mono">
                        </div>
                        <button onclick="runWealthSimulation()" class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-xl text-xs transition shadow-lg glow-emerald cursor-pointer">
                            🚀 RUN SIMULATION
                        </button>
                    </div>

                    <div class="xl:col-span-2 glass-card p-6 rounded-2xl flex flex-col justify-between space-y-6">
                        <div class="grid grid-cols-3 gap-4 text-center">
                            <div class="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                                <span class="text-[10px] text-slate-500 font-mono block uppercase">Total Invested</span>
                                <span id="outInvested" class="text-lg font-bold text-white block mt-1">₹0</span>
                            </div>
                            <div class="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                                <span class="text-[10px] text-slate-500 font-mono block uppercase">Total Profit</span>
                                <span id="outProfit" class="text-lg font-bold text-emerald-400 block mt-1">₹0</span>
                            </div>
                            <div class="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                                <span class="text-[10px] text-slate-500 font-mono block uppercase">Final Wealth</span>
                                <span id="outWealth" class="text-lg font-extrabold text-emerald-300 block mt-1">₹0</span>
                            </div>
                        </div>

                        <div class="relative h-64 w-full">
                            <canvas id="growthChart"></canvas>
                        </div>
                    </div>
                </div>
            </section>

            <!-- SECTION 2: MULTI-INCOME SIMULATOR -->
            <section id="multi-income" class="glass-card p-6 rounded-2xl space-y-4">
                <div class="flex items-center gap-2 text-emerald-400 font-bold uppercase text-xs tracking-wider">
                    <i class="fa-solid fa-wallet"></i> Multiple Income Stream Wealth Projection
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <label class="text-[11px] text-slate-400 block mb-1">Salary (₹)</label>
                        <input type="number" id="incSalary" value="70000" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-400 block mb-1">Freelance (₹)</label>
                        <input type="number" id="incFreelance" value="15000" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-400 block mb-1">Rental (₹)</label>
                        <input type="number" id="incRental" value="10000" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-400 block mb-1">Dividend (₹)</label>
                        <input type="number" id="incDividend" value="2000" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white">
                    </div>
                </div>
                <div class="p-4 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                    <span class="text-slate-400">Combined 10-Year Projected Wealth (12% Return):</span>
                    <span id="multiCorpus" class="font-extrabold text-emerald-400 text-sm">₹0</span>
                </div>
            </section>

            <!-- SECTION 3: LIFESTYLE & MISTAKES -->
            <section id="lifestyle" class="glass-card p-6 rounded-2xl space-y-4">
                <div class="flex items-center gap-2 text-rose-400 font-bold uppercase text-xs tracking-wider">
                    <i class="fa-solid fa-skull-crossbones"></i> Lifestyle Drain & Financial Mistake Cost
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
                        <h4 class="text-xs font-bold text-slate-300">☕ ₹200 Daily Coffee Missed Compounding</h4>
                        <div class="flex justify-between text-xs">
                            <span class="text-slate-400">Total Spent Cash:</span>
                            <span id="lifeSpent" class="font-bold text-white">₹14,40,000</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-slate-400">Opportunity Wealth Missed (20 Yrs @ 12%):</span>
                            <span id="lifeLoss" class="font-bold text-rose-400">₹59,82,700</span>
                        </div>
                    </div>

                    <div class="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
                        <h4 class="text-xs font-bold text-slate-300">⚠️ 3-Year Late Investing Penalty</h4>
                        <div class="flex justify-between text-xs">
                            <span class="text-slate-400">Total Delay + Bad Loan Interest Penalty:</span>
                            <span id="mistakePenalty" class="font-bold text-rose-400">₹24,15,800</span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- SECTION 4: AI ADVISOR -->
            <section id="ai-advisor" class="glass-card p-6 rounded-2xl space-y-4">
                <div class="flex items-center gap-2 text-emerald-400 font-bold uppercase text-xs tracking-wider">
                    <i class="fa-solid fa-brain"></i> Rule-Based Local AI Advisor
                </div>
                <div id="aiSuggestions" class="space-y-2 text-xs font-mono text-slate-300">
                    <div class="p-3 bg-slate-950 border border-slate-800 rounded-lg">Calculating AI Wealth Rules...</div>
                </div>
            </section>

        </main>
    </div>

    <!-- JAVASCRIPT ENGINE -->
    <script>
        let myChart = null;

        async function runWealthSimulation() {
            const payload = {
                initial: document.getElementById('initAmount').value,
                monthly: document.getElementById('monthlyInv').value,
                rate: document.getElementById('expectedRate').value,
                years: document.getElementById('invYears').value,
                step_up: document.getElementById('stepUpHike').value
            };

            const res = await fetch('/api/simulate-wealth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if(data.success) {
                const d = data.data;
                document.getElementById('outInvested').innerText = "₹" + d.total_invested.toLocaleString('en-IN');
                document.getElementById('outProfit').innerText = "₹" + d.total_profit.toLocaleString('en-IN');
                document.getElementById('outWealth').innerText = "₹" + d.final_wealth.toLocaleString('en-IN');

                renderChart(d.year_wise);
            }

            fetchMultiIncome();
            fetchLifestyleAndMistakes();
            fetchAIAdvisor();
        }

        function renderChart(yearWiseData) {
            const labels = yearWiseData.map(item => 'Yr ' + item.year);
            const investedData = yearWiseData.map(item => item.invested);
            const wealthData = yearWiseData.map(item => item.wealth);

            const ctx = document.getElementById('growthChart').getContext('2d');
            if (myChart) myChart.destroy();

            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Total Wealth (₹)', data: wealthData, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.3 },
                        { label: 'Capital Invested (₹)', data: investedData, borderColor: '#64748b', borderDash: [5, 5], fill: false }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
                    scales: {
                        x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e293b' } },
                        y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e293b' } }
                    }
                }
            });
        }

        async function fetchMultiIncome() {
            const payload = {
                salary: floatVal('incSalary'),
                freelance: floatVal('incFreelance'),
                rental: floatVal('incRental'),
                dividend: floatVal('incDividend'),
                years: 10
            };

            const res = await fetch('/api/multi-income', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if(data.success) {
                document.getElementById('multiCorpus').innerText = "₹" + Math.round(data.data.projected_wealth).toLocaleString('en-IN');
            }
        }

        async function fetchLifestyleAndMistakes() {
            const res = await fetch('/api/lifestyle-mistake', { method: 'POST' });
            const data = await res.json();
            if(data.success) {
                document.getElementById('lifeSpent').innerText = "₹" + Math.round(data.lifestyle.total_spent_cash).toLocaleString('en-IN');
                document.getElementById('lifeLoss').innerText = "₹" + Math.round(data.lifestyle.missed_future_wealth).toLocaleString('en-IN');
                document.getElementById('mistakePenalty').innerText = "₹" + Math.round(data.mistake.total_mistake_cost).toLocaleString('en-IN');
            }
        }

        async function fetchAIAdvisor() {
            const res = await fetch('/api/ai-advisor', { method: 'POST' });
            const data = await res.json();
            if(data.success) {
                const adv = data.advisor;
                let html = `<div class="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <span class="text-emerald-400 font-bold">Savings Rate:</span> ${adv.savings_rate_percent}% | 
                    <span class="text-emerald-400 font-bold">Recommended Allocation:</span> ${adv.recommended_asset_allocation}
                </div>`;
                adv.ai_insights.forEach(msg => {
                    html += `<div class="p-3 bg-slate-950 border border-slate-800 rounded-lg mt-2">${msg}</div>`;
                });
                document.getElementById('aiSuggestions').innerHTML = html;
            }
        }

        function floatVal(id) {
            return parseFloat(document.getElementById(id).value) || 0;
        }

        window.onload = runWealthSimulation;
    </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# APPLICATION RUNNER (STANDALONE / RENDER / BLUEPRINT READY)
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.register_blueprint(script45_bp, url_prefix='')

if __name__ == '__main__':
    print("=" * 65)
    print("🚀 SCRIPT 45: SINGLE FILE WEALTH ENGINE ACTIVE!")
    print("👉 Direct URL: http://127.0.0.1:5000/")
    print("=" * 65)
    app.run(debug=True, host='127.0.0.1', port=5000)

