import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from menu.models import MenuItem, MenuSection

class Command(BaseCommand):
    help = 'Professional high-speed import for Menu Engineering Data'

    def handle(self, *args, **options):
        file_path = 'menu_engineering_input_items.csv'
        self.stdout.write(self.style.NOTICE(f"Starting optimized import from {file_path}..."))

        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                items_to_create = []
                
                # Helper to prevent crashes on empty or malformed numbers
                def clean_num(val):
                    if not val or val.strip() == "":
                        return 0.0
                    try:
                        # Convert to float first to handle strings like '30.0'
                        return float(val.strip().replace(',', ''))
                    except ValueError:
                        return 0.0

                # Use a transaction to make it 10x faster
                with transaction.atomic():
                    # Optional: Clear existing items if you want a fresh start
                    # MenuItem.objects.all().delete()

                    for row in reader:
                        # Convert purchases to int safely
                        purchases = int(clean_num(row.get('purchases', 0)))
                        
                        # Get or create a default section for imported items
                        default_section, _ = MenuSection.objects.get_or_create(
                            name="Imported Items",
                            defaults={"description": "Items imported from CSV", "display_order": 99}
                        )

                        # Calculate cost since it's required (Price - (Profit / Purchases) = Cost approx)
                        # Or if we have total profit and total revenue:
                        # Margin = Total Profit / Total Purchases
                        # Cost = Price - Margin
                        price = clean_num(row['price'])
                        total_profit = clean_num(row['profit'])
                        
                        cost = 0.0
                        if purchases > 0:
                            margin_per_unit = total_profit / purchases
                            cost = max(0, price - margin_per_unit)
                        
                        items_to_create.append(MenuItem(
                            external_id=row['item_id'],
                            title=row['item_name'],
                            price=price,
                            cost=cost, # Calculated cost
                            section=default_section, # Required field
                            total_purchases=purchases,
                            total_revenue=clean_num(row['revenue']),
                            total_profit=total_profit,
                            category=row['category'] if row['category'] else 'Dog',
                            description=row.get('description', ''),
                            is_active=True
                        ))

                    # bulk_create sends ONE query instead of hundreds
                    # ignore_conflicts=True skips items that already exist based on external_id
                    MenuItem.objects.bulk_create(items_to_create, ignore_conflicts=True)

                self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(items_to_create)} items in one batch."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("CSV file not found in the backend directory."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical Error: {e}"))