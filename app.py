import os
import re
import uuid
import pytz
import psycopg2
import requests
import gradio as gr
import json
import pickle
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email.mime.text import MIMEText
from datetime import datetime, date
from dotenv import load_dotenv


# ================= LOAD ENV =================

load_dotenv()

DB_URL = os.getenv("DB_URL")
GMAIL_USER = os.getenv("GMAIL_USER")
CRON_SECRET = os.getenv("CRON")
HF_URL = os.getenv("HF_URL")

LEETCODE_API = "https://leetcode-api-vercel.vercel.app"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token.pkl"


# ================= DB =================

def get_db():
    return psycopg2.connect(DB_URL, sslmode="require")


# ================= GMAIL AUTH =================

def get_gmail_service():

    creds = None

    # Load token
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)
        except:
            creds = None

    # Refresh token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)

        except Exception as e:
            print("❌ Token refresh failed:", e)
            creds = None

    if not creds:
        raise Exception(
            "❌ Missing token.pkl. Generate locally and upload to HF."
        )

    return build("gmail", "v1", credentials=creds)


# ================= EMAIL =================

def send_email(to, subject, html):

    try:
        service = get_gmail_service()

        message = MIMEText(html, "html")
        message["To"] = to
        message["From"] = GMAIL_USER
        message["Subject"] = subject

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        body = {"raw": raw}

        result = service.users().messages().send(
            userId="me",
            body=body
        ).execute()

        print("✅ Gmail sent:", to, "| ID:", result.get("id"))

        return True

    except Exception as e:
        print("❌ Gmail send failed:", e)
        return False


# ================= VALIDATION =================

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def valid_email(email):
    return bool(email and EMAIL_REGEX.match(email))


def valid_leetcode(username):

    if not username or len(username) < 3:
        return False

    try:
        r = requests.get(
            f"{LEETCODE_API}/{username}",
            timeout=8
        )

        return r.status_code == 200

    except:
        return False


# ================= LEETCODE =================

def get_daily_problem():

    r = requests.get(f"{LEETCODE_API}/daily", timeout=10)
    r.raise_for_status()

    data = r.json()

    if "questionTitle" in data:
        return data["questionTitle"], data["titleSlug"]

    if "title" in data:
        return data["title"], data["titleSlug"]

    raise ValueError("Invalid daily API format")


def solved_today(username, slug):

    try:
        r = requests.get(
            f"{LEETCODE_API}/{username}/acSubmission?limit=20",
            timeout=10,
        )

        if r.status_code != 200:
            return False

        data = r.json()

        if isinstance(data, dict) and "submission" in data:
            submissions = data["submission"]

        elif isinstance(data, dict) and "data" in data:
            submissions = data["data"]

        elif isinstance(data, list):
            submissions = data

        else:
            return False

        today = date.today()

        for s in submissions:

            if not isinstance(s, dict):
                continue

            if s.get("titleSlug") != slug:
                continue

            ts = s.get("timestamp")

            if not ts:
                continue

            solved_date = datetime.fromtimestamp(
                int(ts),
                tz=pytz.utc
            ).date()

            if solved_date == today:
                return True

        return False

    except Exception as e:
        print("⚠️ solved_today error:", e)
        return False


# ================= SUBSCRIBE =================

