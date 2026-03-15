# """
# FlutterMail — Full-stack email automation for job applications.
# Flask backend with Gmail SMTP, scheduling, bulk send, resume attachment.
# """

# import os
# import json
# import smtplib
# import ssl
# import threading
# import uuid
# from datetime import datetime, timedelta
# from pathlib import Path
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.application import MIMEApplication
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# from apscheduler.schedulers.background import BackgroundScheduler

# app = Flask(__name__, static_folder="static", template_folder="templates")
# CORS(app)
# app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max upload

# # ─── Data storage (JSON files — works on free tiers) ───
# DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
# DATA_DIR.mkdir(exist_ok=True)
# UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
# UPLOAD_DIR.mkdir(exist_ok=True)

# # ─── Scheduler for timed sends ───
# scheduler = BackgroundScheduler()
# scheduler.start()


# # ════════════════════════════════════════════
# #  DATA HELPERS
# # ════════════════════════════════════════════

# def load_data(filename, default=None):
#     path = DATA_DIR / filename
#     if path.exists():
#         with open(path, "r") as f:
#             return json.load(f)
#     return default if default is not None else {}

# def save_data(filename, data):
#     with open(DATA_DIR / filename, "w") as f:
#         json.dump(data, f, indent=2, default=str)

# def get_contacts():
#     return load_data("contacts.json", [])

# def save_contacts(contacts):
#     save_data("contacts.json", contacts)

# def get_template():
#     return load_data("template.json", {
#         "subject": "Application for {{role}} Position - {{your_name}}",
#         "body": "Dear {{greeting}},\n\nI hope this email finds you well. I am writing to express my strong interest in the {{role}} position at {{company}}.\n\nWith my experience in Flutter development, including expertise in Dart, state management (BLoC/Provider/Riverpod), REST API integration, and building responsive cross-platform applications, I am confident I can contribute meaningfully to your team.\n\nKey highlights of my background:\n• Proficient in Flutter & Dart with hands-on experience building production apps\n• Strong understanding of state management patterns and clean architecture\n• Experience with Firebase, REST APIs, and third-party integrations\n• Familiar with CI/CD pipelines and agile development practices\n\nI have attached my resume for your review. I would welcome the opportunity to discuss how my skills align with your team's needs.\n\nThank you for your time and consideration. I look forward to hearing from you.\n\nBest regards,\n{{your_name}}\n{{your_phone}}\n{{your_linkedin}}"
#     })

# def save_template(template):
#     save_data("template.json", template)

# def get_user_info():
#     return load_data("user_info.json", {
#         "your_name": "",
#         "your_phone": "",
#         "your_linkedin": "",
#         "gmail_address": "",
#         "gmail_app_password": ""
#     })

# def save_user_info(info):
#     save_data("user_info.json", info)

# def get_send_log():
#     return load_data("send_log.json", [])

# def add_log_entry(entry):
#     log = get_send_log()
#     log.append({**entry, "timestamp": datetime.now().isoformat()})
#     save_data("send_log.json", log)


# # ════════════════════════════════════════════
# #  EMAIL ENGINE
# # ════════════════════════════════════════════

# def fill_template(template_str, variables):
#     """Replace {{placeholder}} with values. Auto-generates {{greeting}}."""
#     hr_name = variables.get("hr_name", "").strip()
#     greeting = hr_name if hr_name else "Hiring Manager"
#     all_vars = {**variables, "greeting": greeting}
#     result = template_str
#     for key, value in all_vars.items():
#         result = result.replace(f"{{{{{key}}}}}", str(value))
#     return result


# def send_single_email(to_email, subject, body, user_info, attach_resume=True):
#     """Send one email via Gmail SMTP."""
#     sender = user_info.get("gmail_address", "")
#     password = user_info.get("gmail_app_password", "")

#     if not sender or not password:
#         return {"success": False, "error": "Gmail credentials not configured"}

