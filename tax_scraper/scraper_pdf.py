"""
Washington State Tax Law PDF Scraper
Ingests RCW Title 82, WAC Title 458, and DOR Tax Determinations from PDF sources
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import logging
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional
import PyPDF2
import io

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'scraper_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = Path(__file__).parent / "tax_laws.db"
RAW_FILES_DIR = Path(__file__).parent / "raw_files" / "pdfs"
RAW_FILES_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# RCW PDF base URL
RCW_PDF_BASE = "https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf"


class TaxLawDatabase:
    """Manages SQLite database for tax law storage"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize database with schema supporting vector embeddings"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # RCW sections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rcw_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citation TEXT UNIQUE NOT NULL,
                title TEXT,
                chapter TEXT,
                section TEXT,
                full_text TEXT NOT NULL,
                effective_date TEXT,
                url TEXT,
                pdf_path TEXT,
                embedding BLOB,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Scraping progress table for resumability
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_type TEXT NOT NULL,
                last_citation TEXT,
                last_url TEXT,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rcw_citation ON rcw_sections(citation)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_rcw_section(self, data: Dict) -> bool:
        """Insert or update RCW section"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO rcw_sections (citation, title, chapter, section, full_text, effective_date, url, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(citation) DO UPDATE SET
                    full_text = excluded.full_text,
                    effective_date = excluded.effective_date,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                data['citation'],
                data.get('title'),
                data.get('chapter'),
                data.get('section'),
                data['full_text'],
                data.get('effective_date'),
                data.get('url'),
                data.get('pdf_path')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting RCW section {data.get('citation')}: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()


class RCWPDFScraper:
    """Scraper for RCW Title 82 from PDF files"""

    def __init__(self, db: TaxLawDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_title_82(self):
        """Scrape all chapters and sections under RCW Title 82 from PDFs"""
        logger.info("Starting RCW Title 82 PDF scrape")

        # Important chapters for sales/use tax
        important_chapters = [
            '01', '02', '03', '04', '08', '12', '14', '16', '24', '27', '29A',
            '32', '34', '36', '38', '42', '45', '46', '48', '49', '51', '52',
            '54', '60', '63', '64', '70', '74', '75', '80', '82', '84', '85',
            '86', '87', '89', '91'
        ]

        total_sections = 0
        for chapter in important_chapters:
            logger.info(f"Scraping Chapter 82.{chapter}...")
            sections_scraped = self.scrape_chapter_from_pdf(chapter)
            total_sections += sections_scraped
            time.sleep(REQUEST_DELAY)

        logger.info(f"RCW PDF scraping complete. Total sections: {total_sections}")

    def scrape_chapter_from_pdf(self, chapter: str) -> int:
        """Scrape all sections in a chapter from combined PDF"""
        # First, get directory listing to find all section PDFs
        chapter_url = f"{RCW_PDF_BASE}/RCW%20%2082%20%20TITLE/RCW%20%2082%20.%20{chapter}%20%20CHAPTER/"

        try:
            response = self._make_request(chapter_url)
            if not response:
                logger.warning(f"Could not access chapter directory: {chapter_url}")
                return 0

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all PDF links
            all_links = soup.find_all('a', href=re.compile(r'\.pdf$'))

            sections_count = 0
            # Pattern to extract section number from link text (not href, which is URL-encoded)
            section_pattern = re.compile(r'82\s+\.\s+' + chapter + r'\s+\.(\d+[A-Za-z]*)\.pdf$', re.IGNORECASE)

            for link in all_links:
                href = link.get('href')
                link_text = link.get_text(strip=True)

                # Skip chapter/combined PDFs
                if not href or 'CHAPTER' in link_text.upper() or 'COMBINED' in link_text.upper():
                    continue

                # Extract section number from link text (easier than dealing with URL encoding)
                section_match = section_pattern.search(link_text)
                if not section_match:
                    continue

                section_num = section_match.group(1)
                citation = f"RCW 82.{chapter}.{section_num}"

                # Build full PDF URL
                if href.startswith('http'):
                    pdf_url = href
                elif href.startswith('/'):
                    pdf_url = f"https://lawfilesext.leg.wa.gov{href}"
                else:
                    pdf_url = chapter_url + href

                # Download and parse PDF
                if self.scrape_section_pdf(citation, pdf_url, chapter, section_num):
                    sections_count += 1
                    logger.info(f"Scraped: {citation}")

                time.sleep(REQUEST_DELAY)

            return sections_count

        except Exception as e:
            logger.error(f"Error scraping chapter {chapter}: {e}")
            return 0

    def scrape_section_pdf(self, citation: str, pdf_url: str, chapter: str, section: str) -> bool:
        """Download and extract text from a section PDF"""
        try:
            response = self._make_request(pdf_url)
            if not response:
                return False

            # Save PDF file
            pdf_filename = f"rcw_82_{chapter}_{section}.pdf"
            pdf_path = RAW_FILES_DIR / pdf_filename

            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            # Extract text from PDF
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"

            if not full_text.strip():
                logger.warning(f"No text extracted from PDF: {citation}")
                return False

            # Extract title (usually first non-RCW line)
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            title = ""
            for line in lines:
                if 'RCW' not in line and len(line) > 10:
                    title = line
                    break

            # Extract effective date if present
            effective_date = None
            date_match = re.search(r'\[(.*?\d{4}.*?)\]', full_text)
            if date_match:
                effective_date = date_match.group(1)

            # Insert into database
            section_data = {
                'citation': citation,
                'title': title[:500] if title else None,  # Limit title length
                'chapter': chapter,
                'section': section,
                'full_text': full_text,
                'effective_date': effective_date,
                'url': pdf_url,
                'pdf_path': str(pdf_path)
            }

            return self.db.insert_rcw_section(section_data)

        except Exception as e:
            logger.error(f"Error scraping PDF for {citation}: {e}")
            return False

    def _make_request(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None


def main():
    """Main execution function"""
    logger.info("=== Tax Law PDF Scraper Started ===")

    # Initialize database
    db = TaxLawDatabase(DB_PATH)

    try:
        # Start with RCW PDF scraper
        rcw_scraper = RCWPDFScraper(db)
        rcw_scraper.scrape_title_82()

        logger.info("=== Scraping Complete ===")

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
