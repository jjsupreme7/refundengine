#!/usr/bin/env python3
"""
Extract and download PDFs from Washington State RCW site using Selenium
(Browser automation to bypass 403 restrictions)

This script uses Selenium to automate a real browser, which can bypass
anti-bot protections that block simple HTTP requests.

Requirements:
    pip install selenium
    pip install webdriver-manager

Usage:
    python scripts/extract_rcw_pdfs_selenium.py
    python scripts/extract_rcw_pdfs_selenium.py --limit 2  # Test with 2 chapters
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin
from dotenv import load_dotenv

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Install with: pip install selenium webdriver-manager")

# Load environment
load_dotenv()

# Configuration
TITLE_82_URL = "https://app.leg.wa.gov/rcw/default.aspx?Cite=82"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base" / "states" / "washington" / "legal_documents" / "rcw"


def setup_driver(headless: bool = True):
    """
    Setup Chrome driver with Selenium
    """
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless")

    # Additional options to avoid detection
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Set download directory
    prefs = {
        "download.default_directory": str(OUTPUT_DIR.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Setup driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def extract_chapters_with_selenium(driver) -> list:
    """
    Extract all chapter links from Title 82 page using Selenium
    Returns list of (chapter_num, chapter_url, chapter_title)
    """
    print(f"  Loading: {TITLE_82_URL}")
    driver.get(TITLE_82_URL)

    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Give it a moment for dynamic content
    time.sleep(2)

    chapters = []

    # Find all links
    links = driver.find_elements(By.TAG_NAME, "a")

    for link in links:
        try:
            href = link.get_attribute("href")
            text = link.text.strip()

            # Look for chapter links
            if href and 'Cite=' in href and re.search(r'Chapter\s+82\.\d+', text):
                chapter_match = re.search(r'82\.(\d+)', text)
                if chapter_match:
                    chapter_num = chapter_match.group(0)
                    chapters.append((chapter_num, href, text))
        except:
            continue

    return chapters


def extract_sections_with_selenium(driver, chapter_url: str, chapter_num: str) -> list:
    """
    Extract all section links from a chapter page
    Returns list of (section_num, section_url, section_title)
    """
    driver.get(chapter_url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    time.sleep(1)

    sections = []
    links = driver.find_elements(By.TAG_NAME, "a")

    for link in links:
        try:
            href = link.get_attribute("href")
            text = link.text.strip()

            if href and 'Cite=' in href:
                section_match = re.search(r'82\.\d+\.\d+', text)
                if section_match:
                    section_num = section_match.group(0)
                    sections.append((section_num, href, text))
        except:
            continue

    return sections


def download_section_as_pdf(driver, section_url: str, section_num: str, output_path: Path) -> bool:
    """
    Navigate to section page and download as PDF

    Note: This attempts to find a PDF/download button on the page.
    If none exists, we may need to use the browser's print-to-PDF feature.
    """
    try:
        print(f"    Loading: {section_url}")
        driver.get(section_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(1)

        # Try to find PDF link
        pdf_found = False
        links = driver.find_elements(By.TAG_NAME, "a")

        for link in links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text.strip().lower()

                if '.pdf' in href or 'pdf' in text or 'download' in text:
                    print(f"    Clicking PDF link: {text}")
                    link.click()
                    time.sleep(2)  # Wait for download
                    pdf_found = True
                    break
            except:
                continue

        if not pdf_found:
            print(f"    ⚠️  No PDF link found - may need manual print-to-PDF")
            return False

        # Check if file was downloaded
        # (This is tricky - may need to check download directory for new files)

        return True

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False


def scrape_with_selenium(limit: int = None, headless: bool = True):
    """
    Main function using Selenium
    """
    if not SELENIUM_AVAILABLE:
        print("\n❌ Selenium is not installed.")
        print("Install with: pip install selenium webdriver-manager")
        return

    print("\n" + "="*70)
    print("📚 Washington State RCW Title 82 PDF Extractor (Selenium)")
    print("="*70 + "\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}\n")

    # Setup driver
    print("🌐 Starting Chrome browser...")
    driver = setup_driver(headless=headless)

    try:
        # Step 1: Get chapters
        print("\nStep 1: Extracting chapters from Title 82...")
        chapters = extract_chapters_with_selenium(driver)
        print(f"✅ Found {len(chapters)} chapters\n")

        if limit:
            chapters = chapters[:limit]
            print(f"⚠️  Limited to {limit} chapters\n")

        # Step 2: Process each chapter
        total_downloaded = 0
        total_failed = 0

        for i, (chapter_num, chapter_url, chapter_title) in enumerate(chapters, 1):
            print(f"\n{'='*70}")
            print(f"Chapter {i}/{len(chapters)}: {chapter_title}")
            print(f"{'='*70}")

            # Get sections
            sections = extract_sections_with_selenium(driver, chapter_url, chapter_num)
            print(f"  Found {len(sections)} sections")

            for section_num, section_url, section_title in sections:
                print(f"\n  Section: {section_title}")

                filename = f"RCW_{section_num.replace('.', '-')}.pdf"
                output_path = OUTPUT_DIR / filename

                if output_path.exists():
                    print(f"    ⏭️  Already exists: {filename}")
                    continue

                success = download_section_as_pdf(driver, section_url, section_num, output_path)
                if success:
                    total_downloaded += 1
                else:
                    total_failed += 1

                time.sleep(1)

        # Summary
        print("\n" + "="*70)
        print("📊 EXTRACTION SUMMARY")
        print("="*70)
        print(f"✅ Downloaded: {total_downloaded} PDFs")
        print(f"❌ Failed: {total_failed}")
        print(f"📁 Location: {OUTPUT_DIR}")
        print("="*70 + "\n")

    finally:
        driver.quit()
        print("🔒 Browser closed")


def main():
    parser = argparse.ArgumentParser(
        description="Extract RCW Title 82 PDFs using Selenium (browser automation)"
    )
    parser.add_argument("--limit", type=int, help="Limit number of chapters")
    parser.add_argument("--visible", action="store_true", help="Show browser window (not headless)")

    args = parser.parse_args()

    scrape_with_selenium(
        limit=args.limit,
        headless=not args.visible
    )


if __name__ == "__main__":
    main()