#     msg = MIMEMultipart()
#     msg["From"] = sender
#     msg["To"] = to_email
#     msg["Subject"] = subject
#     msg.attach(MIMEText(body, "plain"))

#     # Attach resume if available
#     if attach_resume:
#         resume_files = list(UPLOAD_DIR.glob("resume.*"))
#         if resume_files:
#             resume_path = resume_files[0]
#             with open(resume_path, "rb") as f:
#                 attachment = MIMEApplication(f.read(), _subtype="pdf")
#                 attachment.add_header(
#                     "Content-Disposition", "attachment",
#                     filename=resume_path.name
#                 )
#                 msg.attach(attachment)

#     try:
#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
#             server.login(sender, password)
#             server.sendmail(sender, to_email, msg.as_string())
#         return {"success": True}
#     except smtplib.SMTPAuthenticationError:
#         return {"success": False, "error": "Authentication failed. Check your Gmail App Password."}
#     except Exception as e:
#         return {"success": False, "error": str(e)}


# def send_to_contact(contact, template, user_info, attach=True):
#     """Compose and send email to a single contact."""
#     variables = {**user_info, **contact}
#     subject = fill_template(template["subject"], variables)
#     body = fill_template(template["body"], variables)
#     result = send_single_email(contact["email"], subject, body, user_info, attach)

#     add_log_entry({
#         "hr_name": contact.get("hr_name", ""),
#         "company": contact.get("company", ""),
#         "email": contact["email"],
#         "status": "sent" if result["success"] else "failed",
#         "error": result.get("error", "")
#     })

#     # Update contact status
#     contacts = get_contacts()
#     for c in contacts:
#         if c.get("id") == contact.get("id") or c["email"] == contact["email"]:
#             c["status"] = "sent" if result["success"] else "failed"
#     save_contacts(contacts)

#     return result


# # ════════════════════════════════════════════
# #  API ROUTES
# # ════════════════════════════════════════════

# # ─── Contacts ───

# @app.route("/api/contacts", methods=["GET"])
# def api_get_contacts():
#     return jsonify(get_contacts())

# @app.route("/api/contacts", methods=["POST"])
# def api_add_contact():
#     data = request.json
#     if not data.get("email"):
#         return jsonify({"error": "Email is required"}), 400
#     contacts = get_contacts()
#     contact = {
#         "id": str(uuid.uuid4())[:8],
#         "hr_name": data.get("hr_name", ""),
#         "email": data["email"],
#         "company": data.get("company", ""),
#         "role": data.get("role", "Flutter Developer"),
#         "status": "pending"
#     }
#     contacts.append(contact)
#     save_contacts(contacts)
#     return jsonify(contact), 201

# @app.route("/api/contacts/bulk", methods=["POST"])
# def api_bulk_add():
#     data = request.json
#     contacts_list = data.get("contacts", [])
#     contacts = get_contacts()
#     added = []
#     for c in contacts_list:
#         if c.get("email"):
#             contact = {
#                 "id": str(uuid.uuid4())[:8],
#                 "hr_name": c.get("hr_name", ""),
#                 "email": c["email"],
#                 "company": c.get("company", ""),
#                 "role": c.get("role", "Flutter Developer"),
#                 "status": "pending"
#             }
#             contacts.append(contact)
#             added.append(contact)
#     save_contacts(contacts)
#     return jsonify({"added": len(added), "contacts": added})

# @app.route("/api/contacts/<contact_id>", methods=["DELETE"])
# def api_delete_contact(contact_id):
#     contacts = get_contacts()
#     contacts = [c for c in contacts if c.get("id") != contact_id]
#     save_contacts(contacts)
#     return jsonify({"success": True})

# @app.route("/api/contacts/reset", methods=["POST"])
# def api_reset_contacts():
#     contacts = get_contacts()
#     for c in contacts:
#         c["status"] = "pending"
#     save_contacts(contacts)
#     return jsonify({"success": True})


# # ─── Template ───

