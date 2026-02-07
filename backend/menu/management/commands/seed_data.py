from django.core.management.base import BaseCommand
from django.db import transaction
from menu.models import MenuItem, MenuSection
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seed database with sample menu items for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with sample menu items..."))

        # Sample menu data
        sections_data = [
            {
                'name': 'Appetizers',
                'description': 'Start your meal with our delicious appetizers',
                'order': 1,
                'items': [
                    {'title': 'Crispy Calamari', 'price': 14.99, 'cost': 4.50, 'purchases': 145, 'description': 'Tender calamari rings lightly breaded and fried to golden perfection, served with marinara sauce'},
                    {'title': 'Spinach Artichoke Dip', 'price': 12.99, 'cost': 3.20, 'purchases': 89, 'description': 'Creamy blend of spinach, artichokes, and melted cheeses served with tortilla chips'},
                    {'title': 'Bruschetta', 'price': 10.99, 'cost': 2.80, 'purchases': 67, 'description': 'Toasted bread topped with fresh tomatoes, basil, garlic, and balsamic glaze'},
                    {'title': 'Loaded Nachos', 'price': 15.99, 'cost': 5.00, 'purchases': 112, 'description': 'Crispy tortilla chips loaded with cheese, jalapeños, sour cream, and guacamole'},
                    {'title': 'Truffle Fries', 'price': 11.99, 'cost': 2.50, 'purchases': 34, 'description': 'Hand-cut fries tossed in truffle oil and parmesan cheese'},
                ]
            },
            {
                'name': 'Main Courses',
                'description': 'Signature dishes prepared with the finest ingredients',
                'order': 2,
                'items': [
                    {'title': 'Grilled Ribeye Steak', 'price': 38.99, 'cost': 15.00, 'purchases': 178, 'description': '12oz ribeye steak grilled to perfection, served with garlic mashed potatoes and seasonal vegetables'},
                    {'title': 'Pan-Seared Salmon', 'price': 28.99, 'cost': 11.00, 'purchases': 156, 'description': 'Fresh Atlantic salmon with lemon butter sauce, served with wild rice and asparagus'},
                    {'title': 'Chicken Parmesan', 'price': 22.99, 'cost': 7.50, 'purchases': 134, 'description': 'Breaded chicken breast topped with marinara and melted mozzarella, served over spaghetti'},
                    {'title': 'Lobster Tail', 'price': 45.99, 'cost': 22.00, 'purchases': 45, 'description': 'Butter-poached lobster tail served with drawn butter and seasonal vegetables'},
                    {'title': 'Vegetable Stir Fry', 'price': 18.99, 'cost': 5.00, 'purchases': 28, 'description': 'Fresh mixed vegetables wok-tossed in garlic ginger sauce, served over jasmine rice'},
                    {'title': 'BBQ Baby Back Ribs', 'price': 26.99, 'cost': 10.00, 'purchases': 98, 'description': 'Slow-cooked ribs glazed with house BBQ sauce, served with coleslaw and fries'},
                    {'title': 'Shrimp Scampi', 'price': 24.99, 'cost': 9.00, 'purchases': 23, 'description': 'Jumbo shrimp sautéed in garlic butter wine sauce over linguine'},
                ]
            },
            {
                'name': 'Pizzas',
                'description': 'Hand-tossed pizzas with fresh toppings',
                'order': 3,
                'items': [
                    {'title': 'Margherita Pizza', 'price': 16.99, 'cost': 4.50, 'purchases': 189, 'description': 'Classic pizza with fresh mozzarella, tomatoes, and basil on our signature crust'},
                    {'title': 'Pepperoni Supreme', 'price': 18.99, 'cost': 5.50, 'purchases': 167, 'description': 'Loaded with pepperoni, Italian sausage, and three cheeses'},
                    {'title': 'BBQ Chicken Pizza', 'price': 19.99, 'cost': 6.00, 'purchases': 78, 'description': 'Grilled chicken, red onions, cilantro with tangy BBQ sauce'},
                    {'title': 'Truffle Mushroom Pizza', 'price': 21.99, 'cost': 8.00, 'purchases': 22, 'description': 'Wild mushrooms, truffle oil, and fontina cheese - a gourmet delight'},
                ]
            },
            {
                'name': 'Burgers & Sandwiches',
                'description': 'Handcrafted burgers and sandwiches',
                'order': 4,
                'items': [
                    {'title': 'Classic Cheeseburger', 'price': 15.99, 'cost': 4.50, 'purchases': 210, 'description': 'Angus beef patty with American cheese, lettuce, tomato, and special sauce'},
                    {'title': 'Bacon Avocado Burger', 'price': 18.99, 'cost': 6.00, 'purchases': 145, 'description': 'Premium beef topped with crispy bacon, fresh avocado, and chipotle mayo'},
                    {'title': 'Philly Cheesesteak', 'price': 17.99, 'cost': 5.50, 'purchases': 89, 'description': 'Shaved ribeye with sautéed peppers, onions, and melted provolone on a hoagie roll'},
                    {'title': 'Veggie Burger', 'price': 14.99, 'cost': 3.50, 'purchases': 34, 'description': 'House-made black bean patty with avocado, sprouts, and tahini sauce'},
                ]
            },
            {
                'name': 'Desserts',
                'description': 'Sweet treats to end your meal perfectly',
                'order': 5,
                'items': [
                    {'title': 'New York Cheesecake', 'price': 9.99, 'cost': 2.50, 'purchases': 156, 'description': 'Creamy cheesecake with graham cracker crust and berry compote'},
                    {'title': 'Chocolate Lava Cake', 'price': 11.99, 'cost': 3.00, 'purchases': 134, 'description': 'Warm chocolate cake with molten center, served with vanilla ice cream'},
                    {'title': 'Tiramisu', 'price': 10.99, 'cost': 2.80, 'purchases': 89, 'description': 'Classic Italian dessert with espresso-soaked ladyfingers and mascarpone'},
                    {'title': 'Crème Brûlée', 'price': 10.99, 'cost': 2.50, 'purchases': 23, 'description': 'Vanilla bean custard with caramelized sugar crust'},
                ]
            },
            {
                'name': 'Beverages',
                'description': 'Refreshing drinks and specialty cocktails',
                'order': 6,
                'items': [
                    {'title': 'Fresh Lemonade', 'price': 4.99, 'cost': 0.80, 'purchases': 245, 'description': 'House-made lemonade with fresh lemons and mint'},
                    {'title': 'Iced Coffee', 'price': 5.99, 'cost': 1.00, 'purchases': 189, 'description': 'Cold-brewed coffee served over ice'},
                    {'title': 'Mango Smoothie', 'price': 6.99, 'cost': 1.50, 'purchases': 78, 'description': 'Fresh mango blended with yogurt and honey'},
                    {'title': 'Craft Root Beer', 'price': 4.49, 'cost': 0.60, 'purchases': 56, 'description': 'Small-batch root beer with vanilla undertones'},
                ]
            },
        ]

        def classify_item(price, cost, purchases):
            """Classify item using Menu Engineering Matrix"""
            margin = float(price) - float(cost)
            avg_margin = 8.0  # Average margin threshold
            avg_popularity = 80  # Average popularity threshold
            
            high_margin = margin >= avg_margin
            high_popularity = purchases >= avg_popularity
            
            if high_margin and high_popularity:
                return 'star'
            elif not high_margin and high_popularity:
                return 'plowhorse'
            elif high_margin and not high_popularity:
                return 'puzzle'
            else:
                return 'dog'

        try:
            with transaction.atomic():
                created_items = 0
                
                for section_data in sections_data:
                    # Create or get section
                    section, _ = MenuSection.objects.get_or_create(
                        name=section_data['name'],
                        defaults={
                            'description': section_data['description'],
                            'display_order': section_data['order'],
                            'is_active': True
                        }
                    )
                    
                    for item_data in section_data['items']:
                        price = Decimal(str(item_data['price']))
                        cost = Decimal(str(item_data['cost']))
                        purchases = item_data['purchases']
                        
                        # Calculate derived values
                        revenue = price * purchases
                        profit = (price - cost) * purchases
                        
                        # Classify the item
                        category = classify_item(price, cost, purchases)
                        
                        # Create the menu item
                        item, created = MenuItem.objects.update_or_create(
                            title=item_data['title'],
                            section=section,
                            defaults={
                                'description': item_data['description'],
                                'price': price,
                                'cost': cost,
                                'total_purchases': purchases,
                                'total_revenue': revenue,
                                'total_profit': profit,
                                'category': category,
                                'ai_confidence': round(random.uniform(0.75, 0.98), 2),
                                'is_active': True,
                            }
                        )
                        
                        if created:
                            created_items += 1

                self.stdout.write(self.style.SUCCESS(
                    f"Successfully seeded database!\n"
                    f"  - {len(sections_data)} sections\n"
                    f"  - {created_items} new menu items created"
                ))
                
                # Print summary by category
                for cat in ['star', 'puzzle', 'plowhorse', 'dog']:
                    count = MenuItem.objects.filter(category=cat).count()
                    self.stdout.write(f"  - {cat.capitalize()}s: {count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding database: {e}"))
            raise
