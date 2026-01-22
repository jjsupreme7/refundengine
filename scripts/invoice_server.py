#!/usr/bin/env python3
"""
Simple HTTP server to serve invoices for Excel hyperlinks.
Run this, then Excel links like http://localhost:8888/filename.pdf will work.
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8888
INVOICE_DIR = Path.home() / "Desktop" / "Invoices"

class InvoiceHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(INVOICE_DIR), **kwargs)
    
    def log_message(self, format, *args):
        # Cleaner logging
        print(f"  → {args[0]}")

if __name__ == "__main__":
    os.chdir(INVOICE_DIR)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📄 Invoice Server Running                                    ║
║                                                              ║
║  Serving: {str(INVOICE_DIR):<40} ║
║  URL:     http://localhost:{PORT}/                             ║
║                                                              ║
║  Excel hyperlinks will now work!                             ║
║  Press Ctrl+C to stop.                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    with socketserver.TCPServer(("", PORT), InvoiceHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Server stopped")
