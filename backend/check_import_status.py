#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menu_engineering.settings')
django.setup()

from menu.models import MenuItem, MenuSection

print("\n✅ IMPORT STATUS REPORT")
print("=" * 50)
print(f"Total Menu Sections: {MenuSection.objects.count()}")
print(f"Total Menu Items: {MenuItem.objects.count()}")
print("\nItems by Category:")
print(f"  🌟 Star Items: {MenuItem.objects.filter(category='Star').count()}")
print(f"  🐴 Plowhorse Items: {MenuItem.objects.filter(category='Plowhorse').count()}")
print(f"  🤔 Puzzle Items: {MenuItem.objects.filter(category='Puzzle').count()}")
print(f"  🐕 Dog Items: {MenuItem.objects.filter(category='Dog').count()}")
print(f"  ❓ Unknown: {MenuItem.objects.filter(category='').count() + MenuItem.objects.filter(category__isnull=True).count()}")
print("\nTop 5 Richest Sections by Item Count:")
for section in MenuSection.objects.annotate(item_count=django.db.models.Count('items')).order_by('-item_count')[:5]:
    print(f"  {section.name}: {section.item_count} items")
print("=" * 50)
