import requests, time, os, threading, random
from flask import Flask

CAT_ID = int(os.getenv("CAT_ID", "35"))
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot running cat={CAT_ID} 15s mode OK"

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}, timeout=10)
    except:
        pass

seen = set()
first_run = True

def monitor():
    global first_run
    print(f"=== Bot started cat={CAT_ID} 15s clean mode ===", flush=True)
    fail = 0
    while True:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                "X-LI-DEVICE": "android",
                "Accept": "application/json",
            }
            url = f"https://lihkg.com/api_v2/thread/category?cat_id={CAT_ID}&page=1&count=15&type=now"
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            items = data.get("response", {}).get("items", [])

            if not items:
                fail += 1
                sleep_t = 60 + fail * 30
                print(f"未抓到items，可能被風控，第{fail}次 瞓{sleep_t}秒", flush=True)
                time.sleep(sleep_t)
                if fail > 3:
                    time.sleep(120)
                continue

            fail = 0
            
            if first_run:
                for t in items:
                    seen.add(str(t["thread_id"]))
                first_run = False
                print(f"初始化完成，記住 {len(seen)} 個舊post，之後先開始推新post", flush=True)
            else:
                # 由舊到新推，唔會亂序
                for t in reversed(items):
                    tid = str(t["thread_id"])
                    if tid not in seen:
                        seen.add(tid)
                        title = t.get("title", "")
                        link = f"https://lihkg.com/thread/{tid}"
                        send_tg(f"📱 電訊台\n{title}\n{link}")
                        print(f"PUSH {tid}", flush=True)

            # 清理記憶，唔好一次清晒
            if len(seen) > 500:
                temp = list(seen)[-400:]
                seen.clear()
                for x in temp:
                    seen.add(x)
                    
            print(f"checked {len(items)} at {time.strftime('%H:%M:%S')} latest={items[0]['thread_id']}", flush=True)

        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(30)

        # 終極15秒版核心
        time.sleep(15 + random.randint(2, 5))

threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
