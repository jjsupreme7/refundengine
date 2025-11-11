import requests
from bs4 import BeautifulSoup

# Test parsing of a known RCW section
url = 'https://app.leg.wa.gov/RCW/default.aspx?cite=82.08.020'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

print("=== Looking for main content ===")
main = soup.find('main')
if main:
    print(f"Found main tag: {str(main)[:500]}...")
else:
    print("No main tag")

print("\n=== Looking for H4 (section title) ===")
h4 = soup.find('h4')
if h4:
    print(f"H4: {h4.get_text(strip=True)}")
else:
    print("No H4 found")

print("\n=== Checking for different content areas ===")
# Check for common container classes
for class_name in ['content', 'section-content', 'law-content', 'rcw-content']:
    div = soup.find('div', class_=class_name)
    if div:
        print(f"Found div with class '{class_name}'")

print("\n=== Searching in all text ===")
all_text = soup.get_text()
search_terms = ['Tax imposed', 'retail sale', 'shall collect']
for term in search_terms:
    idx = all_text.find(term)
    if idx != -1:
        print(f"\nFound '{term}' at position {idx}")
        print(f"Context: ...{all_text[max(0,idx-30):idx+100]}...")
        break

print("\n=== Checking for numbered lists (ol) ===")
ols = soup.find_all('ol')
print(f"Found {len(ols)} ordered lists")
if ols:
    print(f"First OL: {str(ols[0])[:300]}...")

print("\n=== Saving HTML to file for inspection ===")
with open('test_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Saved to test_page.html")

print("\n=== Looking for all H tags ===")
for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
    elements = soup.find_all(tag)
    if elements:
        print(f"\n{tag.upper()} tags found: {len(elements)}")
        for elem in elements[:3]:
            print(f"  - {elem.get_text(strip=True)[:100]}")
