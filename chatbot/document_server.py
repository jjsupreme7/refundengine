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
from urllib.parse import unquote

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)

# Base directory for documents
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"

# Security: Only serve PDF files
ALLOWED_EXTENSIONS = {'.pdf'}

# File index cache: {filename: Path}
# Built at startup to avoid rglob() on every request
FILE_INDEX = {}


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
        filename: URL-encoded filename (e.g., "WAC 458-20-100.pdf")

    Security:
        - URL-decodes filename only (no secure_filename mutation)
        - Validates extension (PDF-only whitelist)
        - Uses Path.resolve().relative_to() to prevent directory traversal
        - Only serves files from knowledge_base directory
    """

    # Decode URL-encoded filename
    filename = unquote(filename)

    if not filename or filename.strip() == '':
        abort(400, description="Invalid filename")

    # Security check: validate extension BEFORE file lookup
    # This prevents information disclosure of non-PDF files
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        app.logger.warning(f"Blocked request for non-PDF file: {filename} (extension: {file_ext})")
        abort(403, description="Only PDF files are served")

    # Search for the file in knowledge_base directory using cached index
    file_path = find_file_in_knowledge_base(filename)

    if not file_path:
        abort(404, description=f"File not found: {filename}")

    # Verify file exists and is within knowledge_base directory
    if not file_path.exists():
        abort(404, description="File not found")

    # Security check: ensure file is within knowledge_base directory
    # This prevents directory traversal attacks
    try:
        file_path.resolve().relative_to(KNOWLEDGE_BASE_DIR.resolve())
    except ValueError:
        # File is outside knowledge_base directory - security violation
        app.logger.warning(f"Path traversal attempt blocked: {file_path}")
        abort(403, description="Access denied")

    # Double-check extension of resolved file (defense in depth)
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        app.logger.warning(f"Blocked resolved file with non-PDF extension: {file_path}")
        abort(403, description="Only PDF files are served")

    # Send file
    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=False,  # Display in browser if possible
        download_name=filename
    )


def find_file_in_knowledge_base(filename: str) -> Path:
    """
    Search for a file in the knowledge_base directory using cached index

    Args:
        filename: Filename to search for (case-sensitive)

    Returns:
        Path object if found, None otherwise

    Note:
        This function uses the FILE_INDEX cache built at startup,
        avoiding expensive rglob() calls on every request.
    """
    # Use cached index for O(1) lookup instead of O(n) filesystem search
    return FILE_INDEX.get(filename)


def build_file_index():
    """
    Build an index of all PDF files in the knowledge_base directory

    This function is called once at startup to create a filename->Path
    lookup table, eliminating the need for expensive rglob() calls
    on every request.

    Security:
        - Only indexes files with extensions in ALLOWED_EXTENSIONS
        - Prevents DoS attacks via repeated filesystem searches

    Returns:
        Number of files indexed
    """
    global FILE_INDEX
    FILE_INDEX.clear()

    # Recursively find all allowed files
    for ext in ALLOWED_EXTENSIONS:
        pattern = f"**/*{ext}"
        for file_path in KNOWLEDGE_BASE_DIR.rglob(pattern):
            if file_path.is_file():
                # Index by filename only (not full path)
                filename = file_path.name

                # Handle duplicate filenames by keeping the first one found
                if filename not in FILE_INDEX:
                    FILE_INDEX[filename] = file_path
                else:
                    # Log warning about duplicate
                    existing = FILE_INDEX[filename]
                    app.logger.warning(
                        f"Duplicate filename found: {filename}\n"
                        f"  Existing: {existing}\n"
                        f"  Duplicate: {file_path}\n"
                        f"  Keeping existing entry."
                    )

    return len(FILE_INDEX)


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
    print(f"Allowed Extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    print()

    # Build file index at startup (prevents DoS via rglob on every request)
    print("Building file index...")
    try:
        num_files = build_file_index()
        print(f"✓ Indexed {num_files} files")
    except Exception as e:
        print(f"❌ Error building file index: {e}")
        sys.exit(1)

    print()
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
