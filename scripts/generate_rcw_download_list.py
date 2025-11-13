#!/usr/bin/env python3
"""
Generate a list of RCW Title 82 URLs for manual download

This script creates a downloadable text file with all RCW Title 82 section URLs.
You can then:
1. Open each URL in your browser
2. Use Print-to-PDF (Cmd/Ctrl + P)
3. Save to the rcw/ folder

This is the most reliable method when the site blocks automation.

Usage:
    python scripts/generate_rcw_download_list.py

Output:
    outputs/rcw_title_82_urls.txt - List of URLs to download
    outputs/rcw_title_82_urls.html - Clickable HTML version
"""

from pathlib import Path

# RCW Title 82 structure (as of 2025)
# Chapter numbers and common sections

RCW_TITLE_82_STRUCTURE = {
    "82.04": {
        "name": "Business and occupation tax",
        "priority": "high",
        "sections": [
            "010", "020", "030", "040", "050", "060", "070", "080", "090",
            "100", "190", "200", "210", "213", "214", "215", "216", "217",
            "220", "230", "240", "250", "260", "263", "270", "280", "290",
            "300", "310", "320", "330", "340", "350", "360", "370", "380",
            "390", "400", "410", "420", "425", "426", "427", "428", "429",
            "430", "431", "440", "450", "4266", "4268", "4269", "4270",
            "4452", "4461", "4463", "4481", "750", "760", "770"
        ]
    },
    "82.08": {
        "name": "Retail sales tax",
        "priority": "high",
        "sections": [
            "010", "020", "0201", "0203", "0204", "0205", "0206", "0207",
            "0208", "0251", "0252", "0253", "0254", "0255", "0256", "0257",
            "0258", "0259", "0261", "0262", "0263", "0264", "0265", "0266",
            "0267", "0268", "0269", "0271", "0272", "0273", "0274", "0275",
            "0276", "0277", "0278", "0279", "0281", "0282", "0283", "0284",
            "0293", "0294", "0295", "0298", "0299", "050", "060", "070",
            "080", "090", "100", "110", "120", "130", "140", "150", "160",
            "170", "180", "190", "195", "200", "210"
        ]
    },
    "82.12": {
        "name": "Use tax",
        "priority": "high",
        "sections": [
            "010", "020", "0201", "0203", "0204", "0205", "0206", "0251",
            "0252", "0253", "0254", "0255", "0256", "0257", "0258", "0259",
            "0261", "0262", "0263", "0264", "0265", "0266", "0267", "0268",
            "0269", "0271", "0272", "0273", "0274", "0275", "0276", "0277",
            "0278", "0279", "0281", "0282", "0283", "0284", "030", "040",
            "045", "050", "060", "070", "080", "090", "100"
        ]
    },
    "82.14": {
        "name": "Local retail sales and use taxes",
        "priority": "medium",
        "sections": [
            "010", "020", "030", "036", "040", "050", "060", "070", "080",
            "090", "100", "200", "210", "220", "230", "240", "250", "260",
            "270", "280", "290", "300", "310", "320", "330", "340", "350",
            "360", "370", "380", "390", "400", "410", "415", "420", "425",
            "430", "440", "450", "455", "460", "465", "470"
        ]
    },
    "82.16": {
        "name": "Public utility tax",
        "priority": "medium",
        "sections": [
            "010", "020", "030", "040", "050", "060", "070", "080", "090",
            "100", "110", "120", "130", "140", "150", "160", "170", "180",
            "190", "200"
        ]
    },
    "82.32": {
        "name": "Excise tax collection and reporting",
        "priority": "high",
        "sections": [
            "010", "020", "023", "030", "040", "045", "050", "051", "052",
            "055", "060", "062", "065", "070", "080", "085", "087", "090",
            "100", "105", "110", "117", "120", "130", "135", "140", "145",
            "150", "160", "170", "180", "190", "200", "210", "215", "220",
            "230", "235", "237", "240", "250", "260", "263", "265", "267",
            "270", "280", "290", "300", "310", "320", "330", "340", "350",
            "360", "380", "385", "390", "400", "410", "415", "420", "430"
        ]
    },
    "82.02": {
        "name": "General provisions",
        "priority": "low",
        "sections": ["010", "020", "030", "040", "050", "060", "070", "080"]
    },
    "82.24": {
        "name": "Cigarette tax",
        "priority": "low",
        "sections": ["010", "020", "025", "026", "027", "028", "030"]
    },
    "82.26": {
        "name": "Tobacco products tax",
        "priority": "low",
        "sections": ["010", "020", "030", "040", "050", "060", "070"]
    }
}


