import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# ── YOUR DETAILS (filled via environment variables) ──────────────────────────
ROLL_NUMBER          = os.environ.get("ROLL_NUMBER", "")
REGISTRATION_NUMBER  = os.environ.get("REG_NUMBER", "")
TELEGRAM_BOT_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID     = os.environ.get("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL       = 600   # seconds (10 minutes)

RESULTS_URLS = [
    "https://icaiexam.icai.org",
    "https://results.icai.org",
    "https://caresults.icai.org",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(message):
    """Send a message to your Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
        print("✅ Telegram message sent!")
    except Exception as e:
        print(f"❌ Telegram failed: {e}")


def check_if_results_live():
    """Check if CA Final results page is live."""
    keywords = [
        "ca final result",
        "final examination result",
        "result declared",
        "november 2024",
        "may 2025",
        "june 2025",
    ]
    for url in RESULTS_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            text = resp.text.lower()
            for kw in keywords:
                if kw in text:
                    print(f"🎉 Results found at {url} (keyword: {kw})")
                    return True, url
        except Exception as e:
            print(f"⚠️  Could not reach {url}: {e}")
    return False, None


def fetch_my_result(base_url):
    """Try to fetch personal result by submitting roll number."""
    endpoints = ["/result.php", "/CAFinalResult.aspx", "/index.php"]
    payload = {
        "regno":  REGISTRATION_NUMBER,
        "rollno": ROLL_NUMBER,
        "exam":   "finalnew",
        "submit": "Submit",
    }
    for endpoint in endpoints:
        try:
            url = base_url.rstrip("/") + endpoint
            resp = requests.post(url, data=payload, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")
            result_text = ""
            for table in tables:
                for row in table.find_all("tr"):
                    cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                    if cols:
                        result_text += " | ".join(cols) + "\n"
            if result_text.strip():
                return result_text
        except Exception as e:
            print(f"Could not fetch from {endpoint}: {e}")
    return None


def main():
    print("🤖 CA Results Bot is running...")
    print(f"   Roll No: {ROLL_NUMBER}")
    print(f"   Reg No:  {REGISTRATION_NUMBER}")
    print(f"   Checking every {CHECK_INTERVAL // 60} minutes")

    # Send a startup confirmation to your Telegram
    send_telegram(
        "🤖 <b>CA Results Bot Started!</b>\n\n"
        f"I'll check every {CHECK_INTERVAL // 60} minutes and notify you the moment results are out.\n"
        f"Roll No: {ROLL_NUMBER}"
    )

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Checking for results...")

        live, url = check_if_results_live()

        if live:
            my_result = fetch_my_result(url)

            if my_result:
                message = (
                    "🎓 <b>CA FINAL RESULTS ARE OUT!</b>\n\n"
                    f"Roll No: <b>{ROLL_NUMBER}</b>\n"
                    f"Reg No: {REGISTRATION_NUMBER}\n\n"
                    "📊 <b>YOUR RESULTS:</b>\n"
                    f"<pre>{my_result[:3000]}</pre>\n\n"
                    f"🔗 Check: {url}"
                )
            else:
                message = (
                    "🎓 <b>CA FINAL RESULTS ARE LIVE!</b>\n\n"
                    f"I couldn't auto-fetch your result.\n"
                    f"👉 Check manually: {url}\n\n"
                    f"Roll No: {ROLL_NUMBER}\n"
                    f"Reg No: {REGISTRATION_NUMBER}"
                )

            send_telegram(message)
            print("✅ Notified! Bot will keep checking every 10 min.")
            # Keep running in case the first scrape failed
        else:
            print("❌ Results not live yet.")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main() 
