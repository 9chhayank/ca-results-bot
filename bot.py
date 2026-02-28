import requests
from bs4 import BeautifulSoup
import os

ROLL_NUMBER         = os.environ.get("ROLL_NUMBER", "")
REGISTRATION_NUMBER = os.environ.get("REG_NUMBER", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")

RESULTS_URLS = [
    "https://icaiexam.icai.org",
    "https://results.icai.org",
    "https://caresults.icai.org",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}


def send_telegram(message):
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
                    print(f"🎉 Results found at {url}")
                    return True, url
        except Exception as e:
            print(f"⚠️ Could not reach {url}: {e}")
    return False, None


def fetch_my_result(base_url):
    payload = {
        "regno":  REGISTRATION_NUMBER,
        "rollno": ROLL_NUMBER,
        "exam":   "finalnew",
        "submit": "Submit",
    }
    endpoints = ["/result.php", "/CAFinalResult.aspx", "/index.php"]
    for endpoint in endpoints:
        try:
            url = base_url.rstrip("/") + endpoint
            resp = requests.post(url, data=payload, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, "html.parser")
            result_text = ""
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                    if cols:
                        result_text += " | ".join(cols) + "\n"
            if result_text.strip():
                return result_text
        except Exception as e:
            print(f"Error: {e}")
    return None


def main():
    print(f"🔍 Checking for CA Final results...")
    live, url = check_if_results_live()

    if live:
        print("🎉 Results are LIVE!")
        my_result = fetch_my_result(url)

        if my_result:
            send_telegram(
                "🎓 <b>CA FINAL RESULTS ARE OUT!</b>\n\n"
                f"Roll No: <b>{ROLL_NUMBER}</b>\n\n"
                "📊 <b>YOUR RESULTS:</b>\n"
                f"<pre>{my_result[:3000]}</pre>\n\n"
                f"🔗 {url}"
            )
        else:
            send_telegram(
                "🎓 <b>CA FINAL RESULTS ARE LIVE!</b>\n\n"
                f"Couldn't auto-fetch your result.\n"
                f"👉 Check manually: {url}\n\n"
                f"Roll No: {ROLL_NUMBER}"
            )
    else:
        print("❌ Results not live yet.")
        send_telegram("🔍 Checked for CA Final results — <b>Not live yet.</b>\n\nWill keep checking every 10 minutes automatically!")

if __name__ == "__main__":
    main()
