# Technical notes

*[Deutsche Fassung](TECHNICAL.de.md)*

Build, API and behaviour details for Stock Analyzer. See [README](README.md) to
just run the app, and [DEPLOYMENT.md](DEPLOYMENT.md) for unimplemented options
for hosting it as a web service.

## Architecture

A Flask app (`app.py`) over an analysis module (`analyzer.py`). `main.py` starts
that server on a free local port and opens the page in the default browser. The
chart is rendered server-side by matplotlib (`Agg` backend) and passed to the
page as a base64 PNG.

To run the Flask app directly in debug mode on a fixed port, skipping `main.py`:

```
.venv/bin/python app.py     # http://127.0.0.1:5000
```

## Packaging

The app is bundled with **PyInstaller** into a single self-contained executable.
Every dependency — the CPython interpreter, Flask, pandas, numpy, matplotlib,
and yfinance's compiled `curl_cffi` HTTP layer — is baked into the binary. It
has no Python and no site-packages requirement on the target machine.

```
uv venv --python 3.13 .venv-build          # clean: NOT --system-site-packages
VIRTUAL_ENV=.venv-build uv pip install -r requirements.txt pyinstaller
.venv-build/bin/pyinstaller --noconfirm stock-analyzer.spec
python scripts/smoke_test.py dist/stock-analyzer
```

Output lands in `dist/stock-analyzer` (~70 MB).

The build is driven by `stock-analyzer.spec` rather than command-line flags,
because `--add-data` takes a `:` separator on Linux/macOS and `;` on Windows —
the spec's tuples mean the same thing everywhere. Three things in it are
load-bearing:

- **The build venv must be clean.** Do not use `--system-site-packages`, or
  PyInstaller will sweep system Arch packages into the bundle.
- `('templates', 'templates')` ships `index.html`. Leave it out and PyInstaller
  fails the build outright, which is the good case — it cannot silently produce
  a bundle that 500s at runtime.
- `collect_data_files('yfinance')` and `collect_data_files('certifi')` ship
  yfinance's data files and the TLS CA bundle. Without them, live requests fail
  on certificate verification.

`scripts/smoke_test.py` launches a built binary and checks it actually serves —
a bundle can compile and still fail at runtime, and this is what catches that.
It exercises only offline routes; `/analyze` is excluded so CI does not depend
on Yahoo being reachable.

`app.py` branches on `sys.frozen` to resolve the template folder out of
`sys._MEIPASS`, which is where PyInstaller unpacks bundled data at runtime. That
branch is inert when running from source.

### Cross-platform builds

**PyInstaller does not cross-compile.** The binary embeds a native CPython plus
platform-specific compiled wheels (numpy, pandas, matplotlib, curl_cffi), so a
Linux build is an ELF binary and will not run on macOS or Windows. Producing all
three means running the same build on all three operating systems.

`.github/workflows/build.yml` does exactly that: a matrix over `ubuntu-latest`,
`macos-latest` (Apple Silicon) and `windows-latest`, each running the spec build
and then the smoke test, uploading one artifact per platform. It runs on pushes
and PRs to `main`, and can be triggered by hand from the Actions tab.

Pushing a `v*` tag additionally publishes a GitHub release with all three
binaries attached:

```
git tag v1.0.0 && git push origin v1.0.0
```

The Linux binary links only `libc`, `libz`, `libpthread` and `libdl`, with a
GLIBC floor of 2.14, so it runs on effectively any modern distribution.

Unsigned binaries are blocked by default on the other two platforms: macOS
Gatekeeper requires an explicit override until the binary is signed and
notarised (Apple Developer account), and Windows SmartScreen warns until the
`.exe` is signed.

### Why there is no native window

The app previously opened a native window via **pywebview** (and `setup.py` was
a macOS-only **py2app** config, now removed along with the `Archiv.zip` and
`__MACOSX/` leftovers from the project's origin on a Mac).

pywebview was dropped because its Linux GTK backend binds to `webkit2gtk-4.1`
and the system `gi` (PyGObject) — Arch packages, not pip installs. That forced
the dev venv to use `--system-site-packages` and made a self-contained Linux
bundle impractical. Opening the default browser instead costs a native window
frame and removes the entire system-library dependency, leaving one identical
build recipe on all three platforms.

If a native window is ever wanted back on Linux specifically, the right vehicle
is a Flatpak declaring the GNOME runtime, which supplies `webkit2gtk` properly —
not PyInstaller.

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
