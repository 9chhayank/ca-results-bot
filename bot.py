import requests
from bs4 import BeautifulSoup
import os

ROLL_NUMBER         = os.environ.get("ROLL_NUMBER", "")
REGISTRATION_NUMBER = os.environ.get("REG_NUMBER", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Target website ────────────────────────────────────────────────────────────
TARGET_URL = "https://icai.nic.in"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Keywords to detect results being live
# Targeting January 2026 CA Final results specifically
KEYWORDS = [
    "ca final",
    "final examination",
    "january 2026",
    "jan 2026",
    "result",
]


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
        print("✅ Telegram message sent!")
    except Exception as e:
        print(f"❌ Telegram failed: {e}")


def check_if_results_live():
    """Check icai.nic.in for CA Final January 2026 result links."""
    try:
        resp = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = resp.text.lower()

        print(f"✅ Reached {TARGET_URL} successfully")

        # Look for links containing result-related keywords
        all_links = soup.find_all("a", href=True)
        result_links = []

        for link in all_links:
            link_text = link.get_text(strip=True).lower()
            href = link["href"].lower()
            combined = link_text + " " + href

            # Must contain "final" AND ("result" OR "january" OR "jan")
            if "final" in combined and ("result" in combined or "january" in combined or "jan" in combined):
                full_url = link["href"]
                if full_url.startswith("/"):
                    full_url = "https://icai.nic.in" + full_url
                result_links.append((link.get_text(strip=True), full_url))
                print(f"🔗 Found link: {link.get_text(strip=True)} → {full_url}")

        if result_links:
            return True, result_links

        # Fallback: check raw page text for keywords combo
        if ("final" in page_text and "result" in page_text and
                ("january" in page_text or "jan 2026" in page_text)):
            print("⚠️ Keywords found in page text but no direct link detected")
            return True, []

        print("❌ No CA Final January 2026 result found yet")
        return False, []

    except Exception as e:
        print(f"❌ Error reaching {TARGET_URL}: {e}")
        return False, []


def fetch_my_result(result_page_url):
    """Try to submit roll number on the result page and get marks."""
    payload = {
        "regno":  REGISTRATION_NUMBER,
        "rollno": ROLL_NUMBER,
        "exam":   "finalnew",
        "submit": "Submit",
    }
    try:
        resp = requests.post(result_page_url, data=payload, headers=HEADERS, timeout=20)
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
        print(f"Error fetching result: {e}")
    return None


def main():
    print(f"🔍 Checking {TARGET_URL} for CA Final January 2026 results...")
    print(f"   Roll No: {ROLL_NUMBER}")

    live, result_links = check_if_results_live()

    if live:
        print("🎉 Results are LIVE!")

        # Try to fetch personal result from the first result link found
        my_result = None
        if result_links:
            first_link_url = result_links[0][1]
            my_result = fetch_my_result(first_link_url)

        # Build links text for Telegram
        links_text = ""
        for name, url in result_links:
            links_text += f"\n🔗 <a href='{url}'>{name}</a>"

        if my_result:
            send_telegram(
                "🎓 <b>CA FINAL RESULTS ARE OUT!</b>\n\n"
                f"Roll No: <b>{ROLL_NUMBER}</b>\n\n"
                "📊 <b>YOUR RESULTS:</b>\n"
                f"<pre>{my_result[:3000]}</pre>\n"
                f"{links_text}"
            )
        else:
            send_telegram(
                "🎓 <b>CA FINAL JANUARY 2026 RESULTS ARE LIVE!</b>\n\n"
                f"👉 Check here: {links_text if links_text else TARGET_URL}\n\n"
                f"Roll No: <b>{ROLL_NUMBER}</b>\n"
                f"Reg No: {REGISTRATION_NUMBER}\n\n"
                "⚠️ <i>Could not auto-fetch marks — please check manually</i>"
            )
    else:
        print("❌ Results not live yet.")
        send_telegram(
            "🔍 <b>Checked icai.nic.in</b>\n\n"
            "❌ CA Final January 2026 results are <b>not live yet</b>\n\n"
            "⏰ Will check again in sometime automatically!"
        )


if __name__ == "__main__":
    main()
