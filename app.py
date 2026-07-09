from flask import Flask, render_template_string, request, redirect, session, url_for
import os

# --- Blueprints Import ---
from script1 import script1_bp
from script2 import script2_bp
from script3 import script3_bp
from script4 import script4_bp
from script5 import script5_bp
from script6 import script6_bp
from script7 import script7_bp
from script8 import script8_bp
from script9 import script9_bp
from script10 import script10_bp
from script11 import script11_bp
from script12 import script12_bp
from script15 import script15_bp
from script16 import script16_bp
from script17 import script17_bp
from script18 import script18_bp
from script19 import script19_bp
from script20 import script20_bp
from script21 import script21_bp
from script22 import script22_bp
from script23 import script23_bp
from script24 import script24_bp
from script25 import script25_bp
from script26 import script26_bp
from script27 import script27_bp
from script28 import script28_bp
from script29 import script29_bp
from script30 import script30_bp
from script31 import script31_bp
from script32 import script32_bp
from script33 import script33_bp


app = Flask(__name__)
app.url_map.strict_slashes = False
app.secret_key = "PHANTOM_ULTRA_SECRET_KEY" # Session secure rakhne ke liye

# --- ⚙️ CREDENTIALS SETTING ---
ADMIN_USER = "shivam"
ADMIN_PASS = "@nishka"

# --- 🛡️ SECURITY MIDDLEWARE ---
@app.before_request
def check_login():
    # Login page, static files, aur active session ko allow karein
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'logged_in' not in session:
        return redirect(url_for('login'))

# --- 🔑 LOGIN PAGE ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = "ACCESS_DENIED: INVALID_CREDENTIALS"

    return f"""
    <html>
    <head>
        <title>PHANTOM_AUTH</title>
        <style>
            body {{ background: #000; color: #0f0; font-family: 'Courier New', monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-box {{ border: 1px solid #0f0; padding: 40px; background: #050505; box-shadow: 0 0 20px #0f0; text-align: center; }}
            input {{ display: block; width: 100%; margin: 10px 0; padding: 10px; background: #111; border: 1px solid #0f0; color: #0f0; }}
            button {{ background: #0f0; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; width: 100%; }}
            .error {{ color: #ff0000; font-size: 12px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>[ GATEWAY_AUTH ]</h2>
            {f'<div class="error">{error}</div>' if error else ''}
            <form method="POST">
                <input type="text" name="user" placeholder="USERNAME" required>
                <input type="password" name="pass" placeholder="PASSWORD" required>
                <button type="submit">DECRYPT_ACCESS</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Shivam Singh Dashboard</title>
        <style>
            body { background: #000; color: #00ff00; font-family: 'Courier New', monospace; text-align: center; padding: 40px; }
            .btn { background: transparent; border: 1px solid #00ff00; color: #00ff00; padding: 15px; width: 260px; 
                   margin: 10px; cursor: pointer; font-weight: bold; transition: 0.3s; text-decoration: none; display: inline-block; }
            .btn:hover { background: #00ff00; color: #000; box-shadow: 0 0 15px #00ff00; }
            h1 { text-shadow: 0 0 10px #00ff00; }
            .logout-link { color: #ff0000; text-decoration: none; font-size: 12px; position: absolute; top: 20px; right: 20px; }
        </style>
    </head>
    <body>
        <a href="/logout" class="logout-link">[ TERMINATE_SESSION ]</a>
        <h1>[ SHIVAM SINGH OMEGA DASHBOARD ]</h1>
        <div style="display: flex; flex-wrap: wrap; justify-content: center;">
            <a href="/script1/" class="btn">Open Analyzer</a>
            <a href="/script2/" class="btn">Open Scraper</a>
            <a href="/script3/" class="btn">EXE Converter</a>
            <a href="/script4/" class="btn">DDoS Lab</a>
            <a href="/script5/" class="btn">Ping Tool</a>
            <a href="/script6/" class="btn">Video Call</a>
            <a href="/script7/" class="btn">VoIP Call</a>
            <a href="/script8/" class="btn">Phone OSINT</a>
            <a href="/script9/" class="btn">Private Call</a>
            <a href="/script10/" class="btn">Spy Cam</a>
            <a href="/script11/" class="btn">Mail Spoofing</a>
            <a href="/script12/" class="btn">Nmap Scanner</a>
            <a href="/script15/" class="btn">Nu Attack</a>
            <a href="/script16/" class="btn">Vehicle Info</a>
            <a href="/script17/" class="btn">Message Vault</a>
            <a href="/script18/" class="btn" style="border-width: 2px;">FILE VAULT (PRIVATE)</a>
            <a href="/script19/" class="btn">Jarvis</a>
            <a href="/script20/" class="btn">Information</a>
            <a href="/script21/" class="btn">XSS</a>
            <a href="/script22/" class="btn">Phone infonit</a>
            <a href="/script23/" class="btn">Car Info</a>
            <a href="/script24/" class="btn">Mail Spoof</a>
            <a href="/script25/" class="btn">Mail Leak</a>
            <a href="/script26/" class="btn">Mac Lookup</a>
            <a href="/script27/" class="btn">Leads Finder</a>
            <a href="/script28/" class="btn"> IMEI Finder</a>
            <a href="/script29/" class="btn"> Ip Finder</a>
            <a href="/script30/" class="btn"> ADB </a>
            <a href="/script31/" class="btn"> Google Dorking </a>
            <a href="/script32/" class="btn"> WhatsApp</a>
            <a href="/script33/" class="btn"> Seo Audit</a>
        </div>
    </body>
    </html>
    """

# --- Blueprints Register Karein ---
app.register_blueprint(script1_bp, url_prefix='/script1')
app.register_blueprint(script2_bp, url_prefix='/script2')
app.register_blueprint(script3_bp, url_prefix='/script3')
app.register_blueprint(script4_bp, url_prefix='/script4')
app.register_blueprint(script5_bp, url_prefix='/script5')
app.register_blueprint(script6_bp, url_prefix='/script6')
app.register_blueprint(script7_bp, url_prefix='/script7')
app.register_blueprint(script8_bp, url_prefix='/script8')
app.register_blueprint(script9_bp, url_prefix='/script9')
app.register_blueprint(script10_bp, url_prefix='/script10')
app.register_blueprint(script11_bp, url_prefix='/script11')
app.register_blueprint(script12_bp, url_prefix='/script12')
app.register_blueprint(script15_bp, url_prefix='/script15')
app.register_blueprint(script16_bp, url_prefix='/script16')
app.register_blueprint(script17_bp, url_prefix='/script17')
app.register_blueprint(script18_bp, url_prefix='/script18')
app.register_blueprint(script19_bp, url_prefix='/script19')
app.register_blueprint(script20_bp, url_prefix='/script20')
app.register_blueprint(script21_bp, url_prefix='/script21')
app.register_blueprint(script22_bp, url_prefix='/script22')
app.register_blueprint(script23_bp, url_prefix='/script23')
app.register_blueprint(script24_bp, url_prefix='/script24')
app.register_blueprint(script25_bp, url_prefix='/script25')
app.register_blueprint(script26_bp, url_prefix='/script26')
app.register_blueprint(script27_bp, url_prefix='/script27')
app.register_blueprint(script28_bp, url_prefix='/script28')
app.register_blueprint(script29_bp, url_prefix='/script29')
app.register_blueprint(script30_bp, url_prefix='/script30')
app.register_blueprint(script31_bp, url_prefix='/script31')
app.register_blueprint(script32_bp, url_prefix='/script32')
app.register_blueprint(script33_bp, url_prefix='/script33')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
