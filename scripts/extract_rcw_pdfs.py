#!/usr/bin/env python3
"""
Extract and download PDFs from Washington State RCW site
https://app.leg.wa.gov/rcw/default.aspx?Cite=82

This script:
1. Scrapes the RCW Title 82 page to find all chapters and sections
2. Downloads PDFs for each section
3. Saves them to knowledge_base/states/washington/legal_documents/rcw/

Note: The site may block automated requests. If that happens, this script
will provide instructions for manual download or use browser automation.
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
BASE_URL = "https://app.leg.wa.gov/rcw"
TITLE_82_URL = "https://app.leg.wa.gov/rcw/default.aspx?Cite=82"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base" / "states" / "washington" / "legal_documents" / "rcw"

# Request headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}


def fetch_page(url: str, retries: int = 3) -> str:
    """
    Fetch a webpage with retries and proper headers
    """
    for attempt in range(retries):
        try:
            print(f"  Fetching: {url}")
            session = requests.Session()
            response = session.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"  ⚠️  403 Forbidden - Site is blocking automated access")
                return None
            else:
                print(f"  ⚠️  Status {response.status_code}")

        except Exception as e:
            print(f"  ⚠️  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return None


def extract_chapters_from_title(html_content: str) -> list:
    """
    Extract all chapter links from Title 82 page
    Returns list of (chapter_num, chapter_url, chapter_title)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    chapters = []

    # Find all chapter links
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for chapter links (e.g., "Chapter 82.04")
        if 'Cite=' in href and re.search(r'Chapter\s+82\.\d+', text):
            chapter_match = re.search(r'82\.(\d+)', text)
            if chapter_match:
                chapter_num = chapter_match.group(0)  # e.g., "82.04"
                chapter_url = urljoin(BASE_URL, href)
                chapters.append((chapter_num, chapter_url, text))

    return chapters


