from setuptools import setup

APP = ['main.py']
DATA_FILES = [('templates', ['templates/index.html'])]
OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'flask',
        'jinja2',
        'werkzeug',
        'yfinance',
        'pandas',
        'numpy',
        'matplotlib',
        'webview',
        'PIL',
        'certifi',
        'requests',
        'urllib3',
        'charset_normalizer',
        'multitasking',
        'peewee',
        'pytz',
        'dateutil',
    ],
    'includes': ['analyzer', 'app', 'cmath'],
    'plist': {
        'CFBundleName': 'Stock Analyzer',
        'CFBundleDisplayName': 'Stock Analyzer',
        'CFBundleIdentifier': 'com.local.stock-analyzer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
