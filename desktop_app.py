#!/usr/bin/env python3
"""
Watch Auction - Desktop Application

A native desktop application for searching watch auctions.
Uses PyWebView to create a native window with the Flask web interface.
"""

import sys
import threading
import webview
from app import app

def run_flask():
    """Run Flask server in a separate thread."""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def main():
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Create native window
    window = webview.create_window(
        title='Watch Auction - Pesquisa de Leilões',
        url='http://127.0.0.1:5000',
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        text_select=True
    )

    # Start the GUI (blocks until window is closed)
    webview.start()

if __name__ == '__main__':
    main()
