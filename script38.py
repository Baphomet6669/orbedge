import os
import json
from flask import Blueprint, render_template_string, request, jsonify

# 1. DEFINE THE BLUEPRINT FOR CORE ROUTER
script38_bp = Blueprint('script38', __name__, static_folder='static')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Delta Capital Suite')

# Comprehensive Financial Ratios Dictionary containing A-Z Data Structures
RATIO_DATABASE = {
    "pe_ratio": {
        "name": "Price-to-Earnings (P/E) Ratio",
        "category": "Valuation Ratios",
        "explanation": "P/E ratio batata hai ki company ke ₹1 kamane ke liye investors kitna paisa dene ko tayar hain. Agar P/E industry average se bohot zyada hai, toh stock overvalued ho sakta hai, aur agar kam hai toh undervalued.",
        "formula": "$$\\text{P/E Ratio} = \\frac{\\text{Market Price Per Share}}{\\text{Earnings Per Share (EPS)}}$$",
        "example": "Maan lo Reliance ka share price ₹2,500 hai aur uska EPS ₹100 hai. Toh P/E Ratio = 2500 / 100 = 25. Yaani aap ₹1 ki earning ke liye ₹25 pay kar rahe ho.",
        "inputs": [
            {"id": "pe_price", "label": "Market Price per Share (₹)", "placeholder": "e.g. 2500"},
            {"id": "pe_eps", "label": "Earnings Per Share / EPS (₹)", "placeholder": "e.g. 100"}
        ],
        "calc_script": "return (v.pe_price / v.pe_eps).toFixed(2) + 'x';"
    },
    "pb_ratio": {
        "name": "Price-to-Book (P/B) Ratio",
        "category": "Valuation Ratios",
        "explanation": "P/B ratio yeh compare karta hai ki company ki market value uski actual book value (assets minus liabilities) se kitni zyada hai. Banking aur manufacturing stocks ke liye yeh bohot important ratio hai.",
        "formula": "$$\\text{P/B Ratio} = \\frac{\\text{Market Price Per Share}}{\\text{Book Value Per Share (BVPS)}}$$",
        "example": "Agar kisi bank ka share price ₹500 hai aur uski book value ₹250 hai, toh P/B ratio 500 / 250 = 2.0 hoga.",
        "inputs": [
            {"id": "pb_price", "label": "Market Price per Share (₹)", "placeholder": "e.g. 500"},
            {"id": "pb_bvps", "label": "Book Value per Share (₹)", "placeholder": "e.g. 250"}
        ],
        "calc_script": "return (v.pb_price / v.pb_bvps).toFixed(2) + 'x';"
    },
    "roe": {
        "name": "Return on Equity (ROE)",
        "category": "Profitability Ratios",
        "explanation": "ROE yeh batata hai ki company shareholders ke paise (Equity) par kitna percent profit generate kar pa rahi hai. 15% se upar ka ROE generally achha maana jaata hai.",
        "formula": "$$\\text{ROE (\\%)} = \\left( \\frac{\\text{Net Income}}{\\text{Shareholders' Equity}} \\right) \\times 100$$",
        "example": "Company ne ₹15 Crore ka net profit kamaya, aur shareholders ki total equity ₹100 Crore thi. Toh ROE = (15 / 100) * 100 = 15%.",
        "inputs": [
            {"id": "roe_income", "label": "Net Income (₹ in Crores)", "placeholder": "e.g. 15"},
            {"id": "roe_equity", "label": "Shareholders' Equity (₹ in Crores)", "placeholder": "e.g. 100"}
        ],
        "calc_script": "return ((v.roe_income / v.roe_equity) * 100).toFixed(2) + '%';"
    },
    "roce": {
        "name": "Return on Capital Employed (ROCE)",
        "category": "Profitability Ratios",
        "explanation": "ROCE batata hai ki company apne total capital (Equity + Debt/Karza) par kitna return generate kar rahi hai. Capital-heavy companies ke liye yeh ROE se zyada accurate picture deta hai.",
        "formula": "$$\\text{ROCE (\\%)} = \\left( \\frac{\\text{EBIT}}{\\text{Total Capital Employed}} \\right) \\times 100$$",
        "example": "Company ka Operating Profit (EBIT) ₹20 Crore hai, total capital employed ₹100 Crore hai. ROCE = (20 / 100) * 100 = 20%.",
        "inputs": [
            {"id": "roce_ebit", "label": "EBIT / Operating Profit (₹ in Crores)", "placeholder": "e.g. 20"},
            {"id": "roce_capital", "label": "Capital Employed (Assets - Current Liab.)", "placeholder": "e.g. 100"}
        ],
        "calc_script": "return ((v.roce_ebit / v.roce_capital) * 100).toFixed(2) + '%';"
    },
    "debt_equity": {
        "name": "Debt-to-Equity Ratio",
        "category": "Leverage / Debt Ratios",
        "explanation": "Yeh ratio batata hai ki company par equity ke mukable kitna karza (debt) hai. Generally, Debt-to-Equity ratio 1 se kam hona chahiye. Agar yeh zyada hai, toh company risky ho sakti hai.",
        "formula": "$$\\text{Debt to Equity} = \\frac{\\text{Total Debt (Liabilities)}}{\\text{Total Shareholders' Equity}}$$",
        "example": "Company ke paas ₹40 Crore ka total debt hai aur ₹80 Crore ki equity hai. Debt-to-Equity = 40 / 80 = 0.5 (Safe zone).",
        "inputs": [
            {"id": "de_debt", "label": "Total Debt (₹ in Crores)", "placeholder": "e.g. 40"},
            {"id": "de_equity", "label": "Total Equity (₹ in Crores)", "placeholder": "e.g. 80"}
        ],
        "calc_script": "return (v.de_debt / v.de_equity).toFixed(2);"
    },
    "current_ratio": {
        "name": "Current Ratio",
        "category": "Liquidity Ratios",
        "explanation": "Current Ratio batata hai ki kya company ke paas agle 1 saal mein aane wali short-term liabilities ko chukane ke liye kaafi current assets hain ya nahi. Ideal ratio 2:1 maana jaata hai.",
        "formula": "$$\\text{Current Ratio} = \\frac{\\text{Current Assets}}{\\text{Current Liabilities}}$$",
        "example": "Company ke pass short-term assets ₹200 Crore hain aur short-term liabilities ₹100 Crore hain. Current Ratio = 200 / 100 = 2.0.",
        "inputs": [
            {"id": "curr_assets", "label": "Total Current Assets (₹)", "placeholder": "e.g. 200"},
            {"id": "curr_liab", "label": "Total Current Liabilities (₹)", "placeholder": "e.g. 100"}
        ],
        "calc_script": "return (v.curr_assets / v.curr_liab).toFixed(2);"
    }
}

