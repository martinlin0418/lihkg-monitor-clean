import requests, time, os, threading, random
from flask import Flask

CAT_ID = int(os.getenv("CAT_ID", "35"))
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot running cat={CAT_ID} OK"

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}, timeout=10)
    except:
        pass

seen = set()

def monitor():
    print(f"=== Bot started cat={CAT_ID} ===", flush=True)
    while True:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36",
                "X-LI-DEVICE": "android",
                "X-LI-DEVICE-TYPE": "android",
                "Accept": "application/json",
                "Referer": "https://lihkg.com/"
            }
            url = f"https://lihkg.com/api_v2/thread/category?cat_id={CAT_ID}&page=1&count=15&type=now"
            r = requests.get(url, headers=headers, timeout=20)
            if "application/json" not in r.headers.get("Content-Type","") and len(r.text) < 200:
                print(f"LIHKG回應異常: {r.text[:200]}", flush=True)
                time.sleep(60)
                continue
            
            data = r.json()
            items = data.get("response",{}).get("items",[])
            if not items:
                print("未抓到items，可能被風控，60秒後再試", flush=True)
            else:
                print(f"checked {len(items)} threads at {time.strftime('%H:%M:%S')} latest={items[0]['thread_id']}", flush=True)
                for t in items:
                    tid = str(t["thread_id"])
                    if tid not in seen:
                        if len(seen) > 0:
                            title = t.get("title","")
                            link = f"https://lihkg.com/thread/{tid}"
                            send_tg(f"📱 電訊台\n{title}\n{link}")
                            print(f"PUSH {tid}", flush=True)
                        seen.add(tid)
            if len(seen) > 300:
                seen.clear()
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
        time.sleep(15 + random.randint(2,5))

threading.Thread(target=monitor, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
