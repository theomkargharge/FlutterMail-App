# ⚡ FlutterMail

**Automated email sender for Flutter job applications.** Deploy for free on Railway or Render.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 📝 **Email Templates** — Customizable template with `{{placeholders}}`
- 📎 **Resume Attachment** — Upload your PDF resume, auto-attaches to every email
- 👥 **Contact Management** — Add HRs one-by-one or bulk import
- 🚀 **Immediate Send** — Send to one or all pending contacts
- ⏰ **Scheduled Send** — Set a future date/time for automatic bulk sending
- 📜 **Send History** — Track every email sent
- 🔒 **Gmail App Password** — Secure authentication (no OAuth hassle)

---

## 🚀 Deploy in 5 Minutes

### Option A: Railway (Recommended)

1. **Push to GitHub:**
   ```bash
   cd fluttermail-app
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create fluttermail --public --push
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app) → Sign in with GitHub
   - Click **"New Project"** → **"Deploy from GitHub Repo"**
   - Select your `fluttermail` repo
   - Railway auto-detects Python and deploys!
   - Click **"Generate Domain"** in Settings to get your URL

3. **Done!** Your app is live at `https://fluttermail-xxxx.up.railway.app`

### Option B: Render

1. **Push to GitHub** (same as above)

2. **Deploy on Render:**
   - Go to [render.com](https://render.com) → Sign in with GitHub
   - Click **"New" → "Web Service"**
   - Connect your `fluttermail` repo
   - Render auto-detects the `render.yaml` config
   - Click **"Create Web Service"**

3. **Done!** Your app is live at `https://fluttermail.onrender.com`

---

## 🔧 Local Development

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/fluttermail.git
cd fluttermail
pip install -r requirements.txt

# Run locally
python app.py

# Open http://localhost:5000
```

---

## 📋 First-Time Setup (After Deploy)

1. Open your deployed app URL
2. Go to **⚙️ Settings** tab
3. Fill in your name, phone, LinkedIn
4. Add your **Gmail address** and **App Password**
   - Get App Password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Requires 2-Step Verification enabled
5. Upload your **resume PDF**
6. Go to **👥 Contacts** → Add HR emails
7. Go to **📝 Template** → Customize your email
8. Go to **🚀 Send** → Start sending!

---

## 📁 Project Structure

```
fluttermail-app/
├── app.py              # Flask backend (API + email engine)
├── static/
│   └── index.html      # Frontend (single-file, no build needed)
├── requirements.txt    # Python dependencies
├── Procfile            # Process command for deployment
├── railway.json        # Railway config
├── render.yaml         # Render config
├── data/               # JSON data storage (auto-created)
└── uploads/            # Resume uploads (auto-created)
```

## ⚠️ Important Notes

- **Gmail allows ~500 emails/day** on personal accounts
- **App Password ≠ your Gmail password** — it's a separate 16-char code
- **Data persists** on the deployed server via JSON files
- **Free tiers** may sleep after inactivity — first request wakes it up
- Railway free tier: 500 hours/month; Render free tier: 750 hours/month

## License

MIT — Use it, modify it, land that Flutter job! 🎯
