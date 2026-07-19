# PyInstaller build spec. Used in preference to command-line flags because
# --add-data takes a ':' separator on Linux/macOS and ';' on Windows, whereas
# the tuples below mean the same thing on all three.
#
#   pyinstaller --noconfirm stock-analyzer.spec

from PyInstaller.utils.hooks import collect_data_files

datas = [('templates', 'templates')]
datas += collect_data_files('yfinance')   # yfinance's bundled data files
datas += collect_data_files('certifi')    # TLS CA bundle; live requests fail without it

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='stock-analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    # console=True is deliberate: the app prints its URL and stays in the
    # foreground until Ctrl-C. With console=False there is no way to read the
    # URL or stop the server.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
