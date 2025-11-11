"""
Enrich RCW sections in WA_Tax_Law.xlsx with AI-generated metadata
Matches the exact format used for WAC analysis in core/ingest_documents.py
Uses OpenAI GPT-4o-mini for cost-effective bulk processing
"""

import pandas as pd
from pathlib import Path
import logging
import os
from openai import OpenAI
from typing import Dict, List, Any
import json
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "WA_Tax_Law.xlsx"
DB_PATH = Path(__file__).parent / "tax_laws.db"

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def array_to_string(value: Any) -> str:
    """Convert array to comma-separated string, handle various input types"""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    elif isinstance(value, str):
        return value
    else:
        return str(value) if value else ""


def analyze_rcw_section(client: OpenAI, citation: str, title: str, full_text: str) -> Dict:
    """
    Use OpenAI GPT-4o-mini to analyze RCW section and extract metadata
    Matches the format from core/ingest_documents.py suggest_metadata_with_ai()
    """

    # Match exact prompt from core/ingest_documents.py
    prompt = f"""Analyze this Washington State tax law document and extract metadata.

Filename: {citation}

First few pages:
{full_text[:3000]}

Return JSON with these fields:
{{
  "document_title": "Full descriptive title",
  "citation": "WAC 458-20-101 or RCW 82.04",
  "law_category": "exemption" | "rate" | "definition" | "compliance" | "general",
  "effective_date": "2020-01-01 or null",
  "topic_tags": ["registration", "licensing"],
  "tax_types": ["sales tax", "use tax"],
  "industries": ["general", "retail"],
  "keywords": ["key", "terms"],
  "referenced_statutes": ["RCW 82.04"],
  "document_summary": "1-2 sentence summary"
}}

Be specific and accurate. Extract actual information from the text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing tax law documents. Extract metadata accurately."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )

        # Extract JSON from response
        response_text = response.choices[0].message.content
        metadata = json.loads(response_text.strip())

        # Convert arrays to comma-separated strings for Excel compatibility
        processed_metadata = {
            "law_category": metadata.get("law_category", ""),
            "topic_tags": array_to_string(metadata.get("topic_tags", [])),
            "tax_types": array_to_string(metadata.get("tax_types", [])),
            "industries": array_to_string(metadata.get("industries", [])),
            "keywords": array_to_string(metadata.get("keywords", [])),
            "referenced_statutes": array_to_string(metadata.get("referenced_statutes", [])),
            "document_summary": metadata.get("document_summary", "")
        }

        return processed_metadata

    except Exception as e:
        logger.error(f"Error analyzing {citation}: {e}")
        return {
            "law_category": "",
            "topic_tags": "",
            "tax_types": "",
            "industries": "",
            "keywords": "",
            "referenced_statutes": "",
            "document_summary": f"[Error analyzing: {str(e)[:100]}]"
        }


def enrich_metadata():
    """Enrich RCW sections with AI-generated metadata matching WAC format"""

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.info("Set it with: $env:OPENAI_API_KEY='your-key-here'")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Read Excel file
    logger.info(f"Reading {OUTPUT_FILE}")
    df = pd.read_excel(OUTPUT_FILE, sheet_name='Metadata')
    logger.info(f"Total records: {len(df)}")

    # Connect to SQLite to get full_text
    import sqlite3
    conn = sqlite3.connect(DB_PATH)

    # Get RCW sections that need enrichment (empty law_category or document_summary)
    rcw_mask = df['citation'].str.startswith('RCW', na=False)
    needs_enrichment = df[rcw_mask & (df['law_category'].isna() | (df['law_category'] == ''))]

    logger.info(f"RCW sections needing enrichment: {len(needs_enrichment)}")

    if len(needs_enrichment) == 0:
        logger.info("No sections need enrichment!")
        conn.close()
        return

    # Process each section
    enriched_count = 0
    start_time = time.time()

    for idx, row in needs_enrichment.iterrows():
        citation = row['citation']
        title = row['document_title'] if pd.notna(row['document_title']) else ""

        logger.info(f"Analyzing {citation} ({enriched_count + 1}/{len(needs_enrichment)})")

        # Get full text from database
        cursor = conn.cursor()
        cursor.execute("SELECT full_text FROM rcw_sections WHERE citation = ?", (citation,))
        result = cursor.fetchone()

        if not result:
            logger.warning(f"No full_text found for {citation}")
            continue

        full_text = result[0]

        # Analyze with OpenAI
        metadata = analyze_rcw_section(client, citation, title, full_text)

        # Update dataframe with comma-separated strings
        df.at[idx, 'law_category'] = metadata.get('law_category', '')
        df.at[idx, 'topic_tags'] = metadata.get('topic_tags', '')
        df.at[idx, 'tax_types'] = metadata.get('tax_types', '')
        df.at[idx, 'industries'] = metadata.get('industries', '')
        df.at[idx, 'keywords'] = metadata.get('keywords', '')
        df.at[idx, 'referenced_statutes'] = metadata.get('referenced_statutes', '')
        df.at[idx, 'document_summary'] = metadata.get('document_summary', '')
        df.at[idx, 'AI_Confidence'] = 'High'

        enriched_count += 1

        # Progress reporting every 50 sections
        if enriched_count % 50 == 0:
            elapsed = time.time() - start_time
            rate = enriched_count / elapsed
            remaining = (len(needs_enrichment) - enriched_count) / rate
            logger.info(f"Progress: {enriched_count}/{len(needs_enrichment)} sections enriched")
            logger.info(f"Rate: {rate:.1f} sections/sec | ETA: {remaining/60:.1f} minutes")
            time.sleep(0.5)  # Small delay every 50 requests

    conn.close()

    # Write back to Excel
    logger.info(f"Writing enriched data to {OUTPUT_FILE}")
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Metadata', index=False)

        # Apply formatting
        worksheet = writer.sheets['Metadata']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 12
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 50
        worksheet.column_dimensions['E'].width = 20
        worksheet.column_dimensions['F'].width = 15
        worksheet.column_dimensions['G'].width = 15
        worksheet.column_dimensions['H'].width = 30
        worksheet.column_dimensions['I'].width = 20
        worksheet.column_dimensions['J'].width = 20
        worksheet.column_dimensions['K'].width = 30
        worksheet.column_dimensions['L'].width = 20
        worksheet.column_dimensions['M'].width = 60
        worksheet.column_dimensions['N'].width = 15
        worksheet.column_dimensions['O'].width = 12
        worksheet.column_dimensions['P'].width = 50
        worksheet.freeze_panes = 'A2'

    total_time = time.time() - start_time
    logger.info(f"✓ Enriched {enriched_count} RCW sections with AI-generated metadata")
    logger.info(f"✓ Total time: {total_time/60:.1f} minutes")
    logger.info(f"✓ Average: {total_time/enriched_count:.2f} seconds per section")
    logger.info(f"✓ File updated: {OUTPUT_FILE}")
    logger.info(f"✓ Format: Matches WAC analysis from core/ingest_documents.py")


if __name__ == "__main__":
    logger.info("=== RCW Metadata Enrichment (OpenAI GPT-4o-mini) ===")
    logger.info("Using WAC-compatible format from core/ingest_documents.py")
    enrich_metadata()
