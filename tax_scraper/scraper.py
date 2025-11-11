"""
Washington State Tax Law Scraper
Ingests RCW Title 82, WAC Title 458, and DOR Tax Determinations into SQLite database
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
import json

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
RAW_FILES_DIR = Path(__file__).parent / "raw_files"
RAW_FILES_DIR.mkdir(exist_ok=True)

REQUEST_DELAY = 1.5  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


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
                embedding BLOB,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # WAC sections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wac_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citation TEXT UNIQUE NOT NULL,
                title TEXT,
                chapter TEXT,
                section TEXT,
                full_text TEXT NOT NULL,
                effective_date TEXT,
                url TEXT,
                embedding BLOB,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # DOR determinations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dor_determinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                determination_number TEXT UNIQUE NOT NULL,
                date TEXT,
                tax_type TEXT,
                industry TEXT,
                title TEXT,
                full_text TEXT,
                pdf_url TEXT,
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wac_citation ON wac_sections(citation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dor_number ON dor_determinations(determination_number)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_rcw_section(self, data: Dict) -> bool:
        """Insert or update RCW section"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO rcw_sections (citation, title, chapter, section, full_text, effective_date, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
                data.get('url')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting RCW section {data.get('citation')}: {e}")
            return False

    def update_progress(self, scraper_type: str, last_citation: str, last_url: str, status: str):
        """Update scraping progress for resumability"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scraping_progress (scraper_type, last_citation, last_url, status)
            VALUES (?, ?, ?, ?)
        """, (scraper_type, last_citation, last_url, status))
        self.conn.commit()

    def get_last_progress(self, scraper_type: str) -> Optional[Dict]:
        """Get last scraping progress"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT last_citation, last_url, status, timestamp
            FROM scraping_progress
            WHERE scraper_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (scraper_type,))
        result = cursor.fetchone()
        if result:
            return {
                'last_citation': result[0],
                'last_url': result[1],
                'status': result[2],
                'timestamp': result[3]
            }
        return None

    def close(self):
        if self.conn:
            self.conn.close()


class RCWScraper:
    """Scraper for RCW Title 82 (Excise Taxes)"""

    def __init__(self, db: TaxLawDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://app.leg.wa.gov"

    def scrape_title_82(self):
        """Scrape all chapters and sections under RCW Title 82"""
        logger.info("Starting RCW Title 82 scrape")

        # Get all chapters in Title 82
        chapters = self.get_title_chapters()
        logger.info(f"Found {len(chapters)} chapters in Title 82")

        total_sections = 0
        for chapter_num, chapter_url in chapters:
            logger.info(f"Scraping Chapter {chapter_num}...")
            sections = self.get_chapter_sections(chapter_url, chapter_num)

            for section_data in sections:
                if self.scrape_section(section_data):
                    total_sections += 1
                    logger.info(f"Scraped: {section_data['citation']}")

                time.sleep(REQUEST_DELAY)

            self.db.update_progress('rcw_title_82', f"82.{chapter_num}", chapter_url, 'completed')

        logger.info(f"RCW scraping complete. Total sections: {total_sections}")

    def get_title_chapters(self) -> List[tuple]:
        """Get all chapter numbers and URLs for Title 82"""
        chapters = []

        # Focus on the most important chapters for sales/use tax
        # These are the core chapters relevant to refund analysis
        important_chapters = [
            '01',  # Definitions
            '02',  # Deductions, credits
            '03',  # Administration and penalties
            '04',  # Business & Occupation Tax
            '08',  # Retail Sales Tax
            '12',  # Use Tax
            '14',  # Local Taxes
            '16',  # Public Utility Tax
            '24',  # Timber Tax
            '27',  # Wholesaling of Motor Vehicle Fuel Tax
            '29A', # Litter Tax
            '32',  # Administration and penalties
            '34',  # Penalties
            '36',  # Taxpayer Assistance
            '38',  # Sales and Use Tax for Mental Health Services
            '42',  # Marijuana Tax
            '45',  # Economic Nexus
            '46',  # Lodging Tax
            '48',  # Manufactured/Mobile Home Tax
            '49',  # Commute Trip Reduction Tax
            '51',  # Enhanced Food Fish Tax
            '52',  # Extension, collection of other taxes
            '54',  # Pollution Control Facilities
            '60',  # Multistate Tax Compact
            '63',  # Tax Reform
            '64',  # Tax preferences
            '70',  # Data centers
            '74',  # Ride-sharing surcharges
            '75',  # Worker Training Surcharges
            '80',  # Vapor products tax
            '82',  # Timber tax distribution
            '84',  # Warehouse and grain elevators
            '85',  # Semiconductors
            '86',  # Linking program
            '87',  # High capacity transportation
            '89',  # Aviation fuel tax
            '91'   # Incremental tax rate
        ]

        for chapter in important_chapters:
            url = f"{self.base_url}/RCW/default.aspx?cite=82.{chapter}"

            # Check if chapter exists
            try:
                response = self._make_request(url)
                if response and "No results found" not in response.text:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Check if there's actual content
                    if soup.find('div', class_='WSLegislativeText') or soup.find('a', href=re.compile(r'cite=82\.')):
                        chapters.append((chapter, url))
                        logger.info(f"Found chapter 82.{chapter}")

                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Chapter 82.{chapter} does not exist or error: {e}")
                continue

        return chapters

    def get_chapter_sections(self, chapter_url: str, chapter_num: str) -> List[Dict]:
        """Get all sections within a chapter"""
        sections = []

        response = self._make_request(chapter_url)
        if not response:
            return sections

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all section links in the chapter index
        section_links = soup.find_all('a', href=re.compile(r'cite=82\.' + chapter_num + r'\.\d+'))

        for link in section_links:
            citation_match = re.search(r'cite=([\d.]+)', link.get('href', ''))
            if citation_match:
                citation = citation_match.group(1)
                section_url = self.base_url + link['href'] if link['href'].startswith('/') else link['href']

                sections.append({
                    'citation': f"RCW {citation}",
                    'chapter': chapter_num,
                    'section': citation.split('.')[-1],
                    'url': section_url
                })

        return sections

    def scrape_section(self, section_data: Dict) -> bool:
        """Scrape a specific RCW section"""
        response = self._make_request(section_data['url'])
        if not response:
            return False

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract section title
        title_elem = soup.find('h2')
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Extract full text of the section
        text_div = soup.find('div', class_='WSLegislativeText')
        if not text_div:
            logger.warning(f"No text found for {section_data['citation']}")
            return False

        full_text = text_div.get_text(separator='\n', strip=True)

        # Extract effective date if available
        effective_date = None
        date_pattern = re.search(r'\[(\d{4}.*?)\]', full_text)
        if date_pattern:
            effective_date = date_pattern.group(1)

        # Save raw HTML
        raw_file = RAW_FILES_DIR / f"rcw_{section_data['citation'].replace(' ', '_').replace('.', '_')}.html"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Insert into database
        section_data.update({
            'title': title,
            'full_text': full_text,
            'effective_date': effective_date
        })

        return self.db.insert_rcw_section(section_data)

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
    logger.info("=== Tax Law Scraper Started ===")

    # Initialize database
    db = TaxLawDatabase(DB_PATH)

    try:
        # Start with RCW scraper
        rcw_scraper = RCWScraper(db)
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