def generate_url_list(output_txt: Path, output_html: Path, priority_filter: str = None):
    """
    Generate URL lists in both text and HTML formats

    Args:
        priority_filter: 'high', 'medium', 'low', or None (all)
    """
    urls = []
    html_sections = []

    print("\n📋 Generating RCW Title 82 URL List")
    print("="*70 + "\n")

    # Generate URLs for each chapter
    for chapter, info in RCW_TITLE_82_STRUCTURE.items():
        if priority_filter and info["priority"] != priority_filter:
            continue

        chapter_name = info["name"]
        sections = info["sections"]

        print(f"Chapter {chapter}: {chapter_name}")
        print(f"  Priority: {info['priority']}")
        print(f"  Sections: {len(sections)}\n")

        # HTML section header
        html_sections.append(f"<h2>Chapter {chapter}: {chapter_name}</h2>")
        html_sections.append(f"<p><em>Priority: {info['priority']} | Sections: {len(sections)}</em></p>")
        html_sections.append("<ul>")

        for section in sections:
            full_citation = f"{chapter}.{section}"
            url = f"https://app.leg.wa.gov/rcw/default.aspx?cite={full_citation}"
            filename = f"RCW_{full_citation.replace('.', '-')}.pdf"

            urls.append(f"{url} | {filename} | RCW {full_citation} - {chapter_name}")

            html_sections.append(
                f'<li><a href="{url}" target="_blank">RCW {full_citation}</a> '
                f'<span style="color: #666;">({chapter_name})</span> '
                f'<code style="background: #f0f0f0; padding: 2px 6px; font-size: 0.9em;">{filename}</code></li>'
            )

        html_sections.append("</ul><br>")

    # Write text file
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(output_txt, 'w') as f:
        f.write("="*70 + "\n")
        f.write("RCW Title 82 - Excise Taxes\n")
        f.write("Download URLs for Manual Extraction\n")
        f.write("="*70 + "\n\n")
        f.write("Instructions:\n")
        f.write("1. Open each URL in your browser\n")
        f.write("2. Use Print-to-PDF (Cmd/Ctrl + P → Save as PDF)\n")
        f.write("3. Save with the filename shown after the URL\n")
        f.write("4. Save all PDFs to: knowledge_base/states/washington/legal_documents/rcw/\n")
        f.write("\n" + "="*70 + "\n\n")

        for url_line in urls:
            f.write(url_line + "\n")

    # Write HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RCW Title 82 - Download URLs</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #1a365d;
            border-bottom: 3px solid #3182ce;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5282;
            margin-top: 30px;
        }}
        .instructions {{
            background: #f7fafc;
            border-left: 4px solid #3182ce;
            padding: 20px;
            margin: 20px 0;
        }}
        .instructions ol {{
            margin: 10px 0;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        a {{
            color: #3182ce;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
            color: #2c5282;
        }}
        code {{
            background: #f0f0f0;
            padding: 2px 6px;
            font-size: 0.9em;
            border-radius: 3px;
        }}
        .stats {{
            background: #edf2f7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>📚 RCW Title 82 - Excise Taxes</h1>
    <p><strong>Washington State Revised Code - Download URLs</strong></p>

    <div class="instructions">
        <h3>🔽 Download Instructions</h3>
        <ol>
            <li>Click on each RCW link below (opens in new tab)</li>
            <li>Use your browser's Print function (Cmd/Ctrl + P)</li>
            <li>Select "Save as PDF" as the destination</li>
            <li>Use the filename shown next to each link</li>
            <li>Save all PDFs to: <code>knowledge_base/states/washington/legal_documents/rcw/</code></li>
        </ol>
    </div>

    <div class="stats">
        <strong>📊 Total Sections:</strong> {len(urls)}
    </div>

    {''.join(html_sections)}

    <hr style="margin: 40px 0; border: none; border-top: 1px solid #e2e8f0;">
    <p style="color: #666; font-size: 0.9em;">
        Generated by RefundEngine RCW Extraction Tool<br>
        Next step: Process PDFs with <code>python scripts/ingest_documents.py</code>
    </p>
</body>
</html>
"""

    with open(output_html, 'w') as f:
        f.write(html_content)

    # Summary
    print("="*70)
    print("✅ URL Lists Generated")
    print("="*70)
    print(f"📄 Text file: {output_txt}")
    print(f"🌐 HTML file: {output_html}")
    print(f"📊 Total sections: {len(urls)}")
    print("="*70 + "\n")

    print("📋 Next steps:")
    print(f"  1. Open {output_html} in your browser")
    print("  2. Click each link and save as PDF")
    print("  3. Save PDFs to: knowledge_base/states/washington/legal_documents/rcw/")
    print("  4. Run ingestion: python scripts/ingest_documents.py --type tax_law --folder knowledge_base/states/washington/legal_documents/rcw --export-metadata outputs/RCW_Metadata.xlsx")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate list of RCW Title 82 URLs for manual download"
    )
    parser.add_argument(
        "--priority",
        choices=['high', 'medium', 'low'],
        help="Filter by priority (high=critical tax chapters, medium=supplementary, low=other)"
    )

    args = parser.parse_args()

    output_txt = Path(__file__).parent.parent / "outputs" / "rcw_title_82_urls.txt"
    output_html = Path(__file__).parent.parent / "outputs" / "rcw_title_82_urls.html"

    generate_url_list(output_txt, output_html, priority_filter=args.priority)


if __name__ == "__main__":
    main()
