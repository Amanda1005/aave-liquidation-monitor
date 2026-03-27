import os
import requests
from datetime import datetime, timezone, timedelta

# Config
DUNE_API_KEY = os.environ["DUNE_API_KEY"]
DUNE_QUERY_ID = os.environ["DUNE_QUERY_ID"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
THRESHOLD = float(os.environ.get("THRESHOLD", "5"))

def get_results():
    url = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"
    headers = {"X-Dune-API-Key": DUNE_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data["result"]["rows"]

def get_latest_liquidation(rows):
    latest = rows[0]
    day = latest["day"][:10]
    amount = float(latest["total_debt_covered_usd"]) / 1_000_000
    return day, amount

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    print("[INFO] Running Aave liquidation monitor...")
    rows = get_results()
    print(f"[INFO] Rows received: {len(rows)}")
    day, amount = get_latest_liquidation(rows)
    print(f"[RESULT] {day} → ${amount:.2f}M")

    # 確認數據是今天或昨天的
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[INFO] Data date: {day} | Today: {today} | Yesterday: {yesterday}")

    if day not in [today, yesterday]:
        print(f"[WARNING] Data may be stale — {day} is older than yesterday")

    if amount > THRESHOLD:
        message = (
            f"🚨 *Aave V3 Liquidation Alert*\n"
            f"Date: `{day}`\n"
            f"Daily Liquidation: `${amount:.2f}M`\n"
            f"Threshold: `${THRESHOLD}M`\n"
            f"Status: *CRITICAL — immediate review required*"
        )
        send_telegram(message)
        print(f"[ALERT] ${amount:.2f}M > ${THRESHOLD}M → Telegram sent")
    else:
        print(f"[OK] ${amount:.2f}M ≤ ${THRESHOLD}M → no alert")

if __name__ == "__main__":
    main()