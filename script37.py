import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import smtplib
import re
import dns.resolver
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# SCRIPT 37 ENGINE MODULES (VALIDATION, SPAM SCORE & ENGINE)
# =========================================================

class CoreEmailValidator:
    @staticmethod
    def is_syntax_valid(email: str) -> bool:
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email.strip()) is not None

    @staticmethod
    def check_mx_record(email: str) -> bool:
        try:
            domain = email.split('@')[-1]
            records = dns.resolver.resolve(domain, 'MX')
            return len(records) > 0
        except Exception:
            return False

class CoreSpamAuditor:
    SPAM_WORDS = ['free', 'click here', 'buy now', 'make money', 'earn cash', 
                  '100% free', 'guaranteed', 'urgent', 'winner', 'lottery', 
                  'get paid', 'act fast', 'limited time', 'risk-free']

    @classmethod
    def audit_content(cls, subject: str, body: str) -> dict:
        score = 0
        triggers = []
        content = (subject + " " + body).lower()

        for word in cls.SPAM_WORDS:
            if word in content:
                score += 2
                triggers.append(word)

        if subject.isupper() and len(subject) > 3:
            score += 3
            triggers.append("ALL CAPS SUBJECT")

        status = "Safe" if score < 4 else ("Risky" if score < 8 else "High Spam Risk")
        return {"score": score, "status": status, "triggers": triggers}

# =========================================================
# TKINTER APPLICATION (DESKTOP INTERFACE)
# =========================================================

class EnterpriseBulkEmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Script 37 | Enterprise Bulk Email Suite")
        self.root.geometry("680x780")
        self.root.config(bg="#0f172a")
        self.root.resizable(False, False)

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TProgressbar", thickness=15, troughcolor='#1e293b', background='#10b981')

        # Main Header
        header = tk.Label(root, text="⚡ Enterprise Email Broadcast Suite", font=("Segoe UI", 16, "bold"), bg="#0f172a", fg="#10b981")
        header.pack(pady=12)

        # 1. SMTP Pool Frame
        smtp_frame = tk.LabelFrame(root, text=" SMTP Config (Default: Gmail) ", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8", padx=10, pady=8)
        smtp_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(smtp_frame, text="Host & Port:", bg="#1e293b", fg="#cbd5e1").grid(row=0, column=0, sticky="w")
        self.host_entry = tk.Entry(smtp_frame, width=22, bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.host_entry.grid(row=0, column=1, padx=5, pady=3)
        self.host_entry.insert(0, "smtp.gmail.com")

        self.port_entry = tk.Entry(smtp_frame, width=8, bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.port_entry.grid(row=0, column=2, padx=5, pady=3)
        self.port_entry.insert(0, "587")

        tk.Label(smtp_frame, text="Sender Email:", bg="#1e293b", fg="#cbd5e1").grid(row=1, column=0, sticky="w")
        self.email_entry = tk.Entry(smtp_frame, width=32, bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.email_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=3)

        tk.Label(smtp_frame, text="App Password:", bg="#1e293b", fg="#cbd5e1").grid(row=2, column=0, sticky="w")
        self.pass_entry = tk.Entry(smtp_frame, width=32, show="*", bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.pass_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=3)

        # 2. Content & Recipient Frame
        content_frame = tk.LabelFrame(root, text=" Campaign Content ", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8", padx=10, pady=8)
        content_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(content_frame, text="Recipients (Comma Separated Emails):", bg="#1e293b", fg="#cbd5e1").pack(anchor="w")
        self.recipients_entry = tk.Entry(content_frame, width=75, bg="#0f172a", fg="#10b981", insertbackground="white")
        self.recipients_entry.pack(fill="x", pady=(0, 6))
        self.recipients_entry.insert(0, "user1@example.com, user2@example.com")

        tk.Label(content_frame, text="Subject Line:", bg="#1e293b", fg="#cbd5e1").pack(anchor="w")
        self.subject_entry = tk.Entry(content_frame, width=75, bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.subject_entry.pack(fill="x", pady=(0, 6))
        self.subject_entry.insert(0, "Important Update for {{email}}")

        tk.Label(content_frame, text="Body (Supports HTML & Dynamic Tags like {{email}}):", bg="#1e293b", fg="#cbd5e1").pack(anchor="w")
        self.body_text = scrolledtext.ScrolledText(content_frame, width=75, height=6, bg="#0f172a", fg="#ffffff", insertbackground="white")
        self.body_text.pack(fill="x")
        self.body_text.insert(tk.END, "<h2>Hello,</h2><p>This is an automated system transmission for <b>{{email}}</b>.</p>")

        # 3. Execution Terminal Log
        log_frame = tk.LabelFrame(root, text=" Live Engine Status & Logs ", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8", padx=10, pady=5)
        log_frame.pack(fill="x", padx=15, pady=5)

        self.log_terminal = scrolledtext.ScrolledText(log_frame, width=75, height=6, bg="#090d16", fg="#94a3b8", font=("Consolas", 8))
        self.log_terminal.pack(fill="x")

        # Progress Bar & Control
        self.progress = ttk.Progressbar(root, orient="horizontal", length=650, mode="determinate", style="TProgressbar")
        self.progress.pack(pady=8)

        self.status_label = tk.Label(root, text="Status: Ready", font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8")
        self.status_label.pack()

        self.send_btn = tk.Button(
            root, text="🚀 LAUNCH BROADCAST PIPELINE", font=("Segoe UI", 11, "bold"), 
            bg="#10b981", fg="#0f172a", activebackground="#059669", relief="flat", padx=10, pady=6, 
            command=self.start_sending_thread
        )
        self.send_btn.pack(pady=10)

    def log(self, message: str, color_prefix: str = "[LOG]"):
        self.log_terminal.insert(tk.END, f"{color_prefix} {message}\n")
        self.log_terminal.see(tk.END)

    def start_sending_thread(self):
        threading.Thread(target=self.execute_engine, daemon=True).start()

    def execute_engine(self):
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        sender_email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        recipients_raw = self.recipients_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()

        if not sender_email or not password or not recipients_raw or not subject or not body:
            messagebox.showwarning("Validation Error", "Sare required fields fill karein!")
            return

        # 1. Spam Audit Check
        spam_audit = CoreSpamAuditor.audit_content(subject, body)
        self.log(f"Spam Audit Rating: {spam_audit['score']}/14 ({spam_audit['status']})")
        if spam_audit['score'] >= 8:
            messagebox.showerror("Campaign Aborted", f"High Spam Risk! Triggers: {', '.join(spam_audit['triggers'])}")
            return

        recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
        total_emails = len(recipients)

        self.send_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = total_emails

        success_count = 0
        failed_count = 0

        try:
            self.status_label.config(text="Status: Authenticating SMTP Gateway...", fg="#3b82f6")
            self.log(f"Connecting to Gateway {host}:{port}...")

            server = smtplib.SMTP(host, int(port), timeout=12)
            server.starttls()
            server.login(sender_email, password)
            self.log("SMTP Authentication Verified Successfully!", "[OK]")

            for idx, to_email in enumerate(recipients, start=1):
                self.status_label.config(text=f"Processing: {to_email} ({idx}/{total_emails})", fg="#3b82f6")
                
                # Validation Logic
                if not CoreEmailValidator.is_syntax_valid(to_email):
                    self.log(f"Skipped {to_email} (Invalid Syntax)", "[FAIL]")
                    failed_count += 1
                    continue

                if not CoreEmailValidator.check_mx_record(to_email):
                    self.log(f"Skipped {to_email} (MX Lookup Failed)", "[FAIL]")
                    failed_count += 1
                    continue

                try:
                    # Parse dynamic tags
                    parsed_body = body.replace("{{email}}", to_email)
                    parsed_subject = subject.replace("{{email}}", to_email)

                    msg = MIMEMultipart('alternative')
                    msg['From'] = sender_email
                    msg['To'] = to_email
                    msg['Subject'] = parsed_subject
                    msg.attach(MIMEText(parsed_body, 'html'))

                    server.sendmail(sender_email, to_email, msg.as_string())
                    success_count += 1
                    self.log(f"Delivered to {to_email}", "[SUCCESS]")
                except Exception as send_err:
                    self.log(f"Delivery failed to {to_email}: {str(send_err)}", "[ERROR]")
                    failed_count += 1

                self.progress["value"] = idx
                self.root.update_idletasks()
                time.sleep(0.5)  # Rate control throttle

            server.quit()

            self.status_label.config(text=f"Completed! Success: {success_count} | Failed: {failed_count}", fg="#10b981")
            messagebox.showinfo("Execution Summary", f"Pipeline Dispatch Finished!\n\nDelivered: {success_count}\nFailed/Skipped: {failed_count}")

        except Exception as err:
            self.status_label.config(text="Status: Fatal System Error", fg="#ef4444")
            self.log(f"Fatal Connection Failure: {str(err)}", "[CRITICAL]")
            messagebox.showerror("SMTP Exception", f"Connection Failed: {str(err)}")

        finally:
            self.send_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnterpriseBulkEmailApp(root)
    root.mainloop()