# @app.route("/api/template", methods=["GET"])
# def api_get_template():
#     return jsonify(get_template())

# @app.route("/api/template", methods=["PUT"])
# def api_update_template():
#     save_template(request.json)
#     return jsonify({"success": True})


# # ─── User Info ───

# @app.route("/api/user-info", methods=["GET"])
# def api_get_user_info():
#     info = get_user_info()
#     # Mask the password in response
#     if info.get("gmail_app_password"):
#         info["gmail_app_password_set"] = True
#         info["gmail_app_password"] = "••••••••••••••••"
#     else:
#         info["gmail_app_password_set"] = False
#     return jsonify(info)

# @app.route("/api/user-info", methods=["PUT"])
# def api_update_user_info():
#     data = request.json
#     current = get_user_info()
#     # Don't overwrite password with masked value
#     if data.get("gmail_app_password") == "••••••••••••••••":
#         data["gmail_app_password"] = current.get("gmail_app_password", "")
#     current.update(data)
#     save_user_info(current)
#     return jsonify({"success": True})


# # ─── Resume Upload ───

# @app.route("/api/resume", methods=["POST"])
# def api_upload_resume():
#     if "file" not in request.files:
#         return jsonify({"error": "No file provided"}), 400
#     file = request.files["file"]
#     if not file.filename.lower().endswith(".pdf"):
#         return jsonify({"error": "Only PDF files are accepted"}), 400

#     # Clear old resumes
#     for old in UPLOAD_DIR.glob("resume.*"):
#         old.unlink()

#     filename = "resume.pdf"
#     file.save(UPLOAD_DIR / filename)
#     return jsonify({"success": True, "filename": filename})

# @app.route("/api/resume", methods=["GET"])
# def api_check_resume():
#     resume_files = list(UPLOAD_DIR.glob("resume.*"))
#     if resume_files:
#         return jsonify({"has_resume": True, "filename": resume_files[0].name})
#     return jsonify({"has_resume": False})


# # ─── Send Log ───

# @app.route("/api/log", methods=["GET"])
# def api_get_log():
#     return jsonify(get_send_log())


# # ─── Send Emails ───

# @app.route("/api/send/one", methods=["POST"])
# def api_send_one():
#     """Send email to a single contact."""
#     data = request.json
#     contact_id = data.get("contact_id")
#     attach = data.get("attach_resume", True)

#     contacts = get_contacts()
#     contact = next((c for c in contacts if c.get("id") == contact_id), None)
#     if not contact:
#         return jsonify({"error": "Contact not found"}), 404

#     template = get_template()
#     user_info = get_user_info()

#     result = send_to_contact(contact, template, user_info, attach)
#     return jsonify(result)

# @app.route("/api/send/bulk", methods=["POST"])
# def api_send_bulk():
#     """Send emails to all pending contacts."""
#     data = request.json or {}
#     attach = data.get("attach_resume", True)
#     contact_ids = data.get("contact_ids", None)  # Optional: specific contacts

#     contacts = get_contacts()
#     template = get_template()
#     user_info = get_user_info()

#     if contact_ids:
#         targets = [c for c in contacts if c.get("id") in contact_ids]
#     else:
#         targets = [c for c in contacts if c.get("status") == "pending"]

#     if not targets:
#         return jsonify({"error": "No contacts to send to"}), 400

#     results = {"sent": 0, "failed": 0, "details": []}
#     for contact in targets:
#         result = send_to_contact(contact, template, user_info, attach)
#         if result["success"]:
#             results["sent"] += 1
#         else:
#             results["failed"] += 1
#         results["details"].append({
#             "email": contact["email"],
#             "hr_name": contact.get("hr_name", ""),
#             **result
#         })

#     return jsonify(results)

# @app.route("/api/send/schedule", methods=["POST"])
# def api_schedule_send():
#     """Schedule a bulk send at a specific time."""
#     data = request.json
#     send_time_str = data.get("send_time")
#     attach = data.get("attach_resume", True)

