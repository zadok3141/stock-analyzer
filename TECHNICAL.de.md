# Technische Hinweise

*[English version](TECHNICAL.md)*

Details zu Build, API und Verhalten des Stock Analyzer. Wenn du die App einfach
nur starten willst, siehe die [README](README.de.md); für noch nicht umgesetzte
Möglichkeiten, sie als Webdienst zu betreiben, siehe
[DEPLOYMENT.md](DEPLOYMENT.md) (nur auf Englisch).

## Architektur

Eine Flask-App (`app.py`) über einem Analysemodul (`analyzer.py`). `main.py`
startet diesen Server auf einem freien lokalen Port und öffnet die Seite im
Standardbrowser. Der Chart wird serverseitig von matplotlib (Backend `Agg`)
gerendert und als base64-kodiertes PNG an die Seite übergeben.

Um die Flask-App direkt im Debug-Modus auf einem festen Port zu starten und
`main.py` zu überspringen:

```
.venv/bin/python app.py     # http://127.0.0.1:5000
```

## Paketierung

Die App wird mit **PyInstaller** zu einer einzigen, eigenständigen ausführbaren
Datei gebündelt. Jede Abhängigkeit — der CPython-Interpreter, Flask, pandas,
numpy, matplotlib und die kompilierte HTTP-Schicht `curl_cffi` von yfinance —
steckt fest in der Programmdatei. Auf dem Zielrechner werden weder Python noch
site-packages benötigt.

```
uv venv --python 3.13 .venv-build          # sauber: NICHT --system-site-packages
VIRTUAL_ENV=.venv-build uv pip install -r requirements.txt pyinstaller
.venv-build/bin/pyinstaller --noconfirm stock-analyzer.spec
python scripts/smoke_test.py dist/stock-analyzer
```

Das Ergebnis landet in `dist/stock-analyzer` (~70 MB).

Gesteuert wird der Build über `stock-analyzer.spec` statt über
Kommandozeilenoptionen, weil `--add-data` unter Linux/macOS `:` als Trennzeichen
erwartet und unter Windows `;` — die Tupel in der Spec-Datei bedeuten überall
dasselbe. Drei Dinge darin sind tragend:

- **Das Build-venv muss sauber sein.** Verwende kein `--system-site-packages`,
  sonst zieht PyInstaller System-Pakete von Arch mit in das Bundle.
- `('templates', 'templates')` liefert `index.html` mit aus. Lässt man es weg,
  bricht PyInstaller den Build rundheraus ab — und das ist der gute Fall, denn so
  kann kein Bundle entstehen, das stillschweigend zur Laufzeit 500er wirft.
- `collect_data_files('yfinance')` und `collect_data_files('certifi')` liefern
  die Datendateien von yfinance und das TLS-CA-Bundle mit. Ohne sie scheitern
  Live-Anfragen an der Zertifikatsprüfung.

`scripts/smoke_test.py` startet eine gebaute Programmdatei und prüft, ob sie
tatsächlich ausliefert — ein Bundle kann fehlerfrei kompilieren und trotzdem zur
Laufzeit scheitern, und genau das fängt dieser Test ab. Er testet nur Routen ohne
Netzzugriff; `/analyze` ist ausgenommen, damit die CI nicht davon abhängt, dass
Yahoo erreichbar ist.

`app.py` verzweigt anhand von `sys.frozen`, um den Template-Ordner aus
`sys._MEIPASS` aufzulösen — dorthin entpackt PyInstaller gebündelte Daten zur
Laufzeit. Beim Start aus dem Quellcode ist dieser Zweig wirkungslos.

### Plattformübergreifende Builds

**PyInstaller kann nicht cross-kompilieren.** Die Programmdatei enthält ein
natives CPython sowie plattformspezifisch kompilierte Wheels (numpy, pandas,
matplotlib, curl_cffi); ein Linux-Build ist also eine ELF-Datei und läuft weder
unter macOS noch unter Windows. Alle drei zu erzeugen heißt, denselben Build auf
allen drei Betriebssystemen laufen zu lassen.

