from bs4 import BeautifulSoup

with open('test_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all H3 tags
h3_tags = soup.find_all('h3')
print(f"Total H3 tags: {len(h3_tags)}")

# Find the one with the title
for i, h3 in enumerate(h3_tags):
    text = h3.get_text(strip=True)
    if 'Tax imposed' in text:
        print(f"\nFound title H3 at index {i}: {text[:100]}")
        print("\nParent of H3:")
        print(f"  Tag: {h3.parent.name}")
        print(f"  Class: {h3.parent.get('class')}")
        print(f"  ID: {h3.parent.get('id')}")

        print("\nNext sibling:")
        next_sib = h3.find_next_sibling()
        if next_sib:
            print(f"  Tag: {next_sib.name}")
            print(f"  Text preview: {next_sib.get_text(strip=True)[:200]}")

        print("\nAll siblings after title:")
        for j, sib in enumerate(h3.find_next_siblings()):
            if j < 5:
                print(f"  {j}. {sib.name}: {str(sib)[:100]}...")

        print("\nParent div contents:")
        parent = h3.parent
        print(f"Parent HTML length: {len(str(parent))}")
        print(f"Parent text length: {len(parent.get_text())}")
        print(f"\nParent text preview (first 1000 chars):")
        print(parent.get_text(separator='\n', strip=True)[:1000])
        break
