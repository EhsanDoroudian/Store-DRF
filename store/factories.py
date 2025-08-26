"""
Django Factory Boy Factories for Store Models

This module contains factory classes for creating test data and sample instances
of all models in the store application. These factories use the Factory Boy library
to generate realistic fake data for development, testing, and database seeding.

Key Concepts:
- Factory Boy: A library that helps create test data and model instances
- Faker: Generates realistic fake data (names, addresses, prices, etc.)
- SubFactory: Creates related objects automatically
- LazyAttribute: Sets attributes based on other attributes when creating objects
- Post-generation: Runs custom logic after object creation

Usage Examples:
    # Create a single instance
    product = ProductFactory()
    
    # Create multiple instances
    products = ProductFactory.create_batch(5)
    
    # Create with specific attributes
    product = ProductFactory(name="Laptop", price=999.99)
    
    # Create related objects
    order = OrderFactory(customer=existing_customer)

Available Factories:
- CustomUserFactory: Creates regular users
- SuperUserFactory: Creates admin users (username: admin, password: admin1234)
- CategoryFactory: Creates product categories
- DiscountFactory: Creates discount offers
- ProductFactory: Creates products with categories and discounts
- CustomerFactory: Creates customers with user accounts
- AdressFactory: Creates customer addresses
- OrderFactory: Creates customer orders
- OrderItemFactory: Creates order line items
- CartFactory: Creates shopping carts
- CartItemFactory: Creates cart line items
- CommentFactory: Creates product reviews/comments
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils.text import slugify
from core.models import CustomUser
from .models import *

# Initialize Faker for generating realistic fake data
fake = Faker()

class CustomUserFactory(DjangoModelFactory):
    """
    Factory for creating CustomUser instances with fake data.
    
    This factory generates realistic user data including:
    - Random username, first name, last name, and email
    - Sets a default password that can be used for testing
    
    Usage:
        # Create a single user
        user = CustomUserFactory()
        
        # Create multiple users
        users = CustomUserFactory.create_batch(5)
        
        # Create user with specific attributes
        user = CustomUserFactory(first_name="John", last_name="Doe")
    """
    class Meta:
        model = CustomUser

    # Generate random username using Faker
    username = factory.Faker('user_name')
    
    # Generate random first and last names
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    
    # Generate random email address
    email = factory.Faker('email')
    
    # Set password using Django's set_password method for proper hashing
    # This ensures the password is properly encrypted before saving
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class SuperUserFactory(DjangoModelFactory):
    """
    Factory for creating superuser instances with predefined credentials.
    
    This factory creates a superuser with:
    - Username: 'admin'
    - Password: 'admin1234'
    - Staff and superuser privileges enabled
    
    Usage:
        # Create the admin superuser
        admin_user = SuperUserFactory()
        
        # This will create a user with username 'admin' and password 'admin1234'
        # that has full administrative access to the Django admin panel
    """
    class Meta:
        model = CustomUser

    # Set fixed username for admin user
    username = 'admin'
    
    # Set fixed first and last names
    first_name = 'Admin'
    last_name = 'User'
    
    # Set fixed email
    email = 'admin@example.com'
    
    # Enable staff and superuser privileges
    is_staff = True
    is_superuser = True
    
    # Set password using Django's set_password method
    password = factory.PostGenerationMethodCall('set_password', 'admin1234')

class CategoryFactory(DjangoModelFactory):
    """
    Factory for creating Category instances with fake data.
    
    This factory generates realistic category data including:
    - Random title (single word)
    - Random description (10-word sentence)
    - Note: top_product is set separately after product creation
    
    Usage:
        # Create a single category
        category = CategoryFactory()
        
        # Create multiple categories
        categories = CategoryFactory.create_batch(5)
        
        # Create category with specific title
        category = CategoryFactory(title="Electronics")
    """
    class Meta:
        model = Category

    # Generate random category title (single word)
    title = factory.Faker('word')
    
    # Generate random description (10-word sentence)
    description = factory.Faker('sentence', nb_words=10)
    
    # Note: top_product will be set after product creation in init_db.py
    # This is because we need products to exist before we can reference them

class DiscountFactory(DjangoModelFactory):
    """
    Factory for creating Discount instances with fake data.
    
    This factory generates realistic discount data including:
    - Random discount percentage (positive float, max 50%)
    - Random description (5-word sentence)
    
    Usage:
        # Create a single discount
        discount = DiscountFactory()
        
        # Create multiple discounts
        discounts = DiscountFactory.create_batch(3)
        
        # Create discount with specific percentage
        discount = DiscountFactory(discount=25.5)
    """
    class Meta:
        model = Discount

    # Generate random discount percentage (positive float, maximum 50%)
    # This represents a discount from 0% to 50% off
    discount = factory.Faker('pyfloat', positive=True, max_value=50)
    
    # Generate random description (5-word sentence)
    description = factory.Faker('sentence', nb_words=5)

class ProductFactory(DjangoModelFactory):
    """
    Factory for creating Product instances with fake data.
    
    This factory generates realistic product data including:
    - Random name, description, price, and inventory
    - Automatically creates a category if none provided
    - Generates URL-friendly slug from the name
    - Handles discount relationships through post-generation
    
    Usage:
        # Create a single product (will create its own category)
        product = ProductFactory()
        
        # Create product with existing category
        product = ProductFactory(category=existing_category)
        
        # Create product with specific discounts
        product = ProductFactory(discount=[discount1, discount2])
        
        # Create multiple products
        products = ProductFactory.create_batch(5)
    """
    class Meta:
        model = Product

    # Generate random product name (single word)
    name = factory.Faker('word')
    
    # Create a new category if none provided, or use existing one
    # SubFactory creates a new instance of CategoryFactory for each product
    category = factory.SubFactory(CategoryFactory)
    
    # Generate URL-friendly slug from the product name
    # slugify converts "Product Name" to "product-name"
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    
    # Generate random description (3-sentence paragraph)
    description = factory.Faker('paragraph', nb_sentences=3)
    
    # Generate random price (3 digits before decimal, 2 after, positive)
    # Example: 123.45, 999.99, etc.
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    
    # Generate random inventory count (0 to 100 items)
    inventory = factory.Faker('random_int', min=0, max=100)
    
    @factory.post_generation
    def discount(self, create, extracted, **kwargs):
        """
        Post-generation method to handle discount relationships.
        
        This method runs after the product is created and handles:
        1. If specific discounts are provided, add them to the product
        2. If no discounts provided, randomly create 0-3 discounts
        
        Args:
            create: Boolean indicating if the object was actually created
            extracted: List of discount objects passed to the factory
            **kwargs: Additional keyword arguments
        """
        if not create:
            return
        
        if extracted:
            # If discounts are passed in, add them to the product
            for discount in extracted:
                self.discount.add(discount)
        else:
            # Add 0-3 random discounts if none provided
            num_discounts = fake.random_int(min=0, max=3)
            if num_discounts > 0:
                # Create new discount instances and add them
                discounts = DiscountFactory.create_batch(num_discounts)
                for discount in discounts:
                    self.discount.add(discount)

class CustomerFactory(DjangoModelFactory):
    """
    Factory for creating Customer instances with fake data.
    
    This factory generates realistic customer data including:
    - Automatically creates a CustomUser for each customer
    - Random phone number
    - Random birth date (18-90 years old)
    
    Usage:
        # Create a single customer (will create its own user)
        customer = CustomerFactory()
        
        # Create customer with existing user
        customer = CustomerFactory(user=existing_user)
        
        # Create multiple customers
        customers = CustomerFactory.create_batch(5)
    """
    class Meta:
        model = Customer

    # Create a new CustomUser for each customer, or use existing one
    # SubFactory creates a new instance of CustomUserFactory for each customer
    user = factory.SubFactory(CustomUserFactory)
    
    # Generate random phone number
    phone_number = factory.Faker('phone_number')
    
    # Generate random birth date (person must be 18-90 years old)
    # This ensures realistic customer data for e-commerce scenarios
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=90)

class AdressFactory(DjangoModelFactory):
    """
    Factory for creating Adress instances with fake data.
    
    This factory generates realistic address data including:
    - Automatically creates a Customer for each address
    - Random province/state, city, and street address
    - Note: Address is linked to customer (one-to-one relationship)
    
    Usage:
        # Create a single address (will create its own customer)
        address = AdressFactory()
        
        # Create address for existing customer
        address = AdressFactory(customer=existing_customer)
        
        # Create multiple addresses
        addresses = AdressFactory.create_batch(5)
    """
    class Meta:
        model = Adress

    # Create a new Customer for each address, or use existing one
    # SubFactory creates a new instance of CustomerFactory for each address
    customer = factory.SubFactory(CustomerFactory)
    
    # Generate random province/state name
    province = factory.Faker('state')
    
    # Generate random city name
    city = factory.Faker('city')
    
    # Generate random street address
    street = factory.Faker('street_address')

class OrderFactory(DjangoModelFactory):
    """
    Factory for creating Order instances with fake data.
    
    This factory generates realistic order data including:
    - Automatically creates a Customer for each order
    - Random order status (paid, unpaid, or canceled)
    
    Order statuses:
    - 'p': Paid
    - 'u': Unpaid (default)
    - 'c': Canceled
    
    Usage:
        # Create a single order (will create its own customer)
        order = OrderFactory()
        
        # Create order for existing customer
        order = OrderFactory(customer=existing_customer)
        
        # Create order with specific status
        order = OrderFactory(status='p')  # Paid order
        
        # Create multiple orders
        orders = OrderFactory.create_batch(5)
    """
    class Meta:
        model = Order

    # Create a new Customer for each order, or use existing one
    # SubFactory creates a new instance of CustomerFactory for each order
    customer = factory.SubFactory(CustomerFactory)
    
    # Generate random order status from predefined choices
    # 'p' = Paid, 'u' = Unpaid, 'c' = Canceled
    status = factory.Faker('random_element', elements=['p', 'u', 'c'])

class OrderItemFactory(DjangoModelFactory):
    """
    Factory for creating OrderItem instances with fake data.
    
    This factory generates realistic order item data including:
    - Automatically creates an Order and Product for each item
    - Random quantity (1-10 items)
    - Price automatically set from the product's price
    
    OrderItem represents individual products within an order.
    Each order can have multiple items, each with its own quantity and price.
    
    Usage:
        # Create a single order item (will create its own order and product)
        order_item = OrderItemFactory()
        
        # Create order item for existing order and product
        order_item = OrderItemFactory(order=existing_order, product=existing_product)
        
        # Create order item with specific quantity
        order_item = OrderItemFactory(quantity=5)
        
        # Create multiple order items
        order_items = OrderItemFactory.create_batch(5)
    """
    class Meta:
        model = OrderItem

    # Create a new Order for each item, or use existing one
    # SubFactory creates a new instance of OrderFactory for each item
    order = factory.SubFactory(OrderFactory)
    
    # Create a new Product for each item, or use existing one
    # SubFactory creates a new instance of ProductFactory for each item
    product = factory.SubFactory(ProductFactory)
    
    # Generate random quantity (1-10 items)
    quantity = factory.Faker('random_int', min=1, max=10)
    
    # Set price automatically from the product's price
    # LazyAttribute ensures this runs when the object is created
    # If no product available, generates a random price as fallback
    price = factory.LazyAttribute(lambda o: o.product.price if o.product else fake.pydecimal(left_digits=3, right_digits=2, positive=True))

class CartFactory(DjangoModelFactory):
    """
    Factory for creating Cart instances with fake data.
    
    This factory creates shopping cart instances. Carts are simple containers
    that hold cart items. Each cart gets a unique UUID automatically.
    
    Usage:
        # Create a single cart
        cart = CartFactory()
        
        # Create multiple carts
        carts = CartFactory.create_batch(5)
        
        # The cart ID will be a unique UUID automatically generated
    """
    class Meta:
        model = Cart

class CartItemFactory(DjangoModelFactory):
    """
    Factory for creating CartItem instances with fake data.
    
    This factory generates realistic cart item data including:
    - Automatically creates a Cart and Product for each item
    - Random quantity (1-5 items)
    
    CartItem represents individual products within a shopping cart.
    Each cart can have multiple items, each with its own quantity.
    
    Usage:
        # Create a single cart item (will create its own cart and product)
        cart_item = CartItemFactory()
        
        # Create cart item for existing cart and product
        cart_item = CartItemFactory(cart=existing_cart, product=existing_product)
        
        # Create cart item with specific quantity
        cart_item = CartItemFactory(quantity=3)
        
        # Create multiple cart items
        cart_items = CartItemFactory.create_batch(5)
    """
    class Meta:
        model = CartItem

    # Create a new Cart for each item, or use existing one
    # SubFactory creates a new instance of CartFactory for each item
    cart = factory.SubFactory(CartFactory)
    
    # Create a new Product for each item, or use existing one
    # SubFactory creates a new instance of ProductFactory for each item
    product = factory.SubFactory(ProductFactory)
    
    # Generate random quantity (1-5 items)
    quantity = factory.Faker('random_int', min=1, max=5)

class CommentFactory(DjangoModelFactory):
    """
    Factory for creating Comment instances with fake data.
    
    This factory generates realistic comment data including:
    - Automatically creates a Product for each comment
    - Random commenter name
    - Random comment body (2-sentence paragraph)
    - Random comment status (waiting, approved, or not approved)
    
    Comment statuses:
    - 'w': Waiting for approval
    - 'a': Approved (default)
    - 'na': Not approved
    
    Usage:
        # Create a single comment (will create its own product)
        comment = CommentFactory()
        
        # Create comment for existing product
        comment = CommentFactory(product=existing_product)
        
        # Create comment with specific status
        comment = CommentFactory(status='w')  # Waiting for approval
        
        # Create multiple comments
        comments = CommentFactory.create_batch(5)
    """
    class Meta:
        model = Comment

    # Create a new Product for each comment, or use existing one
    # SubFactory creates a new instance of ProductFactory for each comment
    product = factory.SubFactory(ProductFactory)
    
    # Generate random commenter name
    name = factory.Faker('name')
    
    # Generate random comment body (2-sentence paragraph)
    body = factory.Faker('paragraph', nb_sentences=2)
    
    # Generate random comment status from predefined choices
    # 'w' = Waiting, 'a' = Approved, 'na' = Not Approved
    status = factory.Faker('random_element', elements=['w', 'a', 'na'])