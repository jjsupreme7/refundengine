#!/usr/bin/env python3
"""
Download Washington Administrative Code (WAC) Title 458 - Department of Revenue

Scrapes https://app.leg.wa.gov/wac/default.aspx?cite=458 and downloads all sections
from Chapter 458-20 (Excise Tax Rules) and other relevant chapters.

Usage:
    python scripts/download_wac_title_458.py
    python scripts/download_wac_title_458.py --chapters 458-20
    python scripts/download_wac_title_458.py --limit 10  # For testing
    python scripts/download_wac_title_458.py --format html  # HTML only
    python scripts/download_wac_title_458.py --format pdf   # PDF only
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configuration
DEFAULT_OUTPUT_DIR = "knowledge_base/wa_tax_law/wac/title_458"
BASE_URL = "https://app.leg.wa.gov/wac"
USER_AGENT = "WA-Tax-Research-Bot/1.0 (Educational/Research; Refund Analysis)"
RATE_LIMIT_SECONDS = 2.0  # More conservative for leg.wa.gov

# Priority chapters for tax law
PRIORITY_CHAPTERS = [
    "458-20",  # Excise tax rules (most important, ~270 sections)
    "458-02",  # Consolidated licensing system
    "458-29",  # Tax appeals
    "458-30",  # Property tax
]


class WACTitleScraper:
    """Scraper for Washington Administrative Code Title 458"""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        rate_limit: float = RATE_LIMIT_SECONDS,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def scrape_chapters(self, title_cite: str = "458") -> List[Dict]:
        """
        Scrape title page to get all chapters

        Args:
            title_cite: Title number (default: "458")

        Returns:
            List of chapter dicts with: cite, title, url
        """
        url = f"{BASE_URL}/default.aspx?cite={title_cite}"
        print(f"Fetching chapters from {url}...")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching title page: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        chapters = []

        # Find all chapter links (format: cite=458-XX)
        for link in soup.find_all("a", href=re.compile(r"cite=458-\d+")):
            href = link.get("hre")
            cite_match = re.search(r"cite=(458-\d+)", href)

            if cite_match:
                chapter_cite = cite_match.group(1)
                chapter_title = link.get_text(strip=True)
                chapter_url = urljoin(BASE_URL, href)

                chapters.append(
                    {
                        "cite": chapter_cite,
                        "title": chapter_title,
                        "url": chapter_url,
                    }
                )

        print(f"✅ Found {len(chapters)} chapters in Title {title_cite}")
        return chapters

    def scrape_chapter_sections(self, chapter_cite: str) -> List[Dict]:
        """
        Scrape chapter page to get all sections

        Args:
            chapter_cite: Chapter citation (e.g., "458-20")

        Returns:
            List of section dicts with: cite, title, url
        """
        url = f"{BASE_URL}/default.aspx?cite={chapter_cite}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error fetching chapter {chapter_cite}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        sections = []

        # Find all section links (format: cite=458-XX-XXXXX)
        pattern = re.compile(rf"cite={re.escape(chapter_cite)}-\d+")

        for link in soup.find_all("a", href=pattern):
            href = link.get("hre")
            cite_match = re.search(r"cite=(458-\d+-\d+)", href)

            if cite_match:
                section_cite = cite_match.group(1)
                section_title = link.get_text(strip=True)
                section_url = urljoin(BASE_URL, href)

                sections.append(
                    {
                        "cite": section_cite,
                        "title": section_title,
                        "url": section_url,
                        "chapter": chapter_cite,
                    }
                )

        return sections

    def download_section(self, section: Dict, format: str, chapter_dir: Path) -> bool:
        """
        Download a single WAC section in specified format(s)

        Args:
            section: Section dict with cite, title, url
            format: 'html', 'pd', or 'both'
            chapter_dir: Directory to save the section

        Returns:
            True if successful, False otherwise
        """
        cite = section["cite"]
        safe_cite = cite.replace("-", "_")
        safe_title = re.sub(r"[^\w\s-]", "", section["title"])
        safe_title = re.sub(r"\s+", "_", safe_title)
        base_filename = f"{safe_cite}_{safe_title[:50]}"

        success = True

        # Download HTML
        if format in ["html", "both"]:
            html_path = chapter_dir / f"{base_filename}.html"

            if not html_path.exists():
                html_url = f"{BASE_URL}/default.aspx?cite={cite}&full=true"
                html_content = self._download_with_retry(html_url)

                if html_content:
                    html_path.write_bytes(html_content.content)
                else:
                    success = False

        # Download PDF (may require authentication/session)
        if format in ["pd", "both"]:
            pdf_path = chapter_dir / f"{base_filename}.pd"

            if not pdf_path.exists():
                pdf_url = f"{BASE_URL}/default.aspx?cite={cite}&pdf=true"
                pdf_content = self._download_with_retry(pdf_url)

                if pdf_content:
                    # Verify it's actually a PDF (not an error page)
                    if pdf_content.content[:4] == b"%PDF":
                        pdf_path.write_bytes(pdf_content.content)
                    else:
                        print(
                            f"  ⚠️  PDF authentication required for {
                                cite}, skipping PDF"
                        )
                        # Still consider success if HTML worked
                        success = success and (format == "both")
                else:
                    success = False

        # Save metadata
        if success or format == "html":  # Save metadata even if PDF failed
            metadata_path = chapter_dir / f"{base_filename}.json"
            metadata = {
                "cite": section["cite"],
                "title": section["title"],
                "chapter": section["chapter"],
                "url": section["url"],
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2))

        return success

    def _download_with_retry(
        self, url: str, max_retries: int = 3
    ) -> Optional[requests.Response]:
        """Download with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return None

                wait_time = 2**attempt
                time.sleep(wait_time)

        return None

    def download_chapter(
        self, chapter_cite: str, format: str, limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Download all sections in a chapter

        Args:
            chapter_cite: Chapter citation (e.g., "458-20")
            format: 'html', 'pd', or 'both'
            limit: Optional limit for testing

        Returns:
            Stats dict: {'success': N, 'skipped': N, 'failed': N}
        """
        print(f"\n📖 Scraping sections from chapter {chapter_cite}...")

        sections = self.scrape_chapter_sections(chapter_cite)

        if not sections:
            print(f"  ❌ No sections found in chapter {chapter_cite}")
            return {"success": 0, "skipped": 0, "failed": 0}

        print(f"  ✅ Found {len(sections)} sections")

        if limit:
            sections = sections[:limit]
            print(f"  ⚠️  Limiting to {limit} sections for testing")

        # Create chapter directory
        safe_chapter = chapter_cite.replace("-", "_")
        chapter_dir = self.output_dir / f"chapter_{safe_chapter}"
        chapter_dir.mkdir(parents=True, exist_ok=True)

        # Download sections
        stats = {"success": 0, "skipped": 0, "failed": 0}

        for section in tqdm(sections, desc=f"  {chapter_cite}"):
            # Check if already exists
            safe_cite = section["cite"].replace("-", "_")
            html_exists = any(chapter_dir.glob(f"{safe_cite}_*.html"))
            pdf_exists = any(chapter_dir.glob(f"{safe_cite}_*.pd"))

            skip = False
            if format == "html" and html_exists:
                skip = True
            elif format == "pd" and pdf_exists:
                skip = True
            elif format == "both" and html_exists and pdf_exists:
                skip = True

            if skip:
                stats["skipped"] += 1
                continue

            success = self.download_section(section, format, chapter_dir)

            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1

            # Rate limiting
            time.sleep(self.rate_limit)

        return stats

    def download_all(
        self,
        chapter_filter: Optional[List[str]] = None,
        format: str = "both",
        limit: Optional[int] = None,
    ):
        """
        Download all chapters and sections

        Args:
            chapter_filter: List of chapter cites to download (e.g., ['458-20']). None = all
            format: 'html', 'pd', or 'both'
            limit: Limit sections per chapter (for testing)
        """
        # Get all chapters
        chapters = self.scrape_chapters()

        if not chapters:
            print("❌ No chapters found")
            return

        # Filter chapters if specified
        if chapter_filter:
            chapters = [c for c in chapters if c["cite"] in chapter_filter]
            print(
                f"📋 Filtered to {len(chapters)} chapters: {', '.join(chapter_filter)}"
            )

        # Download each chapter
        total_stats = {"success": 0, "skipped": 0, "failed": 0}

        for chapter in chapters:
            stats = self.download_chapter(chapter["cite"], format, limit)

            for key in stats:
                total_stats[key] += stats[key]

        # Print summary
        print("\n" + "=" * 70)
        print("📊 Download Summary")
        print("=" * 70)
        print(f"✅ Successfully downloaded: {total_stats['success']}")
        print(f"⏭️  Skipped (already exist): {total_stats['skipped']}")
        print(f"❌ Failed: {total_stats['failed']}")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Download Washington Administrative Code (WAC) Title 458"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--chapters",
        help=f"Comma-separated chapters to download (e.g., '458-20,458-29'). Default: {
            ','.join(PRIORITY_CHAPTERS)}",
    )
    parser.add_argument(
        "--all-chapters",
        action="store_true",
        help="Download ALL chapters (not just priority ones)",
    )
    parser.add_argument(
        "--format",
        choices=["html", "pd", "both"],
        default="both",
        help="Download format (default: both)",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit sections per chapter (for testing)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=RATE_LIMIT_SECONDS,
        help=f"Seconds between downloads (default: {RATE_LIMIT_SECONDS})",
    )

    args = parser.parse_args()

    # Determine chapter filter
    chapter_filter = None
    if args.chapters:
        chapter_filter = [c.strip() for c in args.chapters.split(",")]
    elif not args.all_chapters:
        chapter_filter = PRIORITY_CHAPTERS

    # Initialize scraper
    scraper = WACTitleScraper(output_dir=args.output_dir, rate_limit=args.rate_limit)

    # Download
    print("=" * 70)
    print("Washington Administrative Code (WAC) Title 458 Downloader")
    print("=" * 70)

    scraper.download_all(
        chapter_filter=chapter_filter, format=args.format, limit=args.limit
    )


if __name__ == "__main__":
    main()
