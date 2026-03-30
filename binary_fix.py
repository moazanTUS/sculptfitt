#!/usr/bin/env python3
"""Binary-level fix for emoji corruption."""

# Read the file in binary
with open('backend/static/app.js', 'rb') as f:
    data = f.read()

# These are the mojibake byte sequences we need to fix
# Format: (broken_bytes, fixed_emoji_string_utf8)
fixes = [
    (b'\xc3\xb0\xc5\xb8\xe2\x80\xb9', '🏋️'),       # 🏋️ weightlifter
    (b'\xc3\xb0\xc5\xb8\xe2\x80\x94\xe2\x80\x98', '🗑️'),  # 🗑️ wastebasket  
    (b'\xc3\xb0\xc5\xb8\xe2\x80\xb2', '👁️'),       # 👁️ eye
    (b'\xe2\x80\xa2\xc2\xb1', '⏱️'),                  # ⏱️ stopwatch
    (b'\xc3\xa2\xc2\xb1', '⏱️'),                     # variant
    (b'\xc3\xa2\xc2\x8c', '❌'),                     # ❌ cross mark
    (b'\xc3\xa2\xe2\x14', '⭐'),                     # ⭐ star 
    (b'\xc3\xa2\xc2\xa0', '⚖️'),                     # ⚖️ scale
    (b'\xc3\xa2\xc2\xb3', '⏳'),                     # ⏳ hourglass
]

print(f"Starting with {len(data)} bytes")
for broken_bytes, fixed_emoji in fixes:
    count = data.count(broken_bytes)
    if count > 0:
        data = data.replace(broken_bytes, fixed_emoji.encode('utf-8'))
        print(f"Replaced {count}x {broken_bytes.hex()} → {fixed_emoji}")

# Write back
with open('backend/static/app.js', 'wb') as f:
    f.write(data)

print(f"Finished with {len(data)} bytes")
print("✅ Done!")
