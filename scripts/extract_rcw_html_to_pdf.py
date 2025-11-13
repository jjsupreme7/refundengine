#!/usr/bin/env python3
"""
Extract RCW Title 82 content from HTML and convert to PDF or text

This script:
1. Scrapes RCW Title 82 HTML pages
2. Extracts the legal text content
3. Converts to PDF using reportlab or saves as text
4. Saves to knowledge_base for ingestion

This is more practical than looking for PDFs that may not exist on the site.

Requirements:
    pip install beautifulsoup4 requests reportlab

Usage:
    # Extract as text files
    python scripts/extract_rcw_html_to_pdf.py --format text

    # Extract and convert to PDF
    python scripts/extract_rcw_html_to_pdf.py --format pdf

    # Test with limited chapters
    python scripts/extract_rcw_html_to_pdf.py --limit 2
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Tuple

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Load environment
load_dotenv()

# Configuration
BASE_URL = "https://app.leg.wa.gov/rcw"
TITLE_82_URL = "https://app.leg.wa.gov/rcw/default.aspx?Cite=82"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base" / "states" / "washington" / "legal_documents" / "rcw"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def fetch_page(url: str, retries: int = 3) -> str:
    """Fetch webpage with retries"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"  ⚠️  403 Forbidden")
                return None
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  ⚠️  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def extract_rcw_sections_list(html_content: str) -> List[Tuple[str, str, str]]:
    """
    Extract all RCW section references from Title 82 page
    Returns: [(section_number, url, title), ...]
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = []

    # Find all links with RCW citations
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Match RCW 82.XX.XXX patterns
        if 'Cite=' in href:
            match = re.search(r'82\.\d+\.?\d*', text)
            if match:
                section_num = match.group(0)
                full_url = urljoin(BASE_URL, href)
                sections.append((section_num, full_url, text))

    return sections


def extract_rcw_content(html_content: str, section_num: str) -> dict:
    """
    Extract the actual legal text content from an RCW section page

    Returns:
        {
            'section_number': '82.04.010',
            'title': 'Section Title',
            'content': 'Full legal text...',
            'history': 'Citation history...',
            'notes': 'Any notes or annotations'
        }
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    data = {
        'section_number': section_num,
        'title': '',
        'content': '',
        'history': '',
        'notes': ''
    }

    # Try to find the main content area
    # The exact structure varies, but typically there's a main content div

    # Method 1: Look for specific ID/class patterns common in WA Leg site
    main_content = (
        soup.find('div', {'id': 'rcwcontent'}) or
        soup.find('div', {'class': 'content'}) or
        soup.find('div', {'class': 'rcw'}) or
        soup.find('main') or
        soup.find('article')
    )

    if main_content:
        # Extract title (usually an h1 or h2)
        title_elem = main_content.find(['h1', 'h2', 'h3'])
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)

        # Extract main text content
        # Remove script, style, and nav elements
        for element in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # Get paragraphs
        paragraphs = main_content.find_all(['p', 'div'], recursive=True)
        content_parts = []

        for para in paragraphs:
            text = para.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short noise
                content_parts.append(text)

        data['content'] = '\n\n'.join(content_parts)

        # Look for history/notes sections
        history_elem = main_content.find(string=re.compile(r'NOTES|History|Source', re.I))
        if history_elem:
            parent = history_elem.find_parent()
            if parent:
                data['history'] = parent.get_text(strip=True)

    return data


