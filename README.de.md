# Stock Analyzer

*[English version](README.md)*

Gib ein Börsenkürzel ein — `AAPL`, `MSFT`, `TSLA` — und diese App holt sich den
jüngsten Kursverlauf von Yahoo Finance und zeichnet ihn als Chart, wobei sie die
Stellen markiert, an denen der Kurs die Richtung gewechselt hat.

Sie sucht nach zwei Arten von Wendepunkten:

- **BOS** (Break of Structure, Strukturbruch) — der Kurs hat sein vorheriges Hoch
  oder Tief durchbrochen. Meist ein Zeichen dafür, dass der aktuelle Trend
  anhält.
- **CHoCH** (Change of Character, Charakterwechsel) — der Kurs ist in die
  *entgegengesetzte* Richtung ausgebrochen. Ein frühes Anzeichen dafür, dass der
  Trend drehen könnte.

Neben dem Chart siehst du den aktuellen Kurs, das Hoch und das Tief des
Zeitraums, in welche Richtung der Trend läuft und wie viele Signale gefunden
wurden.

Die App läuft auf deinem eigenen Rechner und öffnet sich in deinem Webbrowser.
Für das Abrufen der Kurse braucht sie eine Internetverbindung.

> Dies ist ein Hobbyprojekt zum Betrachten von Charts, keine Anlageberatung.
> Triff auf dieser Grundlage keine finanziellen Entscheidungen.

Es gibt zwei Wege, die App zu starten. **Der einfachere ist, eine fertige Datei
herunterzuladen** — kein Python, keine Einrichtung — beschrieben im zweiten
Abschnitt weiter unten.

Bauanleitung, die HTTP-API und bekannte Einschränkungen stehen in
[TECHNICAL.de.md](TECHNICAL.de.md).

## Aus dem Quellcode starten

Du brauchst [Python](https://www.python.org/downloads/) 3.13 und
[uv](https://docs.astral.sh/uv/getting-started/installation/), ein Werkzeug zum
Einrichten von Python-Projekten. Dann in einem Terminal in diesem Ordner:

```
uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt
.venv/bin/python main.py
```

Die ersten beiden Befehle legen einen abgeschotteten Ordner für die
Abhängigkeiten der App an und laden diese herunter; du brauchst sie nur einmal.
Der dritte startet die App: Sie gibt eine URL aus und öffnet deinen Browser. Mit
Strg-C im Terminal beendest du sie.

Es wird nichts systemweit installiert, und das Löschen des Ordners `.venv` macht
alles wieder rückgängig.

## Eine fertige Programmdatei starten

Fertige Downloads für Windows, macOS und Linux hängen an jedem
[Release](../../releases). Es muss nichts installiert werden — kein Python,
keine Einrichtung. Die Programmdatei startet die App, öffnet deinen Browser und
läuft weiter, bis du sie beendest.

**Die Downloads für macOS und Windows sind nicht signiert**, weshalb beide
Systeme sie beim ersten Mal blockieren. Die Datei ist völlig in Ordnung — es
bedeutet nur, dass niemand für ein Signaturzertifikat bezahlt hat. So kommst du
jeweils daran vorbei.

### Windows

Lade `stock-analyzer-windows-x86_64.exe` herunter und doppelklicke sie.

SmartScreen meldet **„Der Computer wurde durch Windows geschützt“**. Klicke auf
**Weitere Informationen** und dann auf **Trotzdem ausführen**. Windows merkt sich
das, es ist also ein einmaliger Schritt.

Ein Konsolenfenster öffnet sich und gibt die URL aus, dann folgt dein Browser.
Lass dieses Fenster offen, solange du die App benutzt — es zu schließen oder dort
Strg-C zu drücken, beendet sie.

Manche Antivirenprogramme stufen Dateien dieser Art als verdächtig ein. Das ist
ein bekannter Fehlalarm: Selbstentpackende Programme und Malware-Packer sehen für
automatische Scanner ähnlich aus. Nimm die Datei in die Ausnahmeliste auf oder
starte die App stattdessen aus dem Quellcode.

### macOS

Lade `stock-analyzer-macos-arm64` herunter.

**Nur für Macs mit Apple Silicon** (M1 und neuer). Auf einem älteren Intel-Mac
läuft die Datei nicht, und Rosetta hilft dabei nicht — starte dort stattdessen
aus dem Quellcode.

Heruntergeladene Dateien haben zunächst keine Ausführrechte. Öffne also das
Terminal, wechsle mit `cd` in deinen Download-Ordner und setze sie:

```
chmod +x stock-analyzer-macos-arm64
./stock-analyzer-macos-arm64
```

macOS blockiert den ersten Start mit dem Hinweis, der Entwickler könne nicht
verifiziert werden. Öffne **Systemeinstellungen → Datenschutz & Sicherheit**,
scrolle zu der Meldung, die die Datei nennt, und klicke auf **Trotzdem öffnen**.
Führe dann den obigen Befehl erneut aus.

Das Terminal-Fenster gibt die URL aus und öffnet deinen Browser. Strg-C dort
beendet die App.
