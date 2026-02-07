import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from menu.models import MenuItem

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
                        
                        items_to_create.append(MenuItem(
                            external_id=row['item_id'],
                            title=row['item_name'],
                            price=clean_num(row['price']),
                            total_purchases=purchases,
                            total_revenue=clean_num(row['revenue']),
                            total_profit=clean_num(row['profit']),
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