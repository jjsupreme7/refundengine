test = 'RCW  82 . 08 .010.pdf'
print('String:', repr(test))
print('\nCharacters:')
for i, char in enumerate(test):
    print(f'{i}: {repr(char)} (space={char==" "})')

# Check if the spacing is consistent
import re
# The actual spacing is "RCW  82 . 08 .010.pdf"
# So: RCW + 2 spaces + 82 + space + dot + space + 08 + space + dot + 010 + dot + pdf

# Correct pattern
pattern = r'RCW\s+82\s+\.\s+08\s+\.(\d+)'
match = re.search(pattern, test)
print(f'\nPattern: {pattern}')
print(f'Match: {match}')

# Even simpler - just check for the PDF extension and skip the CHAPTER ones
simple_pattern = r'82\s+\.\s+08\s+\.(\d+[A-Za-z]*)\.pdf$'
match2 = re.search(simple_pattern, test)
print(f'\nSimple pattern: {simple_pattern}')
print(f'Match: {match2}')
if match2:
    print(f'Section number: {match2.group(1)}')
