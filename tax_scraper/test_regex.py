import requests
from bs4 import BeautifulSoup
import re

# Test the chapter 08 directory
chapter_url = "https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf/RCW%20%2082%20%20TITLE/RCW%20%2082%20.%2008%20%20CHAPTER/"
response = requests.get(chapter_url)
soup = BeautifulSoup(response.text, 'html.parser')

print("=== All anchor tags in directory ===")
all_links = soup.find_all('a')
print(f"Total links: {len(all_links)}")

print("\n=== PDF links ===")
pdf_links = [a for a in all_links if a.get('href', '').endswith('.pdf')]
print(f"Total PDF links: {len(pdf_links)}")

if pdf_links:
    print("\nFirst 5 PDF links:")
    for i, link in enumerate(pdf_links[:5]):
        href = link.get('href')
        text = link.get_text(strip=True)
        print(f"{i+1}. href={href}")
        print(f"   text={text}")

print("\n=== Testing regex ===")
chapter = '08'
pattern = r'RCW\s+82\s+\.\s+' + chapter + r'\s+\.\s+\d+.*\.pdf'
print(f"Pattern: {pattern}")

regex = re.compile(pattern, re.IGNORECASE)
matched_links = soup.find_all('a', href=regex)
print(f"\nMatched links: {len(matched_links)}")

# Try matching hrefs directly
print("\n=== Testing href matching ===")
import urllib.parse
test_hrefs = [
    "/Law/RCWArchive/2025/pdf/RCW%20%2082%20%20TITLE/RCW%20%2082%20.%2008%20%20CHAPTER/RCW%20%2082%20.%2008%20.010.pdf",
    "RCW  82 . 08 .020.pdf",
    "RCW  82 . 08 .817.pdf"
]

for href in test_hrefs:
    decoded = urllib.parse.unquote(href)
    print(f"\nOriginal: {href}")
    print(f"Decoded: {decoded}")
    if re.search(pattern, decoded, re.IGNORECASE):
        print(f"MATCH!")
    else:
        print(f"NO MATCH")

print("\n=== Testing with actual link text ===")
for link in pdf_links[2:7]:  # Skip the first 2 (CHAPTER files)
    text = link.get_text(strip=True)
    if re.search(pattern, text, re.IGNORECASE):
        print(f"MATCH: {text}")
    else:
        print(f"NO MATCH: {text}")
