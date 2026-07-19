import contextlib
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from app import app

HOST = '127.0.0.1'

# PyInstaller points these at its unpack directory so the bundled CPython finds
# the libraries shipped alongside it. The variables are inherited by child
# processes, which is a problem for us: webbrowser.open() shells out via
# /bin/sh, and that shell then loads our bundled libreadline instead of the
# system one. If the user's bash is newer than the machine the bundle was built
# on, it dies with "undefined symbol: rl_print_keybinding" and no browser
# opens. PyInstaller saves whatever the user originally had in <VAR>_ORIG.
_LIBRARY_PATH_VARS = ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH')


@contextlib.contextmanager
def _system_library_path():
    """Restore the user's original library paths for anything we spawn."""
    if not getattr(sys, 'frozen', False):
        yield
        return

    saved = {var: os.environ.get(var) for var in _LIBRARY_PATH_VARS}
    try:
        for var in _LIBRARY_PATH_VARS:
            original = os.environ.get(f'{var}_ORIG')
            if original is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = original
        yield
    finally:
        for var, value in saved.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value


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

    # Set STOCK_ANALYZER_NO_BROWSER=1 to leave the browser closed — used by the
    # CI smoke test, where there is nothing to open a page with.
    if not os.environ.get('STOCK_ANALYZER_NO_BROWSER'):
        with _system_library_path():
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
