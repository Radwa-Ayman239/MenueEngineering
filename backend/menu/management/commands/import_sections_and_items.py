import csv
import logging
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from menu.models import MenuItem, MenuSection

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import menu sections and items from CSV files with automatic section assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing sections and items before importing',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🔄 Starting complete menu import from cleaned data..."))
        
        try:
            # Step 1: Create menu sections from cleaned data
            self.import_sections_from_cleaned_data()
            
            # Step 2: Import menu items from cleaned data
            self.import_items_from_cleaned_data(clear=options.get('clear', False))
            
            # Step 3: Optionally enrich with menu engineering classifications
            self.enrich_with_menu_engineering_data()
            
            self.stdout.write(self.style.SUCCESS("✅ Import completed successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Critical Error: {e}"))
            logger.exception("Import failed")

    def import_sections_from_cleaned_data(self):
        """Import menu sections from dim_menu_sections_cleaned.csv"""
        self.stdout.write(self.style.NOTICE("📁 Importing menu sections from cleaned data..."))
        
        # Try multiple paths for the cleaned sections file
        # Docker: /code/Data Analysis/Datasets/
        # Local: Data Analysis/Datasets/
        possible_paths = [
            Path("/code/Data Analysis/Datasets/dim_menu_sections_cleaned.csv"),
            Path("../Data Analysis/Datasets/dim_menu_sections_cleaned.csv"),
            Path(__file__).resolve().parent.parent.parent.parent.parent / "Data Analysis" / "Datasets" / "dim_menu_sections_cleaned.csv",
        ]
        
        sections_file = None
        for path in possible_paths:
            if path.exists():
                sections_file = path
                break
        
        if not sections_file:
            self.stdout.write(self.style.WARNING(f"  ⚠️  Cleaned sections file not found"))
            self.stdout.write(self.style.NOTICE("  Using default sections instead..."))
            self.import_sections()
            return
        
        try:
            section_map = {}
            section_count = 0
            with open(sections_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                with transaction.atomic():
                    for row in reader:
                        ext_id = row.get('id')
                        name = row.get('title', 'Unknown')
                        
                        section, created = MenuSection.objects.get_or_create(
                            name=name,
                            defaults={
                                'description': '',
                                'display_order': 0,
                                'is_active': True
                            }
                        )
                        section_map[ext_id] = section
                        
                        if created:
                            section_count += 1
            
            total = MenuSection.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Sections: {total} total ({section_count} new)")
            )
            return section_map
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error importing sections: {e}"))
            logger.exception("Section import failed")
            self.import_sections()  # Fallback to defaults

    def import_items_from_cleaned_data(self, clear=False):
        """Import menu items from dim_menu_items_cleaned.csv"""
        self.stdout.write(self.style.NOTICE("🍽️  Importing menu items from cleaned data..."))
        
        # Try multiple paths for the cleaned items file
        # Docker: /code/Data Analysis/Datasets/
        # Local: Data Analysis/Datasets/
        possible_paths = [
            Path("/code/Data Analysis/Datasets/dim_menu_items_cleaned.csv"),
            Path("../Data Analysis/Datasets/dim_menu_items_cleaned.csv"),
            Path(__file__).resolve().parent.parent.parent.parent.parent / "Data Analysis" / "Datasets" / "dim_menu_items_cleaned.csv",
        ]
        
        items_file = None
        for path in possible_paths:
            if path.exists():
                items_file = path
                break
        
        if not items_file:
            self.stdout.write(self.style.WARNING(f"  ⚠️  Cleaned items file not found, using backend CSV..."))
            self.import_items(clear)
            return
        
        # Build section map
        section_map = {}
        for section in MenuSection.objects.all():
            section_map[section.name] = section
        
        default_section = MenuSection.objects.first()
        
        try:
            with open(items_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                items_to_create = []
                row_count = 0
                
                def clean_num(val):
                    if not val or str(val).strip() == "":
                        return 0.0
                    try:
                        return float(str(val).strip().replace(',', ''))
                    except ValueError:
                        return 0.0
                
                with transaction.atomic():
                    if clear:
                        MenuItem.objects.all().delete()
                        self.stdout.write(self.style.WARNING("  🗑️  Cleared existing items"))
                    
                    for row in reader:
                        row_count += 1
                        try:
                            item_id = row.get('id')
                            section_id = row.get('section_id')
                            title = row.get('title', 'Unknown')
                            
                            # Find section by ID or use default
                            section = default_section
                            for sec in MenuSection.objects.all():
                                if str(sec.id) == str(section_id):
                                    section = sec
                                    break
                            
                            items_to_create.append(MenuItem(
                                external_id=int(clean_num(item_id)),
                                title=title,
                                description='',
                                price=clean_num(row.get('price', 0)),
                                cost=0,  # Will be enriched from engineering data
                                section=section,
                                total_purchases=int(clean_num(row.get('purchases', 0))),
                                total_revenue=0,  # Will be enriched
                                total_profit=0,  # Will be enriched
                                category='Dog',  # Will be enriched
                                display_order=int(clean_num(row.get('index', 0))),
                                is_active=True
                            ))
                            
                            # Batch create every 1000 items
                            if len(items_to_create) >= 1000:
                                MenuItem.objects.bulk_create(items_to_create, ignore_conflicts=True)
                                self.stdout.write(
                                    self.style.SUCCESS(f"  ✓ Imported {len(items_to_create)} items...")
                                )
                                items_to_create = []
                        
                        except Exception as e:
                            logger.error(f"Error processing item {row.get('id')}: {e}")
                            continue
                    
                    # Final batch
                    if items_to_create:
                        MenuItem.objects.bulk_create(items_to_create, ignore_conflicts=True)
                
                total_items = MenuItem.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Items imported: {total_items} total")
                )
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error importing items: {e}"))
            logger.exception("Item import failed")
            raise

    def enrich_with_menu_engineering_data(self):
        """Enrich items with menu engineering classifications and profit data"""
        self.stdout.write(self.style.NOTICE("🤖 Enriching items with menu engineering data..."))
        
        # Try multiple paths for the engineering file
        # Docker: /app/menu_engineering_input_items.csv
        # Local: backend/menu_engineering_input_items.csv or just menu_engineering_input_items.csv
        possible_paths = [
            Path("/app/menu_engineering_input_items.csv"),
            Path("menu_engineering_input_items.csv"),
            Path(__file__).resolve().parent.parent.parent / "menu_engineering_input_items.csv",
        ]
        
        engineering_file = None
        for path in possible_paths:
            if path.exists():
                engineering_file = path
                break
        
        if not engineering_file:
            self.stdout.write(self.style.WARNING(f"  ⚠️  Engineering file not found, skipping enrichment..."))
            return
        
        try:
            updated_count = 0
            with open(engineering_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                def clean_num(val):
                    if not val or str(val).strip() == "":
                        return 0.0
                    try:
                        return float(str(val).strip().replace(',', ''))
                    except ValueError:
                        return 0.0
                
                for row in reader:
                    try:
                        ext_id = int(clean_num(row.get('item_id', 0)))
                        item = MenuItem.objects.filter(external_id=ext_id).first()
                        
                        if item:
                            item.category = row.get('category', 'Dog')
                            item.total_revenue = clean_num(row.get('revenue', 0))
                            item.total_profit = clean_num(row.get('profit', 0))
                            item.cost = clean_num(row.get('cost', 0))
                            item.description = row.get('description', item.description)
                            item.save()
                            updated_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error enriching item {row.get('item_id')}: {e}")
                        continue
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Enhanced {updated_count} items with engineering data")
            )
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Could not enrich with engineering data: {e}"))
            logger.warning("Engineering enrichment skipped")

    def import_sections(self):
        """Fallback: Create default menu sections"""
        self.stdout.write(self.style.NOTICE("📁 Setting up default menu sections..."))
        
        default_sections = [
            {"name": "Appetizers", "description": "Starters and appetizers", "order": 1},
            {"name": "Main Courses", "description": "Main dishes", "order": 2},
            {"name": "Burgers", "description": "Burger selections", "order": 3},
            {"name": "Beverages", "description": "Drinks and beverages", "order": 4},
            {"name": "Alcoholic Drinks", "description": "Beer, wine, and spirits", "order": 5},
            {"name": "Desserts", "description": "Desserts and sweets", "order": 6},
            {"name": "Sides", "description": "Side dishes", "order": 7},
        ]
        
        created_count = 0
        with transaction.atomic():
            for section_data in default_sections:
                section, created = MenuSection.objects.get_or_create(
                    name=section_data['name'],
                    defaults={
                        'description': section_data['description'],
                        'display_order': section_data['order'],
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Default sections created: {created_count} new")
        )

    def import_items(self, clear=False):
        """Fallback: Import from backend CSV file"""
        self.stdout.write(self.style.NOTICE("🍽️  Importing menu items from backend CSV..."))
        
        # Try multiple paths for the backend CSV file
        # Docker: /app/menu_engineering_input_items.csv  
        # Local: menu_engineering_input_items.csv
        possible_paths = [
            Path("/app/menu_engineering_input_items.csv"),
            Path("menu_engineering_input_items.csv"),
            Path(__file__).resolve().parent.parent.parent / "menu_engineering_input_items.csv",
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            raise FileNotFoundError("menu_engineering_input_items.csv not found in any expected location")
        
        default_section = MenuSection.objects.first()
        
        if not default_section:
            raise ValueError("No menu sections found.")
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                items_to_create = []
                row_count = 0
                
                def clean_num(val):
                    if not val or str(val).strip() == "":
                        return 0.0
                    try:
                        return float(str(val).strip().replace(',', ''))
                    except ValueError:
                        return 0.0
                
                with transaction.atomic():
                    if clear:
                        MenuItem.objects.all().delete()
                    
                    for row in reader:
                        row_count += 1
                        try:
                            items_to_create.append(MenuItem(
                                external_id=int(clean_num(row.get('item_id', 0))),
                                title=row.get('item_name', 'Unknown'),
                                description=row.get('description', ''),
                                price=clean_num(row.get('price', 0)),
                                cost=clean_num(row.get('cost', 0)),
                                section=default_section,
                                total_purchases=int(clean_num(row.get('purchases', 0))),
                                total_revenue=clean_num(row.get('revenue', 0)),
                                total_profit=clean_num(row.get('profit', 0)),
                                category=row.get('category', 'Dog'),
                                display_order=0,
                                is_active=True
                            ))
                            
                            if len(items_to_create) >= 1000:
                                MenuItem.objects.bulk_create(items_to_create, ignore_conflicts=True)
                                self.stdout.write(
                                    self.style.SUCCESS(f"  ✓ Imported {len(items_to_create)} items...")
                                )
                                items_to_create = []
                        
                        except Exception as e:
                            logger.error(f"Error processing row {row_count}: {e}")
                            continue
                    
                    if items_to_create:
                        MenuItem.objects.bulk_create(items_to_create, ignore_conflicts=True)
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Items imported: {MenuItem.objects.count()} total")
                )
        
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ CSV file not found: {e}")
            )
            raise