def save_as_text(data: dict, output_path: Path):
    """Save RCW content as formatted text file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"{'='*70}\n")
        f.write(f"RCW {data['section_number']}\n")
        if data['title']:
            f.write(f"{data['title']}\n")
        f.write(f"{'='*70}\n\n")

        f.write(data['content'])

        if data['history']:
            f.write(f"\n\n{'='*70}\n")
            f.write("HISTORY AND NOTES\n")
            f.write(f"{'='*70}\n\n")
            f.write(data['history'])

    print(f"    ✅ Saved: {output_path.name}")


def save_as_pdf(data: dict, output_path: Path):
    """Save RCW content as PDF using reportlab"""
    if not REPORTLAB_AVAILABLE:
        print("    ⚠️  reportlab not available, saving as text instead")
        save_as_text(data, output_path.with_suffix('.txt'))
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='black',
        spaceAfter=30
    )
    content_style = styles['BodyText']

    story = []

    # Title
    story.append(Paragraph(f"RCW {data['section_number']}", title_style))
    if data['title']:
        story.append(Paragraph(data['title'], styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))

    # Content
    for para in data['content'].split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), content_style))
            story.append(Spacer(1, 0.1 * inch))

    # History
    if data['history']:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("History and Notes", styles['Heading2']))
        story.append(Paragraph(data['history'], content_style))

    doc.build(story)
    print(f"    ✅ Saved PDF: {output_path.name}")


def extract_all_rcw_sections(limit: int = None, output_format: str = 'text', delay: float = 1.0):
    """
    Main extraction function
    """
    print("\n" + "="*70)
    print("📚 Washington State RCW Title 82 Extractor")
    print("="*70 + "\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"📄 Format: {output_format}\n")

    # Step 1: Get main page
    print("Step 1: Fetching RCW Title 82 page...")
    title_html = fetch_page(TITLE_82_URL)

    if not title_html:
        print("\n❌ Could not access the site")
        print("\nAlternative: Manual download")
        print("  1. Visit each chapter at: https://app.leg.wa.gov/rcw/default.aspx?Cite=82")
        print("  2. Use browser 'Print to PDF' for each section")
        print(f"  3. Save PDFs to: {OUTPUT_DIR}")
        return

    # Step 2: Extract all section links
    print("\nStep 2: Extracting section links...")
    sections = extract_rcw_sections_list(title_html)
    print(f"✅ Found {len(sections)} RCW sections in Title 82\n")

    if limit:
        sections = sections[:limit]
        print(f"⚠️  Limited to {limit} sections\n")

    # Step 3: Download each section
    total_success = 0
    total_failed = 0

    for i, (section_num, section_url, section_title) in enumerate(sections, 1):
        print(f"\n[{i}/{len(sections)}] {section_title}")

        # Check if already exists
        if output_format == 'pdf':
            output_path = OUTPUT_DIR / f"RCW_{section_num.replace('.', '-')}.pdf"
        else:
            output_path = OUTPUT_DIR / f"RCW_{section_num.replace('.', '-')}.txt"

        if output_path.exists():
            print(f"    ⏭️  Already exists")
            continue

        # Fetch section page
        print(f"    Fetching: {section_url}")
        section_html = fetch_page(section_url)

        if not section_html:
            print(f"    ❌ Failed to fetch")
            total_failed += 1
            continue

        # Extract content
        content = extract_rcw_content(section_html, section_num)

        if not content['content']:
            print(f"    ⚠️  No content extracted")
            total_failed += 1
            continue

        # Save
        if output_format == 'pdf':
            save_as_pdf(content, output_path)
        else:
            save_as_text(content, output_path)

        total_success += 1

        # Be nice to the server
        time.sleep(delay)

    # Summary
    print("\n" + "="*70)
    print("📊 EXTRACTION SUMMARY")
    print("="*70)
    print(f"✅ Successfully extracted: {total_success}")
    print(f"❌ Failed: {total_failed}")
    print(f"📁 Location: {OUTPUT_DIR}")
    print("="*70 + "\n")

    if total_success > 0:
        print("🔄 Next step: Ingest into knowledge base")
        print(f"\n  python scripts/ingest_documents.py \\")
        print(f"    --type tax_law \\")
        print(f"    --folder {OUTPUT_DIR} \\")
        print(f"    --export-metadata outputs/RCW_Title_82_Metadata.xlsx\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract RCW Title 82 content and convert to PDF or text",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--format",
        choices=['pdf', 'text'],
        default='text',
        help="Output format (text recommended, pdf requires reportlab)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of sections (for testing)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds"
    )

    args = parser.parse_args()

    if args.format == 'pdf' and not REPORTLAB_AVAILABLE:
        print("⚠️  reportlab not installed. Install with: pip install reportlab")
        print("Falling back to text format...\n")
        args.format = 'text'

    extract_all_rcw_sections(
        limit=args.limit,
        output_format=args.format,
        delay=args.delay
    )


if __name__ == "__main__":
    main()