def extract_sections_from_chapter(html_content: str, chapter_num: str) -> list:
    """
    Extract all section links from a chapter page
    Returns list of (section_num, section_url, section_title)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = []

    # Find all section links
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for section links (e.g., "82.04.010", "RCW 82.04.010")
        if 'Cite=' in href:
            section_match = re.search(r'82\.\d+\.\d+', text)
            if section_match:
                section_num = section_match.group(0)
                section_url = urljoin(BASE_URL, href)
                sections.append((section_num, section_url, text))

    return sections


def download_pdf(cite: str, output_path: Path) -> bool:
    """
    Download PDF for a specific RCW citation

    The PDF URL format is:
    https://app.leg.wa.gov/RCW/default.aspx?cite=82.04.010

    Then look for PDF download link
    """
    try:
        # First get the HTML page
        url = f"https://app.leg.wa.gov/RCW/default.aspx?cite={cite}"
        html = fetch_page(url)

        if not html:
            return False

        soup = BeautifulSoup(html, 'html.parser')

        # Look for PDF link (common patterns)
        pdf_link = None

        # Method 1: Look for explicit PDF links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '.pdf' in href.lower() or 'pdf' in link.get_text(strip=True).lower():
                pdf_link = urljoin(BASE_URL, href)
                break

        # Method 2: Look for document download links
        if not pdf_link:
            for link in soup.find_all('a', href=True):
                if 'document' in link.get('href', '').lower() or 'download' in link.get('href', '').lower():
                    pdf_link = urljoin(BASE_URL, link.get('href'))
                    break

        if not pdf_link:
            print(f"    ⚠️  No PDF link found for {cite}")
            return False

        # Download the PDF
        print(f"    Downloading PDF: {pdf_link}")
        response = requests.get(pdf_link, headers=HEADERS, timeout=30)

        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"    ✅ Saved: {output_path.name}")
            return True
        else:
            print(f"    ❌ Failed to download PDF: {response.status_code}")
            return False

    except Exception as e:
        print(f"    ❌ Error downloading PDF for {cite}: {e}")
        return False


def scrape_and_download(limit: int = None, delay: float = 1.0):
    """
    Main function to scrape RCW Title 82 and download all PDFs
    """
    print("\n" + "="*70)
    print("📚 Washington State RCW Title 82 PDF Extractor")
    print("="*70 + "\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}\n")

    # Step 1: Fetch Title 82 main page
    print("Step 1: Fetching RCW Title 82 page...")
    title_html = fetch_page(TITLE_82_URL)

    if not title_html:
        print("\n❌ Could not access the RCW site.")
        print("\n🔧 Alternative approaches:")
        print("  1. Manual download:")
        print("     - Visit: https://app.leg.wa.gov/rcw/default.aspx?Cite=82")
        print("     - Click each chapter and download PDFs manually")
        print("     - Save to:", OUTPUT_DIR)
        print("\n  2. Use browser automation (Selenium/Playwright):")
        print("     pip install selenium")
        print("     Then re-run this script with --selenium flag")
        return

    # Step 2: Extract chapters
    print("\nStep 2: Extracting chapters...")
    chapters = extract_chapters_from_title(title_html)
    print(f"✅ Found {len(chapters)} chapters in Title 82\n")

    if limit:
        chapters = chapters[:limit]
        print(f"⚠️  Limited to {limit} chapters\n")

    # Step 3: For each chapter, extract sections and download PDFs
    total_downloaded = 0
    total_failed = 0

    for i, (chapter_num, chapter_url, chapter_title) in enumerate(chapters, 1):
        print(f"\n{'='*70}")
        print(f"Chapter {i}/{len(chapters)}: {chapter_title}")
        print(f"{'='*70}")

        # Fetch chapter page
        chapter_html = fetch_page(chapter_url)
        if not chapter_html:
            print("  ❌ Could not fetch chapter page")
            total_failed += 1
            continue

        # Extract sections
        sections = extract_sections_from_chapter(chapter_html, chapter_num)
        print(f"  Found {len(sections)} sections")

        # Download PDFs for each section
        for section_num, section_url, section_title in sections:
            print(f"\n  Section: {section_title}")

            # Generate filename
            filename = f"RCW_{section_num.replace('.', '-')}.pdf"
            output_path = OUTPUT_DIR / filename

            # Skip if already exists
            if output_path.exists():
                print(f"    ⏭️  Already exists: {filename}")
                continue

            # Download
            success = download_pdf(section_num, output_path)
            if success:
                total_downloaded += 1
            else:
                total_failed += 1

            # Be nice to the server
            time.sleep(delay)

    # Summary
    print("\n" + "="*70)
    print("📊 EXTRACTION SUMMARY")
    print("="*70)
    print(f"✅ Downloaded: {total_downloaded} PDFs")
    print(f"❌ Failed: {total_failed}")
    print(f"📁 Location: {OUTPUT_DIR}")
    print("="*70 + "\n")

    if total_downloaded > 0:
        print("🔄 Next step: Ingest PDFs into knowledge base")
        print(f"\n  python scripts/ingest_documents.py \\")
        print(f"    --type tax_law \\")
        print(f"    --folder {OUTPUT_DIR} \\")
        print(f"    --export-metadata outputs/RCW_Title_82_Metadata.xlsx")
        print()


def list_existing_pdfs():
    """
    List PDFs already downloaded
    """
    if not OUTPUT_DIR.exists():
        print(f"❌ Directory not found: {OUTPUT_DIR}")
        return

    pdfs = list(OUTPUT_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No PDFs found in {OUTPUT_DIR}")
    else:
        print(f"\n📄 Found {len(pdfs)} PDFs in {OUTPUT_DIR}:\n")
        for pdf in sorted(pdfs):
            print(f"  - {pdf.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDFs from Washington State RCW Title 82",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all PDFs from RCW Title 82
  python scripts/extract_rcw_pdfs.py

  # Download only first 2 chapters (for testing)
  python scripts/extract_rcw_pdfs.py --limit 2

  # List already downloaded PDFs
  python scripts/extract_rcw_pdfs.py --list

  # Set delay between downloads (be nice to server)
  python scripts/extract_rcw_pdfs.py --delay 2.0
        """
    )

    parser.add_argument("--limit", type=int, help="Limit number of chapters to process")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between downloads (seconds)")
    parser.add_argument("--list", action="store_true", help="List existing downloaded PDFs")

    args = parser.parse_args()

    if args.list:
        list_existing_pdfs()
    else:
        scrape_and_download(limit=args.limit, delay=args.delay)


if __name__ == "__main__":
    main()
