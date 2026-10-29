import os, time, json, requests, threading
from flask import Flask

CAT_ID = 35
SEEN_FILE = "seen_ids.json"
CHECK_INTERVAL = 300

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

app = Flask(__name__)
@app.route("/")
def home():
    return "LIHKG Monitor is running!"

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=10)
    except: pass

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f: return set(json.load(f))
    except: return set()

def save_seen(s):
    with open(SEEN_FILE, "w") as f: json.dump(list(s)[-1000:], f)

def fetch_threads():
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        "Referer": "https://lihkg.com/category/35",
        "Origin": "https://lihkg.com",
        "X-LI-DEVICE": "0",
    }
    url = f"https://lihkg.com/api_v2/thread/category?cat_id={CAT_ID}&page=1&count=60&type=now"
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json().get("response", {}).get("items", [])

def monitor_loop():
    seen = load_seen()
    if len(seen)==0:
        send_tg("✅ LIHKG Monitor (Render) started!")
    while True:
        try:
            items = fetch_threads()
            for it in items:
                tid = str(it.get("thread_id"))
                if tid not in seen:
                    seen.add(tid)
                    title = it.get("title","")
                    link = f"https://lihkg.com/thread/{tid}"
                    send_tg(f"🆕 [{CAT_ID}] {title}\n{link}")
                    time.sleep(0.5)
            save_seen(seen)
        except Exception as e: print(e)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=monitor_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
