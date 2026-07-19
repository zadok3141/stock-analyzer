# Stock Analyzer

A desktop app for technical market-structure analysis. Enter a ticker and it pulls
price history from Yahoo Finance, locates swing highs and lows, and detects
**BOS** (Break of Structure) and **CHoCH** (Change of Character) signals — the
points where price breaks a prior swing level, and where it does so against the
prevailing trend. Output is a dark-themed price/volume chart plus a metrics
panel (current price, period high/low, trend direction, signal counts, last
CHoCH).

Architecture is a Flask app (`app.py`) over an analysis module (`analyzer.py`),
displayed in a native window via pywebview (`main.py`). The chart is rendered
server-side by matplotlib and passed to the page as a base64 PNG.

## Running it on this system

The app runs from a virtualenv in the project directory:

```
.venv/bin/python main.py
```

That opens the native window. Nothing is installed system-wide and there is no
desktop entry — launch it from the project directory.

To run just the web app in a browser instead, skipping the native window:

```
.venv/bin/python app.py     # http://127.0.0.1:5000, debug mode
```

### Recreating the venv

The venv **must** be created with `--system-site-packages`. pywebview's GTK
backend needs the system `gi` (PyGObject) and `webkit2gtk-4.1` bindings, which
are Arch packages rather than pip installs and are not otherwise visible from
inside a venv.

```
uv venv --system-site-packages --python 3.14 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt pywebview
```

Note the explicit `pywebview` on that second line. **`requirements.txt` does not
list it**, despite `main.py` importing it — installing from the file alone gives
you an app that dies on startup with `ModuleNotFoundError: No module named
'webview'`.

On startup pywebview logs `[pywebview] QT cannot be loaded` before falling back
to the GTK backend (`gtkwebkit2`). This is normal: it probes Qt first, finds no
`qtpy` in the venv, and moves on. The app works. Installing `qtpy` would silence
it and switch to the Qt6 backend, which is also available on this machine.

## Packaging

`setup.py` is a **py2app** config and only builds macOS `.app` bundles — it does
not work on Linux, and `setup_requires=['py2app']` will not even resolve here.
It is a leftover from the project's origin on a Mac (see also `__MACOSX/` and
`Archiv.zip`). Related: `app.py` branches on `sys.frozen` to locate templates
two levels above the executable, which is the py2app bundle layout. That branch
is dead code when running from source and only matters if the app is ever
bundled.

If a Linux launcher is wanted later, the equivalent is a `.desktop` entry in
`~/.local/share/applications/` pointing at `.venv/bin/python main.py`, not
anything derived from `setup.py`.

## HTTP endpoints

| Route              | Method | Purpose                                                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| `/`                | GET    | The UI                                                               |
| `/analyze`         | POST   | JSON in/out: `ticker`, `period`, `interval`, `window`, `currency`     |
| `/interval-limits` | GET    | Max lookback period Yahoo allows per interval, e.g. `1m` → `7d`      |

`window` is the swing-detection lookback (1–20, default 3): a bar is a swing high
if its high is the maximum across `window` bars either side of it. Larger values
find fewer, more significant swings.

## Caveats

Yahoo Finance caps how far back intraday data goes — one-minute bars only reach
7 days, most other intraday intervals 60 days. `/interval-limits` reports the
ceiling for each, and the UI uses it to constrain the period selector.

Currency conversion fetches the live `USD<CCY>=X` pair and multiplies the OHLC
columns by the latest rate. Two things follow from that: the whole history is
converted at *today's* rate rather than each bar's historical rate, so converted
charts distort past prices; and only EUR gets a proper `€` symbol — every other
non-USD currency converts correctly but is still labelled `$`.

The app requires network access at analysis time. There is no caching, so each
request re-downloads from Yahoo.
