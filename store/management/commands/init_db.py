from django.core.management.base import BaseCommand
from tqdm import tqdm
from faker import Faker
from store.factories import (
    CategoryFactory,
    ProductFactory,
    DiscountFactory,
    CustomerFactory,
    AddressFactory,
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


class Command(BaseCommand):
    help = 'Initialize the database with fake data with progress visualization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,  # Reduced from 50 to create fewer products
            help='Number of each record to create (default: 20)',
        )
        parser.add_argument(
            '--no-progress',
            action='store_true',
            help='Disable progress bars (useful for CI/CD)',
        )
        parser.add_argument(
            '--no-delete',
            action='store_true',
            help='Skip deleting existing data',
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        disable_progress = options['no_progress']
        skip_delete = options['no_delete']

        # Delete all existing data first (unless --no-delete is specified)
        if not skip_delete:
            self.stdout.write(self.style.WARNING('Deleting all existing data...'))
            
            # Delete in reverse order to avoid foreign key constraints
            Comment.objects.all().delete()
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Adress.objects.all().delete()
            Customer.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Discount.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS('All existing data deleted successfully!'))

        self.stdout.write(self.style.SUCCESS(f'Creating {count} of each model...'))

        # Create discounts
        with tqdm(
            total=count,
            desc="Creating discounts",
            unit="discount",
            disable=disable_progress,
        ) as pbar:
            discounts = [DiscountFactory() for _ in range(count)]
            pbar.update(count)

        # Create categories
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

        # Create products with progress
        products = []
        with tqdm(
            total=count * 2,  # Estimate 2 products per category
            desc="Creating products",
            unit="product",
            disable=disable_progress,
        ) as pbar:
            for category in categories:
                # Create 1-3 products per category
                num_products = max(1, count // 3)
                for _ in range(num_products):
                    products.append(ProductFactory(
                        category=category,
                        discount=discounts[:2]  # Add first 2 discounts
                    ))
                    pbar.update(1)
                
                # Set a random product as the category's top product
                if products:
                    category.top_product = products[-1]  # Set last created product
                    category.save()

        # Create customers with addresses
        customers = []
        with tqdm(
            total=count * 2,  # Customers + addresses
            desc="Creating customers & addresses",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                customer = CustomerFactory()
                customers.append(customer)
                AddressFactory(customer=customer)
                pbar.update(2)

        # Create orders with items
        orders = []
        with tqdm(
            total=count * 3,  # Orders + estimated items
            desc="Creating orders with items",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                order = OrderFactory(customer=fake.random_element(customers))
                orders.append(order)
                pbar.update(1)
                
                # Add 1-5 items to each order (ensure unique products per order)
                num_items = fake.random_int(min=1, max=min(5, len(products)))
                selected_products = fake.random_elements(products, length=num_items, unique=True)
                for product in selected_products:
                    OrderItemFactory(
                        order=order,
                        product=product,
                        quantity=fake.random_int(min=1, max=10)
                    )
                    pbar.update(1)

        # Create carts with items
        with tqdm(
            total=count * 3,  # Carts + estimated items
            desc="Creating carts with items",
            unit="record",
            disable=disable_progress,
        ) as pbar:
            for _ in range(count):
                cart = CartFactory()  # This will automatically generate a UUID
                pbar.update(1)
                
                # Add 1-5 items to each cart (ensure unique products per cart)
                num_items = fake.random_int(min=1, max=min(5, len(products)))
                selected_products = fake.random_elements(products, length=num_items, unique=True)
                for product in selected_products:
                    CartItemFactory(
                        cart=cart,
                        product=product,
                        quantity=fake.random_int(min=1, max=5)
                    )
                    pbar.update(1)

        # Create comments for products
        total_comments = 0
        with tqdm(
            total=len(products),
            desc="Creating product comments",
            unit="product",
            disable=disable_progress,
        ) as pbar:
            for product in products:
                # Create 0-3 comments per product
                num_comments = fake.random_int(min=0, max=3)
                CommentFactory.create_batch(num_comments, product=product)
                total_comments += num_comments
                pbar.update(1)

        # Final summary
        self.stdout.write("\n" + self.style.SUCCESS('Successfully created initial data:'))
        self.stdout.write(f'- {len(categories)} categories')
        self.stdout.write(f'- {len(products)} products')
        self.stdout.write(f'- {len(discounts)} discounts')
        self.stdout.write(f'- {len(customers)} customers with addresses')
        self.stdout.write(f'- {len(orders)} orders with items')
        self.stdout.write(f'- {Cart.objects.count()} carts with items')
        self.stdout.write(f'- {total_comments} comments created')