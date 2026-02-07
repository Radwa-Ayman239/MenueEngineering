#!/usr/bin/env python3
"""Quick script to fix test URL namespaces"""
import re

def fix_test_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace all reverse() calls with menu namespace
    replacements = [
        (r'reverse\("section-', 'reverse("menu:section-'),
        (r'reverse\("item-', 'reverse("menu:item-'),
        (r'reverse\("order-', 'reverse("menu:order-'),
        (r'reverse\("activity-', 'reverse("menu:activity-'),
        (r'reverse\("public-', 'reverse("menu:public-'),
        (r'reverse\("ml-', 'reverse("menu:ml-'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

# Fix the test files
fix_test_file('menu/tests/test_views.py')

