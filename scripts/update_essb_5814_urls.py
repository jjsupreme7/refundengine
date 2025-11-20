#!/usr/bin/env python3
"""
Update file_url for ESSB 5814 Documents

Adds official WA DOR URLs to ESSB 5814 documents in the database
"""

from core.database import get_supabase_client
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Load environment
load_dotenv()

# Initialize Supabase
supabase = get_supabase_client()


# Mapping of document titles/keywords to official DOR URLs
ESSB_5814_URL_MAPPINGS = [
    {
        "keywords": ["advertising services", "advertising"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-advertising-services",
    },
    {
        "keywords": ["custom software"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-custom-software",
    },
    {
        "keywords": ["website development", "custom website"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-custom-website-development-services",
    },
    {
        "keywords": ["information technology", "IT services"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-information-technology-services",
    },
    {
        "keywords": ["security services", "investigation", "armored car"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-investigation-security-security",
    },
    {
        "keywords": ["live presentations"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-live-presentations",
    },
    {
        "keywords": ["temporary staffing"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-temporary-staffing-services",
    },
    {
        "keywords": ["contracts existing", "contracts prior"],
        "url": "https://dor.wa.gov/laws-rules/interim-guidance-statement-regarding-contracts-existing-prior-october-1-2025-and-changes-made-essb",
    },
    {
        "keywords": ["DAS exclusions", "retail sale"],
        "url": "https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-das-exclusions-and-definition-retail",
    },
    {
        "keywords": ["frequently asked", "FAQs"],
        "url": "https://dor.wa.gov/taxes-rates/retail-sales-tax/services-newly-subject-retail-sales-tax/frequently-asked-questions-about-essb-5814",
    },
    {
        "keywords": ["services newly subject"],
        "url": "https://dor.wa.gov/taxes-rates/retail-sales-tax/services-newly-subject-retail-sales-tax",
    },
]


def update_essb_5814_urls():
    """Update file_url for all ESSB 5814 documents"""

    print("=" * 80)
    print("UPDATING ESSB 5814 DOCUMENT URLs")
    print("=" * 80)
    print()

    # Get all ESSB 5814 documents without file_url
    result = (
        supabase.table("knowledge_documents")
        .select("id, title, citation, file_url")
        .like("citation", "%ESSB 5814%")
        .execute()
    )

    documents = result.data
    print(f"📊 Found {len(documents)} ESSB 5814 documents")
    print()

    updated_count = 0
    skipped_count = 0
    no_match_count = 0

    for doc in documents:
        doc_id = doc["id"]
        title = doc.get("title", "")
        citation = doc.get("citation", "")
        current_url = doc.get("file_url")

        print(f"📄 {title}")
        print(f"   Citation: {citation}")

        # Skip if already has URL
        if current_url:
            print(f"   ✅ Already has URL: {current_url}")
            skipped_count += 1
            print()
            continue

        # Find matching URL
        matched_url = None
        title_lower = title.lower()

        for mapping in ESSB_5814_URL_MAPPINGS:
            if any(keyword.lower() in title_lower for keyword in mapping["keywords"]):
                matched_url = mapping["url"]
                break

        if matched_url:
            # Update the document
            try:
                supabase.table("knowledge_documents").update(
                    {"file_url": matched_url}
                ).eq("id", doc_id).execute()

                print(f"   ✅ Updated with URL: {matched_url}")
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Error updating: {e}")
        else:
            print("   ⚠️  No URL mapping found")
            no_match_count += 1

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Updated: {updated_count}")
    print(f"⏭️  Skipped (already has URL): {skipped_count}")
    print(f"⚠️  No match found: {no_match_count}")
    print(f"📊 Total: {len(documents)}")
    print()


if __name__ == "__main__":
    update_essb_5814_urls()
