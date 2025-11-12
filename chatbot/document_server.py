#!/usr/bin/env python3
"""
Simple Document Server for Serving PDF Files

This Flask server provides secure file serving for PDF documents
referenced in the RAG chatbot. It validates file paths to prevent
directory traversal attacks.

Usage:
    python chatbot/document_server.py

    # Or run in background:
    python chatbot/document_server.py &

    # Stop:
    pkill -f document_server.py

Server runs on: http://localhost:5001
File endpoint: http://localhost:5001/documents/<filename>
"""

import os
import sys
from pathlib import Path
from flask import Flask, send_file, abort, jsonify
from werkzeug.utils import secure_filename
from urllib.parse import unquote

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)

# Base directory for documents
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'document-server',
        'version': '1.0.0'
    })


@app.route('/documents/<path:filename>', methods=['GET'])
def serve_document(filename):
    """
    Serve a document file securely

    Args:
        filename: URL-encoded filename (e.g., "WAC_458-20-100.pdf")

    Security:
        - Validates filename to prevent directory traversal
        - Only serves files from knowledge_base directory
        - Returns 404 for non-existent files
    """

    # Decode URL-encoded filename
    filename = unquote(filename)

    # Secure the filename (removes any path components)
    safe_filename = secure_filename(filename)

    if not safe_filename:
        abort(400, description="Invalid filename")

    # Search for the file in knowledge_base directory
    file_path = find_file_in_knowledge_base(safe_filename)

    if not file_path:
        abort(404, description=f"File not found: {filename}")

    # Verify file exists and is within knowledge_base directory
    if not file_path.exists():
        abort(404, description="File not found")

    # Security check: ensure file is within knowledge_base directory
    try:
        file_path.resolve().relative_to(KNOWLEDGE_BASE_DIR.resolve())
    except ValueError:
        # File is outside knowledge_base directory - security violation
        app.logger.warning(f"Attempted access to file outside knowledge_base: {file_path}")
        abort(403, description="Access denied")

    # Determine mimetype
    mimetype = get_mimetype(file_path)

    # Send file
    return send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=False,  # Display in browser if possible
        download_name=safe_filename
    )


def find_file_in_knowledge_base(filename: str) -> Path:
    """
    Search for a file in the knowledge_base directory tree

    Args:
        filename: Filename to search for

    Returns:
        Path object if found, None otherwise
    """

    # First, try exact match in common locations
    common_paths = [
        KNOWLEDGE_BASE_DIR / filename,
        KNOWLEDGE_BASE_DIR / "wa_tax_law" / filename,
        KNOWLEDGE_BASE_DIR / "vendors" / filename,
        KNOWLEDGE_BASE_DIR / "states" / "washington" / filename,
    ]

    for path in common_paths:
        if path.exists():
            return path

    # If not found, do a recursive search
    for path in KNOWLEDGE_BASE_DIR.rglob(filename):
        if path.is_file():
            return path

    return None


def get_mimetype(file_path: Path) -> str:
    """
    Get MIME type for a file based on extension

    Args:
        file_path: Path to file

    Returns:
        MIME type string
    """

    suffix = file_path.suffix.lower()

    mimetypes = {
        '.pdf': 'application/pdf',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.txt': 'text/plain',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    return mimetypes.get(suffix, 'application/octet-stream')


@app.errorhandler(404)
def not_found(error):
    """Custom 404 error handler"""
    return jsonify({
        'error': 'Not Found',
        'message': str(error.description)
    }), 404


@app.errorhandler(403)
def forbidden(error):
    """Custom 403 error handler"""
    return jsonify({
        'error': 'Forbidden',
        'message': str(error.description)
    }), 403


@app.errorhandler(400)
def bad_request(error):
    """Custom 400 error handler"""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description)
    }), 400


def main():
    """Run the document server"""

    # Check if knowledge_base directory exists
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"❌ Error: Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        print("   Please create the directory or adjust KNOWLEDGE_BASE_DIR")
        sys.exit(1)

    print("=" * 70)
    print("📄 Document Server Starting")
    print("=" * 70)
    print(f"Knowledge Base: {KNOWLEDGE_BASE_DIR}")
    print(f"Server URL: http://localhost:5001")
    print(f"Health Check: http://localhost:5001/health")
    print(f"File Endpoint: http://localhost:5001/documents/<filename>")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,  # Set to True for development
        threaded=True
    )


if __name__ == "__main__":
    main()
