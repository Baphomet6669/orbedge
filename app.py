from flask import Flask, render_template_string, request, redirect, session, url_for
import os

# --- Blueprints Import ---
from script33 import script33_bp


app = Flask(__name__)
app.url_map.strict_slashes = False
app.secret_key = "PHANTOM_ULTRA_SECRET_KEY" # Session secure rakhne ke liye

# --- ⚙️ CREDENTIALS SETTING ---
ADMIN_USER = "media"
ADMIN_PASS = "@rbitedge789"

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
            <a href="/script33/" class="btn"> Seo Audit</a>
        </div>
    </body>
    </html>
    """

# --- Blueprints Register Karein ---
app.register_blueprint(script33_bp, url_prefix='/script33')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
