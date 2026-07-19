import socket
import threading
import time
import urllib.request
import webbrowser
from app import app

HOST = '127.0.0.1'


def _free_port():
    # Let the OS pick an unused port rather than hardcoding 5000, which may
    # already be taken on the user's machine.
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _start_flask(port):
    app.run(host=HOST, port=port, use_reloader=False)


def _wait_for_flask(url):
    for _ in range(40):
        try:
            urllib.request.urlopen(url)
            return True
        except Exception:
            time.sleep(0.25)
    return False


if __name__ == '__main__':
    port = _free_port()
    url = f'http://{HOST}:{port}'

    t = threading.Thread(target=_start_flask, args=(port,), daemon=True)
    t.start()

    if not _wait_for_flask(url):
        raise SystemExit('Stock Analyzer: the local server failed to start.')

    webbrowser.open(url)
    print(f'Stock Analyzer is running at {url}')
    print('Close this window to quit.')

    # The Flask thread is a daemon, so hold the main thread open to keep the
    # server alive until the user kills the process.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
