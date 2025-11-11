#!/usr/bin/env python3
"""
Download Washington State Department of Revenue Tax Decisions

Scrapes https://dor.wa.gov/washington-tax-decisions and downloads all tax decision PDFs
organized by year.

Usage:
    python scripts/download_tax_decisions.py
    python scripts/download_tax_decisions.py --years 2023,2024,2025
    python scripts/download_tax_decisions.py --output-dir custom/path
    python scripts/download_tax_decisions.py --limit 10  # For testing
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


# Configuration
DEFAULT_OUTPUT_DIR = "knowledge_base/wa_tax_law/tax_decisions"
BASE_URL = "https://dor.wa.gov"
DECISIONS_URL = f"{BASE_URL}/washington-tax-decisions"
USER_AGENT = "WA-Tax-Research-Bot/1.0 (Educational/Research; Refund Analysis)"
RATE_LIMIT_SECONDS = 1.0  # Respectful rate limiting


class TaxDecisionScraper:
    """Scraper for Washington State DOR Tax Decisions"""

    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR, rate_limit: float = RATE_LIMIT_SECONDS):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def scrape_decision_links(self, year_filter: Optional[List[str]] = None) -> List[Dict]:
        """
        Scrape the main page for all tax decision links and metadata

        Args:
            year_filter: List of years to filter (e.g., ['2023', '2024']). None = all years

        Returns:
            List of decision dicts with: citation, date, summary, pdf_url, year, filename
        """
        print(f"Fetching decision listings from {DECISIONS_URL}...")

        try:
            response = self.session.get(DECISIONS_URL, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching decisions page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        decisions = []

        # Find all table rows containing decisions
        # The page structure: table with columns: title, date, pdf_link, summary
        tables = soup.find_all('table')

        for table in tables:
            # Try to find year heading (usually in h2 or h3 before table)
            year_heading = table.find_previous(['h2', 'h3', 'h4'])
            table_year = None

            if year_heading:
                year_text = year_heading.get_text()
                year_match = re.search(r'(20\d{2})', year_text)
                if year_match:
                    table_year = year_match.group(1)

            # Parse table rows
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')

                if len(cells) >= 3:
                    # Column structure:
                    # [0] = citation/title (views-field-title)
                    # [1] = date (views-field-field-date)
                    # [2] = PDF link (views-field-field-media-file)
                    # [3] = summary (views-field-body) - optional

                    # Extract citation from first cell
                    citation = cells[0].get_text(strip=True)
                    if not citation:
                        continue

                    # Extract date from second cell
                    date = cells[1].get_text(strip=True) if len(cells) > 1 else ""

                    # Extract PDF link from third cell
                    pdf_link = cells[2].find('a', href=re.compile(r'\.pdf$', re.IGNORECASE)) if len(cells) > 2 else None

                    if not pdf_link:
                        continue

                    pdf_url = urljoin(BASE_URL, pdf_link.get('href'))

                    # Extract summary from fourth cell
                    summary = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                    # Determine year: try table year first, then extract from date
                    year = table_year
                    if not year and date:
                        date_year_match = re.search(r'(20\d{2})', date)
                        if date_year_match:
                            year = date_year_match.group(1)

                    # Apply year filter at decision level
                    if year_filter and (not year or year not in year_filter):
                        continue

                    # Generate filename from PDF link (e.g., "44WTD070.pdf")
                    filename = pdf_link.get_text(strip=True)

                    decisions.append({
                        'citation': citation,
                        'date': date,
                        'summary': summary,
                        'pdf_url': pdf_url,
                        'year': year or 'unknown',
                        'filename': filename,
                    })

        print(f"✅ Found {len(decisions)} tax decisions")
        return decisions

    def _extract_filename_from_citation(self, citation: str, pdf_url: str) -> str:
        """Extract or generate filename from citation or URL"""
        # Try to get filename from URL first
        url_filename = Path(pdf_url).name
        if url_filename and url_filename.endswith('.pdf'):
            return url_filename

        # Otherwise generate from citation
        # "Det. No. 22-0105, 44 WTD 070" -> "det_no_22-0105_44_wtd_070.pdf"
        clean_citation = re.sub(r'[^\w\s-]', '', citation)
        clean_citation = re.sub(r'\s+', '_', clean_citation)
        return f"{clean_citation.lower()}.pdf"

    def download_decision(self, decision: Dict, year_dir: Path) -> bool:
        """
        Download a single tax decision PDF and save metadata

        Args:
            decision: Decision dict with pdf_url, filename, metadata
            year_dir: Directory to save the PDF

        Returns:
            True if successful, False otherwise
        """
        pdf_path = year_dir / decision['filename']
        metadata_path = year_dir / f"{pdf_path.stem}.json"

        # Skip if already downloaded
        if pdf_path.exists():
            return True

        try:
            # Download PDF with timeout and retry logic
            response = self._download_with_retry(decision['pdf_url'])

            if not response:
                return False

            # Save PDF
            pdf_path.write_bytes(response.content)

            # Save metadata JSON
            metadata = {
                'citation': decision['citation'],
                'date': decision['date'],
                'summary': decision['summary'],
                'pdf_url': decision['pdf_url'],
                'year': decision['year'],
                'filename': decision['filename'],
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2))

            return True

        except Exception as e:
            print(f"  ❌ Error downloading {decision['filename']}: {e}")
            return False

    def _download_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Download with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"  ❌ Failed after {max_retries} attempts: {e}")
                    return None

                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  ⚠️  Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)

        return None

    def download_all(self, decisions: List[Dict], limit: Optional[int] = None) -> Dict[str, int]:
        """
        Download all tax decisions with progress tracking

        Args:
            decisions: List of decision dicts from scrape_decision_links()
            limit: Optional limit for testing (download first N decisions)

        Returns:
            Dict with stats: {'success': N, 'skipped': N, 'failed': N}
        """
        if limit:
            decisions = decisions[:limit]
            print(f"⚠️  Limiting to {limit} decisions for testing")

        stats = {'success': 0, 'skipped': 0, 'failed': 0}

        # Group by year
        by_year = {}
        for decision in decisions:
            year = decision['year']
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(decision)

        # Download by year
        for year, year_decisions in sorted(by_year.items()):
            year_dir = self.output_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n📅 Downloading {len(year_decisions)} decisions from {year}...")

            for decision in tqdm(year_decisions, desc=f"  {year}"):
                pdf_path = year_dir / decision['filename']

                if pdf_path.exists():
                    stats['skipped'] += 1
                    continue

                success = self.download_decision(decision, year_dir)

                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1

                # Rate limiting
                time.sleep(self.rate_limit)

        return stats

    def generate_index(self, decisions: List[Dict]):
        """Generate master index file with all decisions"""
        index_path = self.output_dir / "index.json"

        index_data = {
            'total_decisions': len(decisions),
            'years': sorted(list(set(d['year'] for d in decisions))),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'decisions': decisions,
        }

        index_path.write_text(json.dumps(index_data, indent=2))
        print(f"\n📋 Generated index: {index_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download Washington State DOR Tax Decisions"
    )
    parser.add_argument(
        '--output-dir',
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        '--years',
        help="Comma-separated years to download (e.g., '2023,2024,2025'). Default: all years"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Limit number of decisions to download (for testing)"
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=RATE_LIMIT_SECONDS,
        help=f"Seconds between downloads (default: {RATE_LIMIT_SECONDS})"
    )

    args = parser.parse_args()

    # Parse year filter
    year_filter = None
    if args.years:
        year_filter = [y.strip() for y in args.years.split(',')]

    # Initialize scraper
    scraper = TaxDecisionScraper(output_dir=args.output_dir, rate_limit=args.rate_limit)

    # Scrape decision links
    print("=" * 70)
    print("Washington State DOR Tax Decisions Downloader")
    print("=" * 70)

    decisions = scraper.scrape_decision_links(year_filter=year_filter)

    if not decisions:
        print("❌ No decisions found")
        return

    # Download all decisions
    stats = scraper.download_all(decisions, limit=args.limit)

    # Generate index
    scraper.generate_index(decisions)

    # Print summary
    print("\n" + "=" * 70)
    print("📊 Download Summary")
    print("=" * 70)
    print(f"✅ Successfully downloaded: {stats['success']}")
    print(f"⏭️  Skipped (already exist): {stats['skipped']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📁 Output directory: {scraper.output_dir.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
