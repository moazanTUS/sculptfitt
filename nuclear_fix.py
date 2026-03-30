#!/usr/bin/env python3
"""Nuclear option: read as binary, fix the corruption, write clean UTF-8."""
import sys

# Step 1: Read the broken file
with open('backend/static/app.js', 'rb') as f:
    raw_bytes = f.read()

# Step 2: Try to decode properly
# The file was originally UTF-8 but got corrupted through double-encoding
# Let's try UTF-8 first
try:
    text = raw_bytes.decode('utf-8')
    print("✓ File is valid UTF-8")
except UnicodeDecodeError as e:
    print(f"✗ UTF-8 decode failed: {e}")
    # Try to salvage with error handling
    text = raw_bytes.decode('utf-8', errors='replace')

# Step 3: Map broken sequences to correct ones
# These were created by taking emoji, encoding to UTF-8, then interpreting as cp1252 and re-encoding to UTF-8
broken_to_fixed = {
    'ðŸ‹ï¸': '🏋️',       # Line 4438 - weightlifter emoji on exercise cards
    'ðŸ—\'ï¸': '🗑️',     # Line 1378, 3961, 4133 - delete/trash icon
    'ðŸ'ï¸': '👁️',       # Line 4517 - eye icon (views)
    'â±ï¸': '⏱️',         # Line 3715, 3807, 4516 - stopwatch/timer
    'â­': '⭐',           # Line 3807 - star rating
    'âŒ': '❌',           # Line 4509 - cross/common mistakes
    'âš–ï¸': '⚖️',        # Line 3919 - weight scale
    'â³': '⏳',           # Line 3807 - hourglass timer
}

count = 0
for broken, fixed in broken_to_fixed.items():
    if broken in text:
        num = text.count(broken)
        text = text.replace(broken, fixed)
        count += num
        print(f"Fixed {num}x: '{broken}' → '{fixed}'")

# Step 4: Write back as clean UTF-8 (no BOM)
with open('backend/static/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print(f"\nTotal replacements: {count}")
print("✅ File fixed and saved as clean UTF-8!")

# Verify
with open('backend/static/app.js', 'r', encoding='utf-8') as f:
    verify = f.read()
    print(f"Verification: File now contains 🏋️? {('🏋️' in verify)}")
    print(f"             File now contains 🗑️? {('🗑️' in verify)}")
