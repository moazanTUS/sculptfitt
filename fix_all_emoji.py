#!/usr/bin/env python3
"""Fix all mojibake emoji in app.js using correct replacements."""

with open('backend/static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Map of broken sequences to correct emoji
replacements = {
    'ðŸ‹ï¸': '🏋️',      # Weightlifter (exercise cards)
    'ðŸ—\'ï¸': '🗑️',    # Wastebasket (delete buttons)
    'ðŸ'ï¸': '👁️',      # Eye (views)
    'â±ï¸': '⏱️',        # Stopwatch (timer/duration)
    'âŒ': '❌',          # Cross mark (common mistakes)
    'â­': '⭐',          # Star (rating)
    'âš–ï¸': '⚖️',       # Balance scale (weight)
    'â³': '⏳',          # Hourglass (status)
}

print("Fixing mojibake in app.js...")
fixes = 0
for broken, correct in replacements.items():
    if broken in content:
        count = content.count(broken)
        content = content.replace(broken, correct)
        fixes += count
        print(f"  Replaced {count}x '{broken}' → '{correct}'")

# Write back
with open('backend/static/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"\nTotal fixes: {fixes}")
print("✅ Done! All emoji should now display correctly.")
