"""
Django Management Command: Initialize Database with Sample Data

This command populates the database with realistic sample data for development,
testing, and demonstration purposes. It creates a complete e-commerce store
with categories, products, customers, orders, and more.

The command uses Factory Boy factories to generate realistic data and includes
progress bars for better user experience during data creation.

Usage:
    python manage.py init_db                    # Create 25 of each record (default)
    python manage.py init_db --count 10        # Create 10 of each record
    python manage.py init_db --no-progress     # Disable progress bars
    python manage.py init_db --no-delete       # Skip deleting existing data

Features:
- Creates admin superuser (username: admin, password: admin1234)
- Generates realistic product catalog with categories and discounts
- Creates customer accounts with addresses
- Generates order history with order items
- Creates shopping carts with items
- Adds product reviews and comments
- Includes progress visualization with tqdm
- Handles foreign key relationships properly
"""

from django.core.management.base import BaseCommand
from tqdm import tqdm  # Progress bar library for better UX
from faker import Faker  # For generating additional random data
from store.factories import (
    CategoryFactory,
    ProductFactory,
    DiscountFactory,
    CustomUserFactory,
    SuperUserFactory,
    CustomerFactory,
    AdressFactory,
    OrderFactory,
    OrderItemFactory,
    CartFactory,
    CartItemFactory,
    CommentFactory
)
from store.models import (
    Comment,
    Cart,
    Product,
    Category,
    Discount,
    Customer,
    Adress,
    Order,
    OrderItem,
    CartItem
)
from core.models import CustomUser


