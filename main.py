import threading
import urllib.request
import time
import webview
from app import app

def _start_flask():
    app.run(host='127.0.0.1', port=5000, use_reloader=False)

def _wait_for_flask():
    for _ in range(40):
        try:
            urllib.request.urlopen('http://127.0.0.1:5000')
            return
        except Exception:
            time.sleep(0.25)

if __name__ == '__main__':
    t = threading.Thread(target=_start_flask, daemon=True)
    t.start()
    _wait_for_flask()

    webview.create_window(
        'Stock Analyzer',
        'http://127.0.0.1:5000',
        width=1400,
        height=900,
        min_size=(900, 600),
    )
    webview.start()
