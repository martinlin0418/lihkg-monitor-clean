import requests, time, os, threading
from flask import Flask

CAT_ID = int(os.getenv("CAT_ID", "35"))
# 兼容你Render入面叫 BOT_TOKEN 定係 TELEGRAM_BOT_TOKEN 都得
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot running cat={CAT_ID} - OK"

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID: 
        print("未set BOT_TOKEN/CHAT_ID")
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"TG error {e}")

seen = set()

def monitor():
    print(f"=== Bot started cat={CAT_ID} ===", flush=True)
    while True:
        try:
            url = f"https://lihkg.com/api_v2/thread/category?cat_id={CAT_ID}&page=1&count=10&type=latest"
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0","x-li-device":"android"}, timeout=15).json()
            items = r.get("response",{}).get("items",[])
            if not items:
                print("抓唔到LIHKG，可能cat_id錯", flush=True)
            for t in items:
                tid = str(t["thread_id"])
                if tid not in seen:
                    if len(seen) > 0:
                        title = t.get("title","")
                        link = f"https://lihkg.com/thread/{tid}"
                        send_tg(f"📱 {title}\n{link}")
                        print(f"PUSH {tid} {title}", flush=True)
                    seen.add(tid)
            if len(seen) > 200:
                seen.clear()
            print(f"checked {len(items)} threads at {time.strftime('%H:%M:%S')}", flush=True)
        except Exception as e:
            print(f"Error {e}", flush=True)
        time.sleep(60)

threading.Thread(target=monitor, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
