"""Launch a built stock-analyzer binary and check that it actually serves.

Run against the PyInstaller output to catch bundles that build cleanly but fail
at runtime — a missing templates/ or CA bundle produces exactly that failure.

    python scripts/smoke_test.py dist/stock-analyzer

Only offline routes are exercised. /analyze is deliberately left out: it hits
live Yahoo Finance, which would make CI fail for reasons unrelated to the build.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request

TIMEOUT = 90  # generous: a onefile bundle unpacks itself on first run


def main(binary):
    if not os.path.exists(binary):
        print(f'FAIL: no such binary: {binary}')
        return 1

    # Stop the app opening a browser tab on a CI runner.
    env = {**os.environ, 'STOCK_ANALYZER_NO_BROWSER': '1'}

    proc = subprocess.Popen(
        [binary],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        bufsize=1,
    )
    assert proc.stdout is not None  # stdout=PIPE guarantees this

    url = None
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            print('FAIL: process exited early with code', proc.returncode)
            print(proc.stdout.read())
            return 1
        line = proc.stdout.readline()
        if line:
            print('   app:', line.rstrip())
            m = re.search(r'http://127\.0\.0\.1:\d+', line)
            if m:
                url = m.group(0)
                break

    if not url:
        print(f'FAIL: no URL printed within {TIMEOUT}s')
        proc.kill()
        return 1

    failures = []
    try:
        # The UI page must render: proves templates/ made it into the bundle.
        with urllib.request.urlopen(url + '/', timeout=30) as r:
            body = r.read().decode('utf-8', 'replace')
        if r.status != 200:
            failures.append(f'GET / returned {r.status}')
        elif '<html' not in body.lower():
            failures.append('GET / did not return an HTML document')
        else:
            print(f'   PASS GET /  ({len(body)} bytes)')

        # JSON route: proves Flask routing and the analyzer import both work.
        with urllib.request.urlopen(url + '/interval-limits', timeout=30) as r:
            limits = json.loads(r.read())
        if not isinstance(limits, dict) or not limits:
            failures.append(f'GET /interval-limits returned {limits!r}')
        else:
            print(f'   PASS GET /interval-limits  ({len(limits)} intervals)')
    except Exception as e:
        failures.append(f'{type(e).__name__}: {e}')
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    if failures:
        for f in failures:
            print('FAIL:', f)
        return 1

    print('smoke test passed')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
