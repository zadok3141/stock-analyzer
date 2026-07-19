# Stock Analyzer

A desktop app for technical market-structure analysis. Enter a ticker and it pulls
price history from Yahoo Finance, locates swing highs and lows, and detects
**BOS** (Break of Structure) and **CHoCH** (Change of Character) signals — the
points where price breaks a prior swing level, and where it does so against the
prevailing trend. Output is a dark-themed price/volume chart plus a metrics
panel (current price, period high/low, trend direction, signal counts, last
CHoCH).

Architecture is a Flask app (`app.py`) over an analysis module (`analyzer.py`).
`main.py` starts that server on a free local port and opens the page in your
default browser. The chart is rendered server-side by matplotlib (`Agg` backend)
and passed to the page as a base64 PNG.

## Running from source

Both the commands below and the packaging build use [uv](https://docs.astral.sh/uv/)
— see [installing uv](https://docs.astral.sh/uv/getting-started/installation/) if
you do not have it. Plain `python -m venv` and `pip` work equally well if you
prefer them.

```
uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt
.venv/bin/python main.py
```

That starts the server, opens a browser tab, and prints the URL. Ctrl-C to quit.
Nothing is installed system-wide.

To run the Flask app directly in debug mode on a fixed port instead:

```
.venv/bin/python app.py     # http://127.0.0.1:5000
```

## Running a released binary

Builds for all three platforms are attached to each [release](../../releases),
and every push to `main` also produces them as
[Actions artifacts](../../actions). Nothing needs installing — no Python, no
dependencies. The binary starts a local server, opens your browser, and prints
its URL; it keeps running until you stop it.

**Both the macOS and Windows binaries are unsigned**, so each operating system
blocks them on first launch. Neither warning indicates anything is wrong with
the file — they mean nobody has paid for a signing certificate. The steps below
are the standard way past each.

### Windows

Download `stock-analyzer-windows-x86_64.exe` (64-bit Intel/AMD; Windows on ARM
is not built).

Double-click it. SmartScreen will show **"Windows protected your PC"** — click
**More info**, then **Run anyway**. Windows remembers the choice, so this is a
one-time step per downloaded copy.

A console window opens, prints the URL, and your browser follows. Leave the
console open while you use the app; closing it, or pressing Ctrl-C in it, quits
the server.

Some antivirus products flag PyInstaller executables as suspicious. This is a
well-known false positive — self-extracting binaries and malware packers look
alike to heuristic scanners. If your scanner quarantines it, either allow-list
the file or build from source instead.

### macOS

Download `stock-analyzer-macos-arm64`.

**Apple Silicon only.** The release binary is built on an arm64 runner and will
not run on an Intel Mac — Rosetta does not help, as it translates Intel to ARM
and not the reverse. On an Intel Mac, run from source or build your own binary
there.

The download arrives without the executable bit, so set it first:

```
chmod +x stock-analyzer-macos-arm64
```

Then launch it from Terminal:

```
./stock-analyzer-macos-arm64
```

Gatekeeper will refuse the first launch, reporting that the developer cannot be
verified. Two ways past it:

- Open **System Settings → Privacy & Security**, scroll to the message naming
  the blocked binary, and click **Open Anyway**. This is the reliable route on
  current macOS.
- Or strip the quarantine attribute the browser attached on download:

  ```
  xattr -d com.apple.quarantine stock-analyzer-macos-arm64
  ```

Older instructions suggest right-clicking and choosing Open. That bypass has
been progressively restricted in recent macOS versions, so prefer the two
methods above.

Once running, the Terminal window prints the URL and opens your browser. Ctrl-C
in that window quits the server.

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
Gatekeeper requires a right-click-open until the `.app` is signed and notarised
(Apple Developer account), and Windows SmartScreen warns until the `.exe` is
signed.

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