class Command(BaseCommand):
    """
    Django management command to initialize the database with sample data.
    
    This command creates a complete e-commerce store dataset including:
    - Categories and products with realistic data
    - Customer accounts and addresses
    - Order history and shopping carts
    - Product reviews and comments
    
    The command includes progress visualization and handles data relationships
    properly to avoid foreign key constraint violations.
    """
    help = 'Initialize the database with fake data with progress visualization'

    def add_arguments(self, parser):
        """
        Define command-line arguments for the init_db command.
        
        Args:
            parser: ArgumentParser instance for adding command options
        """
        parser.add_argument(
            '--count',
            type=int,
            default=25,  # Increased default for better demonstration
            help='Number of each record to create (default: 25)',
        )
        parser.add_argument(
            '--no-progress',
            action='store_true',
            help='Disable progress bars (useful for CI/CD environments)',
        )
        parser.add_argument(
            '--no-delete',
            action='store_true',
            help='Skip deleting existing data (useful for incremental data addition)',
        )

    def handle(self, *args, **options):
        """
        Main execution method for the init_db command.
        
        This method orchestrates the entire data creation process:
        1. Cleans existing data (unless --no-delete is specified)
        2. Creates data in the correct order to respect foreign key constraints
        3. Shows progress for each step of the process
        4. Provides a summary of created data
        
        Args:
            *args: Variable length argument list
            **options: Command-line options (count, no_progress, no_delete)
        """
        # Initialize Faker for generating additional random data
        fake = Faker()
        
        # Extract command-line options
        count = options['count']  # Number of records to create for each model
        disable_progress = options['no_progress']  # Whether to show progress bars
        skip_delete = options['no_delete']  # Whether to skip data deletion

        # Delete all existing data first (unless --no-delete is specified)
        if not skip_delete:
            self.stdout.write(self.style.WARNING('Deleting all existing data...'))
            
            # Delete in reverse order to avoid foreign key constraints
            # We must delete child objects before parent objects to prevent
            # "Cannot delete or update a parent row" errors
            
            # Delete comments first (they reference products)
            Comment.objects.all().delete()
            
            # Delete cart items (they reference carts and products)
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            
            # Delete order items (they reference orders and products)
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            
            # Delete addresses (they reference customers)
            Adress.objects.all().delete()
            Customer.objects.all().delete()
            
            # Delete products (they reference categories and discounts)
            Product.objects.all().delete()
            Category.objects.all().delete()
            Discount.objects.all().delete()
            
            # Delete users last (they are referenced by customers)
            CustomUser.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS('All existing data deleted successfully!'))

        self.stdout.write(self.style.SUCCESS(f'Creating {count} of each model...'))

        # Create superuser (admin) - this gives you access to Django admin panel
        self.stdout.write(self.style.SUCCESS('Creating admin superuser...'))
        try:
            admin_user = SuperUserFactory()
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin_user.username}'))
        except Exception as e:
            # If admin user already exists, that's fine - just log it
            self.stdout.write(self.style.WARNING(f'Admin user already exists or error: {e}'))

        # Create discounts first (they are referenced by products)
        # Discounts are simple objects that can be created independently
        with tqdm(
            total=count,
            desc="Creating discounts",
            unit="discount",
            disable=disable_progress,
        ) as pbar:
            # Create all discounts at once for better performance
            discounts = [DiscountFactory() for _ in range(count)]
            pbar.update(count)

        # Create categories - these are the main product groupings
        categories = []
        with tqdm(
            total=count,
            desc="Creating categories",
            unit="category",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                categories.append(CategoryFactory())
                pbar.update(1)

        # Create products with progress - products depend on categories
        # Each category gets multiple products to create a realistic catalog
        products = []
        with tqdm(
            total=count * 2,  # Estimate 2 products per category
            desc="Creating products",
            unit="product",
            disable=disable_progress,
        ) as pbar:
            for category in categories:
                # Create 1-3 products per category for variety
                num_products = max(1, count // 3)
                for _ in range(num_products):
                    # Create product with the current category and first 2 discounts
                    products.append(ProductFactory(
                        category=category,
                        discount=discounts[:2]  # Add first 2 discounts to each product
                    ))
                    pbar.update(1)
                
                # Set a random product as the category's top product
                # This creates a featured product for each category
                if products:
                    category.top_product = products[-1]  # Set last created product as top
                    category.save()

        # Create customers with addresses - customers depend on users
        # Each customer gets an address to create complete customer profiles
        customers = []
        with tqdm(
            total=count * 2,  # Customers + addresses (2 records per iteration)
            desc="Creating customers & addresses",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                # Create customer (this also creates a user account)
                customer = CustomerFactory()
                customers.append(customer)
                
                # Create address for this customer
                AdressFactory(customer=customer)
                
                # Update progress bar by 2 (customer + address)
                pbar.update(2)

        # Create orders with items - orders depend on customers and products
        # Each order gets multiple items to create realistic order history
        orders = []
        with tqdm(
            total=count * 3,  # Orders + estimated items (rough estimate)
            desc="Creating orders with items",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                # Create order for a random customer
                order = OrderFactory(customer=fake.random_element(customers))
                orders.append(order)
                pbar.update(1)
                
                # Add 1-5 items to each order (ensure unique products per order)
                # This prevents duplicate products in the same order
                num_items = fake.random_int(min=1, max=min(5, len(products)))
                selected_products = fake.random_elements(products, length=num_items, unique=True)
                
                # Create order items for each selected product
                for product in selected_products:
                    OrderItemFactory(
                        order=order,
                        product=product,
                        quantity=fake.random_int(min=1, max=10)  # Random quantity 1-10
                    )
                    pbar.update(1)

        # Create carts with items - carts are independent but items depend on products
        # Carts represent current shopping sessions (not tied to specific customers)
        with tqdm(
            total=count * 3,  # Carts + estimated items (rough estimate)
            desc="Creating carts with items",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                # Create cart (this will automatically generate a UUID)
                cart = CartFactory()
                pbar.update(1)
                
                # Add 1-5 items to each cart (ensure unique products per cart)
                # This prevents duplicate products in the same cart
                num_items = fake.random_int(min=1, max=min(5, len(products)))
                selected_products = fake.random_elements(products, length=num_items, unique=True)
                
                # Create cart items for each selected product
                for product in selected_products:
                    CartItemFactory(
                        cart=cart,
                        product=product,
                        quantity=fake.random_int(min=1, max=5)  # Random quantity 1-5
                    )
                    pbar.update(1)

        # Create comments for products - comments depend on products
        # Each product gets 0-3 comments to create realistic product reviews
        total_comments = 0
        with tqdm(
            total=len(products),
            desc="Creating product comments",
            unit="product",
            disable=disable_progress,
        ) as pbar:
            for product in products:
                # Create 0-3 comments per product (some products might have no comments)
                num_comments = fake.random_int(min=0, max=3)
                
                # Use create_batch for better performance when creating multiple comments
                CommentFactory.create_batch(num_comments, product=product)
                
                # Track total comments created for summary
                total_comments += num_comments
                pbar.update(1)

        # Final summary - display statistics of all created data
        # This gives users a clear overview of what was generated
        self.stdout.write("\n" + self.style.SUCCESS('Successfully created initial data:'))
        self.stdout.write(f'- {len(categories)} categories')  # Product groupings
        self.stdout.write(f'- {len(products)} products')      # Individual items for sale
        self.stdout.write(f'- {len(discounts)} discounts')    # Price reduction offers
        self.stdout.write(f'- {CustomUser.objects.count()} users')  # User accounts (including admin)
        self.stdout.write(f'- {len(customers)} customers with addresses')  # Customer profiles
        self.stdout.write(f'- {len(orders)} orders with items')  # Purchase history
        self.stdout.write(f'- {Cart.objects.count()} carts with items')  # Shopping carts
        self.stdout.write(f'- {total_comments} comments created')  # Product reviews