"""
Shared filtering functions for pattern extraction
Removes junk data and keeps only meaningful text-based patterns
"""
import re


def is_valid_refund_basis(value):
    """
    Filter out junk refund basis values

    REJECT:
    - PDF filenames (contains .PDF or .pdf)
    - Invoice numbers (long numeric strings)
    - Pure numeric codes
    - Single characters
    - Empty/null values

    KEEP:
    - Meaningful text patterns like "MPU", "Non-taxable", "OOS services"
    """
    if not value or value in [None, 'None', 'nan', '']:
        return False

    value_str = str(value).strip()

    # Filter out PDF filenames
    if '.PDF' in value_str.upper() or '.pdf' in value_str:
        return False

    # Filter out long numeric strings (invoice numbers like 000002909380-1.PDF without .PDF)
    if re.match(r'^\d{10,}', value_str):
        return False

    # Filter out invoice-like patterns (numbers with dashes/dots)
    if re.match(r'^\d+[-\.]\d+', value_str):
        return False

    # Filter out single characters
    if len(value_str) <= 1:
        return False

    # Filter out pure numeric
    if value_str.replace('.', '').replace(',', '').isdigit():
        return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', value_str):
        return False

    return True


def is_valid_keyword(word):
    """
    Filter out junk description keywords

    REJECT:
    - Pure numeric (002, 003, 81110000)
    - Too short (< 3 characters)
    - Common stopwords (the, and, or)
    - No letters

    KEEP:
    - Meaningful words with letters
    """
    if not word or word in [None, 'None', 'nan', '']:
        return False

    word_str = str(word).strip()

    # Filter pure numeric
    if word_str.isdigit():
        return False

    # Filter too short
    if len(word_str) < 3:
        return False

    # Filter common stopwords
    stopwords = {
        'the', 'and', 'or', 'for', 'to', 'in', 'on', 'at', 'by',
        'from', 'with', 'is', 'was', 'are', 'were', 'this', 'that',
        'see', 'per', 'but', 'then', 'not', 'can', 'will', 'all',
        'has', 'had', 'have', 'been', 'being', 'also', 'use', 'used'
    }
    if word_str.lower() in stopwords:
        return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', word_str):
        return False

    # Filter out purely punctuation or special chars
    if re.match(r'^[^\w]+$', word_str):
        return False

    return True


def is_valid_category_value(value):
    """
    Filter junk category values (Tax Category, Final Decision, Product Type, etc.)

    REJECT:
    - Pure numeric (12, 33, 90)
    - Column headers (contains "Category", "Decision", "Account")
    - Boolean values (True, False)
    - Too short (< 2 characters)
    - Empty/null

    KEEP:
    - Meaningful text categories
    """
    if not value or value in [None, 'None', 'nan', '']:
        return False

    value_str = str(value).strip()

    # Filter pure numeric
    if value_str.isdigit():
        return False

    # Filter column headers (likely headers that leaked into data)
    header_keywords = ['Category', 'Decision', 'Account', 'Group', 'Type', 'Description', 'Basis']
    if any(kw in value_str for kw in header_keywords):
        return False

    # Filter boolean values
    if value_str in ['True', 'False', 'true', 'false', 'TRUE', 'FALSE']:
        return False

    # Too short
    if len(value_str) < 2:
        return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', value_str):
        return False

    return True


def is_text_gl_description(value):
    """
    Keep only text-based GL descriptions, NOT numeric codes

    User requirement: TEXT-BASED patterns only, NO numeric codes

    REJECT:
    - Pure numeric codes (44330030, 90)
    - Codes starting with leading zeros (0123456)
    - Short values (< 3 characters)
    - No letters

    KEEP:
    - Text descriptions like "GRIR - COS/Other", "Proj - Equipment"
    """
    if not value or value in [None, 'None', 'nan', '']:
        return False

    value_str = str(value).strip()

    # Filter pure numeric codes
    if re.match(r'^\d+$', value_str):
        return False

    # Filter codes starting with leading zeros (SAP codes like 00012345)
    if re.match(r'^0+\d+$', value_str):
        return False

    # Filter short values
    if len(value_str) < 3:
        return False

    # Must contain letters (this is the key filter - text only!)
    if not re.search(r'[a-zA-Z]', value_str):
        return False

    # Filter boolean values
    if value_str in ['True', 'False', 'true', 'false']:
        return False

    return True


def is_meaningful_material_code(value):
    """
    Keep only material codes with meaningful text, not pure numeric SAP codes

    REJECT:
    - Pure numeric codes (81110000, 72000000)
    - Short codes (< 3 characters)
    - No letters

    KEEP:
    - Codes with text like "1PWR_SUP", "IOT", "2SFT_MNT"
    """
    if not value or value in [None, 'None', 'nan', '']:
        return False

    value_str = str(value).strip()

    # Filter pure numeric codes
    if value_str.isdigit():
        return False

    # Must contain letters (meaningful codes have text)
    if not re.search(r'[a-zA-Z]', value_str):
        return False

    # Minimum 3 characters
    if len(value_str) < 3:
        return False

    return True


def is_meaningful_location(value):
    """
    Keep meaningful location keywords, filter out generic words

    REJECT:
    - Common words that aren't locations
    - Pure numeric
    - Too short

    KEEP:
    - Actual place names (Bellevue, Polaris, Titan, Redmond)
    - Facility types (Data Center, Network, Cloud, AWS)
    """
    if not value or value in [None, 'None', 'nan', '']:
        return False

    value_str = str(value).strip()

    # Filter pure numeric
    if value_str.isdigit():
        return False

    # Filter too short
    if len(value_str) < 2:
        return False

    # Filter common non-location words
    non_locations = {
        'and', 'per', 'but', 'then', 'the', 'with', 'from', 'installed',
        'in', 'at', 'on', 'to', 'for', 'of', 'by'
    }
    if value_str.lower() in non_locations:
        return False

    # Must contain letters
    if not re.search(r'[a-zA-Z]', value_str):
        return False

    return True


def clean_wac_citations(examples):
    """
    Extract only actual WAC citations from examples

    Returns list of strings that contain valid WAC citation patterns
    """
    wac_pattern = re.compile(r'WAC\s+\d{3}-\d{2}-\d{3,4}[A-Z]?', re.IGNORECASE)

    valid_citations = []
    for example in examples:
        if example and wac_pattern.search(str(example)):
            valid_citations.append(str(example).strip())

    return valid_citations


# Summary of filtering philosophy:
# 1. TEXT-BASED patterns only (user requirement)
# 2. NO pure numeric codes
# 3. NO invoice numbers, PDF filenames, junk data
# 4. Must contain letters to be meaningful
# 5. Filter out column headers, boolean values
# 6. Keep only actionable, meaningful patterns for AI training
