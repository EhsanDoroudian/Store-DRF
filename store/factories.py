import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils.text import slugify
from .models import *

fake = Faker()

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Faker('word')
    description = factory.Faker('sentence', nb_words=10)
    # top_product will be set after product creation

class DiscountFactory(DjangoModelFactory):
    class Meta:
        model = Discount

    discount = factory.Faker('pyfloat', positive=True, max_value=50)
    description = factory.Faker('sentence', nb_words=5)

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.Faker('paragraph', nb_sentences=3)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    inventory = factory.Faker('random_int', min=0, max=100)
    
    @factory.post_generation
    def discount(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for discount in extracted:
                self.discount.add(discount)
        else:
            # Add 0-3 random discounts
            num_discounts = fake.random_int(min=0, max=3)
            discounts = DiscountFactory.create_batch(num_discounts)
            for discount in discounts:
                self.discount.add(discount)

class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    phone_number = factory.Faker('phone_number')
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=90)

class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Adress  # Note: Typo in model name (Address vs Adress)

    customer = factory.SubFactory(CustomerFactory)
    province = factory.Faker('state')
    city = factory.Faker('city')
    street = factory.Faker('street_address')

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    status = factory.Faker('random_element', elements=['p', 'u', 'c'])

class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=10)
    price = factory.LazyAttribute(lambda o: o.product.price)

class CartFactory(DjangoModelFactory):
    class Meta:
        model = Cart

class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)

class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    product = factory.SubFactory(ProductFactory)
    name = factory.Faker('name')
    body = factory.Faker('paragraph', nb_sentences=2)
    status = factory.Faker('random_element', elements=['w', 'a', 'na'])