@script38_bp.route('/')
def index():
    # Pass structural payload to the template renderer
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME, database=RATIO_DATABASE)

@script38_bp.route('/api/ratio-data', methods=['GET'])
def get_ratio_data():
    return jsonify(RATIO_DATABASE)

# DYNAMIC CYBERPUNK FIN-TECH ENGINE INTERFACE
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Fundamental Analytics Terminal</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- MathJax for rendering ultra professional academic equations -->
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        body { 
            font-family: 'Space Grotesk', sans-serif; 
            background-color: #060913; 
            color: #f1f5f9;
        }
        .fin-card {
            background: #0b132b;
            border: 1px solid #1c2541;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        }
        .glow-cyan {
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
        }
        .ratio-btn.active {
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
            color: #060913;
            font-weight: 700;
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
        }
    </style>
</head>
<body class="antialiased selection:bg-cyan-500 selection:text-slate-900">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar Navigation -->
        <aside class="w-full lg:w-80 bg-slate-950 flex flex-col border-b lg:border-r border-slate-900 p-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-xl shadow-lg glow-cyan">
                    <i class="fa-solid fa-chart-pie text-xl text-slate-950"></i>
                </div>
                <div>
                    <h2 class="font-bold text-lg tracking-tight text-white leading-none">QuantumRatio</h2>
                    <span class="text-[10px] text-cyan-400 font-mono uppercase tracking-widest mt-1 block">A-Z RATIO ENGINE v38</span>
                </div>
            </div>
            
            <div class="space-y-6 flex-1 overflow-y-auto pr-1">
                <div>
                    <span class="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-2">Available Ratios Matrix</span>
                    <div class="space-y-2" id="ratioMenu">
                        {% for key, item in database.items() %}
                        <button onclick="selectRatio('{{ key }}')" id="btn-{{ key }}" class="ratio-btn w-full text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-4 py-3 rounded-xl text-xs transition flex justify-between items-center cursor-pointer">
                            <span>{{ item.name }}</span>
                            <i class="fa-solid fa-chevron-right text-[10px] opacity-60"></i>
                        </button>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="pt-4 border-t border-slate-900 text-center">
                <span class="text-[10px] text-slate-500 font-mono">Status: Quant Framework Operational</span>
            </div>
        </aside>

        <!-- Main Display Deck -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-900 pb-6 mb-8">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white">{{ company }}</h1>
                    <p class="text-sm text-slate-400 mt-1">Advanced A-Z Fundamental Analysis Engine & Mathematical Simulation Terminal</p>
                </div>
            </div>

            <!-- Welcome Placeholder State -->
            <div id="welcomeState" class="fin-card p-12 rounded-2xl text-center border border-slate-800 max-w-2xl mx-auto my-12">
                <i class="fa-solid fa-circle-nodes text-5xl text-cyan-500 mb-4 animate-pulse"></i>
                <h3 class="text-xl font-bold text-white mb-2">Fundamental Analytics Active</h3>
                <p class="text-xs text-slate-400 leading-relaxed">Left sidebar me se kisi bhi Advanced Fundamental Ratio par click karein. Uski complete explanation, formula matrices, production examples, aur instant live calculator right screen par fetch ho jayenge.</p>
            </div>

            <!-- Active Workbench View Container -->
            <div id="workbench" class="hidden grid grid-cols-1 xl:grid-cols-12 gap-8">
                <!-- Ratio Insights -->
                <div class="xl:col-span-7 space-y-6">
                    <div class="fin-card p-6 rounded-2xl space-y-4">
                        <div class="flex justify-between items-start">
                            <div>
                                <span id="ratioCategory" class="text-[10px] bg-cyan-950 text-cyan-400 font-mono px-2 py-1 rounded border border-cyan-800 uppercase tracking-widest">VALUATION</span>
                                <h2 id="ratioTitle" class="text-2xl font-bold text-white mt-2">Ratio Title Placeholder</h2>
                            </div>
                        </div>
                        
                        <hr class="border-slate-800">
                        
                        <div>
                            <h4 class="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2"><i class="fa-solid fa-book-open text-cyan-400 mr-1"></i> Core Explanation (Hindi / English Mixed)</h4>
                            <p id="ratioDesc" class="text-xs text-slate-300 leading-relaxed bg-slate-950 p-4 rounded-xl border border-slate-900"></p>
                        </div>

                        <div>
                            <h4 class="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2"><i class="fa-solid fa-square-root-variable text-cyan-400 mr-1"></i> Mathematical Formula Architecture</h4>
                            <div id="ratioFormula" class="bg-slate-950 p-4 rounded-xl border border-slate-900 text-center text-cyan-300 text-sm overflow-x-auto">
                                <!-- Formula targets are injected inside this wrapper -->
                            </div>
                        </div>

                        <div>
                            <h4 class="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2"><i class="fa-solid fa-lightbulb text-cyan-400 mr-1"></i> Production Market Example</h4>
                            <p id="ratioExample" class="text-xs text-slate-400 leading-relaxed bg-slate-900/40 p-4 rounded-xl border border-slate-800 border-l-2 border-l-cyan-500 italic"></p>
                        </div>
                    </div>
                </div>

                <!-- Calculator Dashboard -->
                <div class="xl:col-span-5">
                    <div class="fin-card p-6 rounded-2xl space-y-4 sticky top-6">
                        <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 mb-2">
                            <i class="fa-solid fa-calculator text-cyan-400"></i> Real-time Quant Calculator
                        </h3>
                        
                        <div id="calcInputsContainer" class="space-y-4">
                            <!-- Injected inputs dynamic array -->
                        </div>

                        <div class="bg-slate-950 border border-slate-900 rounded-xl p-5 mt-6 text-center shadow-inner">
                            <span class="text-[10px] font-mono uppercase text-slate-500 block tracking-widest">Computed Quant Output</span>
                            <span id="calcOutputValue" class="text-3xl font-black text-cyan-400 tracking-tight block mt-2">0.00</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let ratioDb = {};

        // Async fetch initial data payload object
        async function loadDatabase() {
            try {
                const res = await fetch('./api/ratio-data');
                ratioDb = await res.json();
            } catch (e) {
                console.error("Database tracking fault initialized", e);
            }
        }

        function selectRatio(key) {
            // UI States optimization
            document.getElementById('welcomeState').classList.add('hidden');
            document.getElementById('workbench').classList.remove('hidden');

            // Reset selection highlights classes
            document.querySelectorAll('.ratio-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('btn-' + key).classList.add('active');

            const item = ratioDb[key];
            if(!item) return;

            // Injections
            document.getElementById('ratioCategory').innerText = item.category;
            document.getElementById('ratioTitle').innerText = item.name;
            document.getElementById('ratioDesc').innerText = item.explanation;
            
            // Formula rendering injection safe framework
            const formulaDiv = document.getElementById('ratioFormula');
            formulaDiv.innerHTML = item.formula;
            
            // Explicitly prompt MathJax to re-parse the newly loaded LaTeX DOM
            if (window.MathJax) {
                MathJax.typesetPromise([formulaDiv]);
            }

            document.getElementById('ratioExample').innerText = item.example;

            // Build dynamic input matrices fields inside dashboard array
            const inputContainer = document.getElementById('calcInputsContainer');
            inputContainer.innerHTML = '';

            item.inputs.forEach(input => {
                const wrapper = document.createElement('div');
                wrapper.innerHTML = `
                    <label class="text-xs text-slate-400 font-mono mb-1 block">\${input.label}</label>
                    <input type="number" id="\${input.id}" placeholder="\${input.placeholder}" oninput="executeRatioCalculation('\${key}')" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-500">
                `;
                inputContainer.appendChild(wrapper);
            });

            // Reset score metrics
            document.getElementById('calcOutputValue').innerText = '---';
        }

        function executeRatioCalculation(key) {
            const item = ratioDb[key];
            if(!item) return;

            let v = {};
            let allFilled = true;

            // Gather elements variable state values safely
            item.inputs.forEach(input => {
                const el = document.getElementById(input.id);
                const val = parseFloat(el.value);
                if(isNaN(val) || val <= 0) {
                    allFilled = false;
                }
                v[input.id] = val;
            });

            const outputDisplay = document.getElementById('calcOutputValue');

            if(!allFilled) {
                outputDisplay.innerText = '---';
                return;
            }

            try {
                // Dynamically evaluate calculation strategy engine execution safely
                const calculationFunction = new Function('v', item.calc_script);
                const result = calculationFunction(v);
                outputDisplay.innerText = result;
            } catch (err) {
                outputDisplay.innerText = 'Error';
            }
        }

        // Initialize engine lifecycle hook
        window.addEventListener('DOMContentLoaded', () => {
            loadDatabase();
        });
    </script>
</body>
</html>
"""

