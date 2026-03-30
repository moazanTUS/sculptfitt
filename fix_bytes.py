#!/usr/bin/env python3
"""Fix mojibake by working at the byte level."""

with open('backend/static/app.js', 'rb') as f:
    data = f.read()

# The mojibake was created by: UTF-8 bytes -> interpreted as cp1252 -> re-encoded as UTF-8
# So we need to: read as UTF-8, encode to cp1252, decode as UTF-8 to reverse it
# OR: manually map the broken sequences to correct ones

# Let's try the reverse encoding approach:
# Take the corrupted UTF-8 text and decode the corruption
try:
    text = data.decode('utf-8')
    # Now for any high-byte sequences, try to reverse the double-encoding
    import re
    
    def fix_sequence(s):
        try:
            # This is text that was: emoji UTF-8 -> interpreted as cp1252 -> re-encoded as UTF-8
            # Try to reverse by: get UTF-8 bytes of the mojibake, decode as cp1252, encode back as UTF-8
            b = s.encode('utf-8')
            fixed = b.decode('cp1252').encode('utf-8').decode('utf-8')
            return fixed
        except:
            return s
    
    # Find sequences with non-ASCII chars
    pattern = re.compile(r'[^\x00-\x7f]+')
    text_fixed = pattern.sub(lambda m: fix_sequence(m.group()), text)
    
    with open('backend/static/app.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write(text_fixed)
    print("✅ Fixed!")
except Exception as e:
    print(f"Error: {e}")
