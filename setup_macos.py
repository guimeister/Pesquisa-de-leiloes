"""
Setup script for building macOS application using py2app.

Usage:
    python setup_macos.py py2app
"""

from setuptools import setup

APP = ['desktop_app.py']
DATA_FILES = [
    ('templates', [
        'templates/base.html',
        'templates/index.html',
        'templates/detail.html',
        'templates/scraper.html',
        'templates/404.html',
    ]),
    ('static', [
        'static/style.css',
    ]),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icon.icns',  # Optional: add your icon
    'plist': {
        'CFBundleName': 'Watch Auction',
        'CFBundleDisplayName': 'Watch Auction',
        'CFBundleIdentifier': 'com.watchauction.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
    'packages': [
        'flask',
        'jinja2',
        'werkzeug',
        'webview',
        'src',
    ],
    'includes': [
        'src.database',
        'src.models',
        'src.parser',
        'src.scraper',
    ],
}

setup(
    name='Watch Auction',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