def subscribe(username, email, timezone):

    if not valid_leetcode(username):
        return "❌ Invalid LeetCode username"

    if not valid_email(email):
        return "❌ Invalid email format"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT email_verified, verification_token, unsubscribed
        FROM users
        WHERE email = %s
    """, (email,))

    row = cur.fetchone()

    if row:

        verified, token, unsub = row

        # Active
        if verified and not unsub:
            cur.close()
            conn.close()
            return "⚠️ Already subscribed"

        # Resubscribe
        if verified and unsub:

            cur.execute("""
                UPDATE users
                SET unsubscribed=false,
                    leetcode_username=%s,
                    timezone=%s,
                    last_sent_date=NULL,
                    last_sent_slot=NULL
                WHERE email=%s
            """, (username, timezone, email))

            conn.commit()
            cur.close()
            conn.close()

            return "✅ Re-subscribed successfully!"

        # Resend verify
        link = f"{HF_URL}?verify={token}"

        send_email(
            email,
            "Verify your subscription",
            f"<a href='{link}'>Verify</a>"
        )

        cur.close()
        conn.close()

        return "📩 Verification re-sent"

    # New user
    token = uuid.uuid4().hex

    cur.execute("""
        INSERT INTO users (
            leetcode_username,
            email,
            timezone,
            email_verified,
            verification_token,
            unsubscribed
        )
        VALUES (%s,%s,%s,false,%s,false)
    """, (username, email, timezone, token))

    conn.commit()
    cur.close()
    conn.close()

    link = f"{HF_URL}?verify={token}"

    send_email(
        email,
        "Verify your subscription",
        f"<a href='{link}'>Verify</a>"
    )

    return "📩 Verification sent"


# ================= VERIFY =================

def verify_user(token):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET email_verified=true
        WHERE verification_token=%s
        AND email_verified=false
    """, (token,))

    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        return "❌ Invalid link"

    return "✅ Email verified"


# ================= UNSUBSCRIBE =================

def unsubscribe_user(token):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET unsubscribed=true
        WHERE verification_token=%s
    """, (token,))

    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        return "❌ Invalid link"

    return "✅ Unsubscribed"


# ================= SCHEDULER =================

def run_scheduler(secret):

    if secret != CRON_SECRET:
        return "❌ Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, leetcode_username, email, timezone,
               last_sent_date, last_sent_slot,
               verification_token
        FROM users
        WHERE email_verified=true
        AND unsubscribed=false
    """)

    users = cur.fetchall()

    title, slug = get_daily_problem()

    now = datetime.now(pytz.utc)

    sent = 0

    for uid, user, mail, tz, last_d, last_s, token in users:

        local = now.astimezone(pytz.timezone(tz))
        hour = local.hour

        if hour == 9:
            slot = "morning"
            sub = "Today's LeetCode"
            body = f"<b>{title}</b>"

        elif hour == 15:
            slot = "afternoon"
            sub = "Reminder"
            body = f"Solve <b>{title}</b>"

        elif hour == 20:
            slot = "night"
            sub = "Final Reminder"
            body = f"Last chance: <b>{title}</b>"

        else:
            continue

        today = date.today()

        if last_d == today and last_s == slot:
            continue

        if solved_today(user, slug):
            continue

        unsub = f"{HF_URL}?unsubscribe={token}"

        ok = send_email(
            mail,
            sub,
            f"{body}<br><a href='{unsub}'>Unsubscribe</a>"
        )

        if not ok:
            print("❌ Failed:", mail)
            continue

        cur.execute("""
            UPDATE users
            SET last_sent_date=%s,
                last_sent_slot=%s
            WHERE id=%s
        """, (today, slot, uid))

        sent += 1

    conn.commit()
    cur.close()
    conn.close()

    return f"✅ Scheduler completed. Sent: {sent}"


# ================= UI =================

with gr.Blocks(title="LeetCode Notifier") as app:

    gr.Markdown("## 📬 LeetCode Daily Email Notifier")

    user = gr.Textbox(label="Username")
    mail = gr.Textbox(label="Email")
    tz = gr.Dropdown(pytz.all_timezones, value="Asia/Kolkata")

    out = gr.Textbox()

    gr.Button("Subscribe").click(subscribe, [user, mail, tz], out)

    gr.Markdown("### 🔒 Scheduler")

    sec = gr.Textbox(type="password")

    gr.Button("Run").click(run_scheduler, sec, out)


if __name__ == "__main__":
    app.launch(debug=True)