Genau das tut `.github/workflows/build.yml`: eine Matrix über `ubuntu-latest`,
`macos-latest` (Apple Silicon) und `windows-latest`, die jeweils den Spec-Build
und anschließend den Smoke-Test ausführt und pro Plattform ein Artefakt
hochlädt. Der Workflow läuft bei Pushes und PRs auf `main` und lässt sich im
Reiter „Actions“ von Hand auslösen.

Das Pushen eines `v*`-Tags veröffentlicht zusätzlich ein GitHub-Release mit allen
drei Programmdateien im Anhang:

```
git tag v1.0.0 && git push origin v1.0.0
```

Die Linux-Datei bindet nur `libc`, `libz`, `libpthread` und `libdl` ein, mit
GLIBC-Untergrenze 2.14, und läuft damit praktisch auf jeder modernen
Distribution.

Unsignierte Programmdateien werden auf den beiden anderen Plattformen
standardmäßig blockiert: macOS Gatekeeper verlangt eine ausdrückliche
Bestätigung, solange die Datei nicht signiert und notarisiert ist (dafür braucht
es einen Apple-Developer-Account), und Windows SmartScreen warnt, solange die
`.exe` nicht signiert ist.

### Warum es kein natives Fenster gibt

Die App öffnete früher ein natives Fenster über **pywebview** (und `setup.py` war
eine nur unter macOS lauffähige **py2app**-Konfiguration, inzwischen entfernt —
zusammen mit `Archiv.zip` und den `__MACOSX/`-Überbleibseln aus der Zeit, als das
Projekt auf einem Mac entstand).

pywebview wurde fallen gelassen, weil sein GTK-Backend unter Linux an
`webkit2gtk-4.1` und das systemweite `gi` (PyGObject) bindet — Arch-Pakete, keine
pip-Installationen. Das zwang das Entwicklungs-venv zu `--system-site-packages`
und machte ein eigenständiges Linux-Bundle unpraktikabel. Stattdessen den
Standardbrowser zu öffnen, kostet einen nativen Fensterrahmen und beseitigt die
gesamte Abhängigkeit von Systembibliotheken — übrig bleibt ein identisches
Build-Rezept auf allen drei Plattformen.

Sollte je wieder ein natives Fenster speziell für Linux gewünscht sein, ist das
richtige Mittel ein Flatpak, das die GNOME-Runtime deklariert und `webkit2gtk`
sauber mitbringt — nicht PyInstaller.

## HTTP-Endpunkte

| Route              | Methode | Zweck                                                                       |
| ------------------ | ------- | --------------------------------------------------------------------------- |
| `/`                | GET     | Die Oberfläche                                                              |
| `/analyze`         | POST    | JSON rein/raus: `ticker`, `period`, `interval`, `window`, `currency`         |
| `/interval-limits` | GET     | Maximaler Rückblickzeitraum, den Yahoo je Intervall erlaubt, z. B. `1m` → `7d` |

`window` ist der Rückblick für die Swing-Erkennung (1–20, Standard 3): Ein Balken
gilt als Swing-Hoch, wenn sein Hoch das Maximum über `window` Balken auf jeder
Seite ist. Größere Werte finden weniger, dafür bedeutsamere Swings.

## Einschränkungen

Yahoo Finance begrenzt, wie weit Intraday-Daten zurückreichen — Ein-Minuten-Balken
nur 7 Tage, die meisten anderen Intraday-Intervalle 60 Tage. `/interval-limits`
meldet die jeweilige Obergrenze, und die Oberfläche schränkt damit die Auswahl
des Zeitraums ein.

Die Währungsumrechnung holt das aktuelle Paar `USD<CCY>=X` und multipliziert die
OHLC-Spalten mit dem neuesten Kurs. Daraus folgen zwei Dinge: Der gesamte
Verlauf wird zum *heutigen* Kurs umgerechnet statt zum jeweils historischen Kurs
jedes Balkens, umgerechnete Charts verzerren also vergangene Kurse; und nur EUR
bekommt ein korrektes `€`-Symbol — jede andere Nicht-USD-Währung wird zwar
richtig umgerechnet, aber weiterhin mit `$` beschriftet.

Die App benötigt zum Analysezeitpunkt Netzwerkzugriff. Es gibt kein Caching, jede
Anfrage lädt also erneut von Yahoo herunter.
