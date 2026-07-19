# Stock Analyzer

Type in a stock ticker — `AAPL`, `MSFT`, `TSLA` — and this app fetches its recent
price history from Yahoo Finance and draws a chart of it, marking the points
where the price changed direction.

It looks for two kinds of turning point:

- **BOS** (Break of Structure) — price pushed past its previous peak or dip.
  Usually a sign the current trend is carrying on.
- **CHoCH** (Change of Character) — price broke the *opposite* way. An early hint
  the trend may be turning.

Next to the chart you get the current price, the high and low over the period,
which way the trend is running, and how many signals were found.

The app runs on your own machine and opens in your web browser. It needs an
internet connection to fetch prices.

> This is a hobby project for looking at charts, not financial advice. Do not
> make money decisions based on it.

There are two ways to run it. **Downloading a binary is the easier one** — no
Python or setup required — and is covered in the second section below.

Build instructions, the HTTP API, and known limitations live in
[TECHNICAL.md](TECHNICAL.md).

## Running from source

You need [Python](https://www.python.org/downloads/) 3.13 and
[uv](https://docs.astral.sh/uv/getting-started/installation/), a tool that sets
up Python projects. Then, in a terminal in this folder:

```
uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt
.venv/bin/python main.py
```

The first two commands create an isolated folder for the app's dependencies and
download them; you only need them once. The third starts the app: it prints a
URL and opens your browser. Press Ctrl-C in the terminal to quit.

Nothing is installed system-wide, and deleting the `.venv` folder undoes it all.

## Running a released binary

Ready-made downloads for Windows, macOS and Linux are attached to each
[release](../../releases). Nothing needs installing — no Python, no setup. The
binary starts the app, opens your browser, and keeps running until you stop it.

**The macOS and Windows downloads are unsigned**, so each system blocks them the
first time. Nothing is wrong with the file — it only means nobody has paid for a
signing certificate. Here is how to get past each.

### Windows

Download `stock-analyzer-windows-x86_64.exe` and double-click it.

SmartScreen shows **"Windows protected your PC"**. Click **More info**, then
**Run anyway**. Windows remembers this, so it is a one-time step.

A console window opens and prints the URL, then your browser follows. Keep that
window open while you use the app — closing it, or pressing Ctrl-C in it, quits.

Some antivirus tools flag this kind of file as suspicious. It is a known false
positive: self-extracting programs and malware packers look similar to automatic
scanners. Allow-list the file, or run from source instead.

### macOS

Download `stock-analyzer-macos-arm64`.

**Apple Silicon Macs only** (M1 and later). It will not run on an older Intel
Mac, and Rosetta does not help — on an Intel Mac, run from source instead.

Downloads arrive without permission to run, so open Terminal, `cd` to your
downloads folder, and set it:

```
chmod +x stock-analyzer-macos-arm64
./stock-analyzer-macos-arm64
```

macOS blocks the first launch, saying the developer cannot be verified. Open
**System Settings → Privacy & Security**, scroll down to the message naming the
file, and click **Open Anyway**. Then run the command above again.

The Terminal window prints the URL and opens your browser. Ctrl-C there quits.