#     if not send_time_str:
#         return jsonify({"error": "send_time is required (ISO format)"}), 400

#     try:
#         send_time = datetime.fromisoformat(send_time_str)
#     except ValueError:
#         return jsonify({"error": "Invalid time format. Use ISO format: 2025-03-15T14:30:00"}), 400

#     if send_time <= datetime.now():
#         return jsonify({"error": "Scheduled time must be in the future"}), 400

#     job_id = f"scheduled_send_{uuid.uuid4().hex[:8]}"

#     def do_scheduled_send():
#         contacts = get_contacts()
#         template = get_template()
#         user_info = get_user_info()
#         targets = [c for c in contacts if c.get("status") == "pending"]
#         for contact in targets:
#             send_to_contact(contact, template, user_info, attach)

#     scheduler.add_job(do_scheduled_send, "date", run_date=send_time, id=job_id)

#     return jsonify({
#         "success": True,
#         "job_id": job_id,
#         "scheduled_for": send_time.isoformat(),
#         "message": f"Bulk send scheduled for {send_time.strftime('%B %d, %Y at %I:%M %p')}"
#     })

# @app.route("/api/send/scheduled", methods=["GET"])
# def api_get_scheduled():
#     """List scheduled jobs."""
#     jobs = []
#     for job in scheduler.get_jobs():
#         jobs.append({
#             "id": job.id,
#             "next_run": str(job.next_run_time),
#         })
#     return jsonify(jobs)

# @app.route("/api/send/scheduled/<job_id>", methods=["DELETE"])
# def api_cancel_scheduled(job_id):
#     """Cancel a scheduled send."""
#     try:
#         scheduler.remove_job(job_id)
#         return jsonify({"success": True})
#     except Exception:
#         return jsonify({"error": "Job not found"}), 404


# # ─── Preview ───

# @app.route("/api/preview", methods=["POST"])
# def api_preview():
#     """Preview email for a contact."""
#     data = request.json
#     contact = data.get("contact", {})
#     template = get_template()
#     user_info = get_user_info()

#     variables = {**user_info, **contact}
#     subject = fill_template(template["subject"], variables)
#     body = fill_template(template["body"], variables)

#     resume_files = list(UPLOAD_DIR.glob("resume.*"))

#     return jsonify({
#         "to": contact.get("email", ""),
#         "subject": subject,
#         "body": body,
#         "has_resume": bool(resume_files)
#     })


# # ─── Health Check ───

# @app.route("/api/health", methods=["GET"])
# def health():
#     return jsonify({
#         "status": "ok",
#         "contacts": len(get_contacts()),
#         "has_resume": bool(list(UPLOAD_DIR.glob("resume.*"))),
#         "gmail_configured": bool(get_user_info().get("gmail_address")),
#     })


# # ─── Serve Frontend ───

# @app.route("/")
# def serve_index():
#     return send_from_directory("static", "index.html")

# @app.route("/<path:path>")
# def serve_static(path):
#     return send_from_directory("static", path)


# # ════════════════════════════════════════════
# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 5000))
#     debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
#     print(f"\n⚡ FlutterMail server running on http://localhost:{port}\n")
#     app.run(host="0.0.0.0", port=port, debug=debug)

"""
FlutterMail — Full-stack email automation for job applications.
Flask backend with Gmail SMTP, scheduling, bulk send, resume attachment.
"""

import os
import json
import smtplib
import ssl
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max upload

# ─── Data storage (JSON files — works on free tiers) ───
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# ─── Scheduler for timed sends ───
scheduler = BackgroundScheduler()
scheduler.start()


# ════════════════════════════════════════════
#  DATA HELPERS
# ════════════════════════════════════════════

def load_data(filename, default=None):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return default if default is not None else {}

