from bs4 import BeautifulSoup

with open('test_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Look for the content div
content_div = soup.find('div', id='ContentPlaceHolder1_pnlExpanded')
print("Content div found:", content_div is not None)

if content_div:
    text = content_div.get_text(separator='\n', strip=True)
    print("Text length:", len(text))
    print("First 500 chars:", text[:500])
    print("\nHTML length:", len(str(content_div)))
    print("First 1000 chars of HTML:", str(content_div)[:1000])