def save_data(filename, data):
    with open(DATA_DIR / filename, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_contacts():
    return load_data("contacts.json", [])

def save_contacts(contacts):
    save_data("contacts.json", contacts)

def get_template():
    return load_data("template.json", {
        "subject": "Application for {{role}} Position - {{your_name}}",
        "body": "Dear {{greeting}},\n\nI hope this email finds you well. I am writing to express my strong interest in the {{role}} position at {{company}}.\n\nWith {{your_experience}} of experience as a {{your_role}}, I have built strong expertise in {{your_skills}}. I am confident I can contribute meaningfully to your team.\n\nKey highlights of my background:\n• Proficient in Flutter & Dart with hands-on experience building production apps\n• Strong understanding of state management patterns and clean architecture\n• Experience with Firebase, REST APIs, and third-party integrations\n• Familiar with CI/CD pipelines and agile development practices\n\nI have attached my resume for your review. I would welcome the opportunity to discuss how my skills align with your team's needs.\n\nThank you for your time and consideration. I look forward to hearing from you.\n\nBest regards,\n{{your_name}}\n{{your_phone}}\n{{your_linkedin}}\n{{your_github}}\n{{your_portfolio}}"
    })

def save_template(template):
    save_data("template.json", template)

def get_user_info():
    return load_data("user_info.json", {
        "your_name": "",
        "your_phone": "",
        "your_linkedin": "",
        "your_email_id": "",
        "your_role": "Flutter Developer",
        "your_experience": "2+ years",
        "your_skills": "Flutter, Dart, BLoC/Provider/Riverpod, REST APIs, Firebase",
        "your_portfolio": "",
        "your_github": "",
        "gmail_address": "",
        "gmail_app_password": ""
    })

def save_user_info(info):
    save_data("user_info.json", info)

def get_send_log():
    return load_data("send_log.json", [])

def add_log_entry(entry):
    log = get_send_log()
    log.append({**entry, "timestamp": datetime.now().isoformat()})
    save_data("send_log.json", log)


# ════════════════════════════════════════════
#  EMAIL ENGINE
# ════════════════════════════════════════════

def fill_template(template_str, variables):
    """Replace {{placeholder}} with values. Auto-generates {{greeting}}. Cleans empty lines."""
    hr_name = variables.get("hr_name", "").strip()
    greeting = hr_name if hr_name else "Hiring Manager"
    all_vars = {**variables, "greeting": greeting}
    result = template_str
    for key, value in all_vars.items():
        result = result.replace(f"{{{{{key}}}}}", str(value).strip())
    # Remove lines that are just leftover empty placeholders like {{your_github}}
    import re
    result = re.sub(r'\{\{[a-z_]+\}\}\n?', '', result)
    # Remove consecutive blank lines (more than 2 newlines → 2)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def send_single_email(to_email, subject, body, user_info, attach_resume=True):
    """Send one email via Gmail SMTP."""
    sender = user_info.get("gmail_address", "")
    password = user_info.get("gmail_app_password", "")

    if not sender or not password:
        return {"success": False, "error": "Gmail credentials not configured"}

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach resume if available
    if attach_resume:
        resume_files = list(UPLOAD_DIR.glob("resume.*"))
        if resume_files:
            resume_path = resume_files[0]
            with open(resume_path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition", "attachment",
                    filename=resume_path.name
                )
                msg.attach(attachment)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return {"success": True}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "Authentication failed. Check your Gmail App Password."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_to_contact(contact, template, user_info, attach=True):
    """Compose and send email to a single contact."""
    variables = {**user_info, **contact}
    subject = fill_template(template["subject"], variables)
    body = fill_template(template["body"], variables)
    result = send_single_email(contact["email"], subject, body, user_info, attach)

    add_log_entry({
        "hr_name": contact.get("hr_name", ""),
        "company": contact.get("company", ""),
        "email": contact["email"],
        "status": "sent" if result["success"] else "failed",
        "error": result.get("error", "")
    })

    # Update contact status
    contacts = get_contacts()
    for c in contacts:
        if c.get("id") == contact.get("id") or c["email"] == contact["email"]:
            c["status"] = "sent" if result["success"] else "failed"
    save_contacts(contacts)

    return result


# ════════════════════════════════════════════
#  API ROUTES
# ════════════════════════════════════════════

# ─── Contacts ───

@app.route("/api/contacts", methods=["GET"])
def api_get_contacts():
    return jsonify(get_contacts())

@app.route("/api/contacts", methods=["POST"])
def api_add_contact():
    data = request.json
    if not data.get("email"):
        return jsonify({"error": "Email is required"}), 400
    contacts = get_contacts()
    contact = {
        "id": str(uuid.uuid4())[:8],
        "hr_name": data.get("hr_name", ""),
        "email": data["email"],
        "company": data.get("company", ""),
        "role": data.get("role", "Flutter Developer"),
        "status": "pending"
    }
    contacts.append(contact)
    save_contacts(contacts)
    return jsonify(contact), 201

@app.route("/api/contacts/bulk", methods=["POST"])
def api_bulk_add():
    data = request.json
    contacts_list = data.get("contacts", [])
    contacts = get_contacts()
    added = []
    for c in contacts_list:
        if c.get("email"):
            contact = {
                "id": str(uuid.uuid4())[:8],
                "hr_name": c.get("hr_name", ""),
                "email": c["email"],
                "company": c.get("company", ""),
                "role": c.get("role", "Flutter Developer"),
                "status": "pending"
            }
            contacts.append(contact)
            added.append(contact)
    save_contacts(contacts)
    return jsonify({"added": len(added), "contacts": added})

@app.route("/api/contacts/<contact_id>", methods=["DELETE"])
def api_delete_contact(contact_id):
    contacts = get_contacts()
    contacts = [c for c in contacts if c.get("id") != contact_id]
    save_contacts(contacts)
    return jsonify({"success": True})

@app.route("/api/contacts/reset", methods=["POST"])
def api_reset_contacts():
    contacts = get_contacts()
    for c in contacts:
        c["status"] = "pending"
    save_contacts(contacts)
    return jsonify({"success": True})


# ─── Template ───

@app.route("/api/template", methods=["GET"])
def api_get_template():
    return jsonify(get_template())

@app.route("/api/template", methods=["PUT"])
def api_update_template():
    save_template(request.json)
    return jsonify({"success": True})


# ─── User Info ───

@app.route("/api/user-info", methods=["GET"])
def api_get_user_info():
    info = get_user_info()
    # Mask the password in response
    if info.get("gmail_app_password"):
        info["gmail_app_password_set"] = True
        info["gmail_app_password"] = "••••••••••••••••"
    else:
        info["gmail_app_password_set"] = False
    return jsonify(info)

@app.route("/api/user-info", methods=["PUT"])
def api_update_user_info():
    data = request.json
    current = get_user_info()
    # Don't overwrite password with masked value
    if data.get("gmail_app_password") == "••••••••••••••••":
        data["gmail_app_password"] = current.get("gmail_app_password", "")
    current.update(data)
    save_user_info(current)
    return jsonify({"success": True})


# ─── Resume Upload ───

@app.route("/api/resume", methods=["POST"])
def api_upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    # Clear old resumes
    for old in UPLOAD_DIR.glob("resume.*"):
        old.unlink()

    filename = "resume.pdf"
    file.save(UPLOAD_DIR / filename)
    return jsonify({"success": True, "filename": filename})

@app.route("/api/resume", methods=["GET"])
def api_check_resume():
    resume_files = list(UPLOAD_DIR.glob("resume.*"))
    if resume_files:
        return jsonify({"has_resume": True, "filename": resume_files[0].name})
    return jsonify({"has_resume": False})


# ─── Send Log ───

@app.route("/api/log", methods=["GET"])
def api_get_log():
    return jsonify(get_send_log())


# ─── Send Emails ───

@app.route("/api/send/one", methods=["POST"])
def api_send_one():
    """Send email to a single contact."""
    data = request.json
    contact_id = data.get("contact_id")
    attach = data.get("attach_resume", True)

    contacts = get_contacts()
    contact = next((c for c in contacts if c.get("id") == contact_id), None)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    template = get_template()
    user_info = get_user_info()

    result = send_to_contact(contact, template, user_info, attach)
    return jsonify(result)

@app.route("/api/send/bulk", methods=["POST"])
def api_send_bulk():
    """Send emails to all pending contacts."""
    data = request.json or {}
    attach = data.get("attach_resume", True)
    contact_ids = data.get("contact_ids", None)  # Optional: specific contacts

    contacts = get_contacts()
    template = get_template()
    user_info = get_user_info()

    if contact_ids:
        targets = [c for c in contacts if c.get("id") in contact_ids]
    else:
        targets = [c for c in contacts if c.get("status") == "pending"]

    if not targets:
        return jsonify({"error": "No contacts to send to"}), 400

    results = {"sent": 0, "failed": 0, "details": []}
    for contact in targets:
        result = send_to_contact(contact, template, user_info, attach)
        if result["success"]:
            results["sent"] += 1
        else:
            results["failed"] += 1
        results["details"].append({
            "email": contact["email"],
            "hr_name": contact.get("hr_name", ""),
            **result
        })

    return jsonify(results)

@app.route("/api/send/schedule", methods=["POST"])
def api_schedule_send():
    """Schedule a bulk send at a specific time."""
    data = request.json
    send_time_str = data.get("send_time")
    attach = data.get("attach_resume", True)

    if not send_time_str:
        return jsonify({"error": "send_time is required (ISO format)"}), 400

    try:
        send_time = datetime.fromisoformat(send_time_str)
    except ValueError:
        return jsonify({"error": "Invalid time format. Use ISO format: 2025-03-15T14:30:00"}), 400

    if send_time <= datetime.now():
        return jsonify({"error": "Scheduled time must be in the future"}), 400

    job_id = f"scheduled_send_{uuid.uuid4().hex[:8]}"

    def do_scheduled_send():
        contacts = get_contacts()
        template = get_template()
        user_info = get_user_info()
        targets = [c for c in contacts if c.get("status") == "pending"]
        for contact in targets:
            send_to_contact(contact, template, user_info, attach)

    scheduler.add_job(do_scheduled_send, "date", run_date=send_time, id=job_id)

    return jsonify({
        "success": True,
        "job_id": job_id,
        "scheduled_for": send_time.isoformat(),
        "message": f"Bulk send scheduled for {send_time.strftime('%B %d, %Y at %I:%M %p')}"
    })

@app.route("/api/send/scheduled", methods=["GET"])
def api_get_scheduled():
    """List scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time),
        })
    return jsonify(jobs)

@app.route("/api/send/scheduled/<job_id>", methods=["DELETE"])
def api_cancel_scheduled(job_id):
    """Cancel a scheduled send."""
    try:
        scheduler.remove_job(job_id)
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Job not found"}), 404


# ─── Preview ───

@app.route("/api/preview", methods=["POST"])
def api_preview():
    """Preview email for a contact."""
    data = request.json
    contact = data.get("contact", {})
    template = get_template()
    user_info = get_user_info()

    variables = {**user_info, **contact}
    subject = fill_template(template["subject"], variables)
    body = fill_template(template["body"], variables)

    resume_files = list(UPLOAD_DIR.glob("resume.*"))

    return jsonify({
        "to": contact.get("email", ""),
        "subject": subject,
        "body": body,
        "has_resume": bool(resume_files)
    })


# ─── Health Check ───

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "contacts": len(get_contacts()),
        "has_resume": bool(list(UPLOAD_DIR.glob("resume.*"))),
        "gmail_configured": bool(get_user_info().get("gmail_address")),
    })


# ─── Serve Frontend ───

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


# ════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n⚡ FlutterMail server running on http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)