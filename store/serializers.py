from rest_framework import serializers
from .models import Cart, CartItem, Category, Product, Comment
from decimal import Decimal
from django.utils.text import slugify



class CategorySerializer(serializers.ModelSerializer):
    product_number = serializers.IntegerField(source='products.count', read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'title', 'description', 'product_number', 'top_product']

    def validate(self, data):
        if len(data['title']) < 3:
            raise serializers.ValidationError("Category title length must at least 3 character.")
        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'inventory', 'category', 'slug', 'description', 'unit_price_after_tax']
        
    title = serializers.CharField(max_length=255, source='name')
    category = serializers.StringRelatedField()
    unit_price_after_tax = serializers.SerializerMethodField(method_name='calculate_tax')

    def calculate_tax(self, product:Product):
        return round(product.price * Decimal(1.09), 1)
    
    def validate(self, data):
        if len(data['name']) < 6:
            raise serializers.ValidationError("Error occured")
        return data

    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()
        return product


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'name', 'body']
    
    def create(self, validated_data):
        product_id = self.context['product_pk']
        return Comment.objects.create(product_id=product_id, **validated_data)


class CartProductSeriallizer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity',]


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']
    
    def create(self, validated_data):
        cart_id = self.context['cart_pk']
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id)
        
        self.instance = cart_item
        return cart_item
        
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'item_total']

    product = CartProductSeriallizer()
    item_total = serializers.SerializerMethodField()

    def get_item_total(self, cart_item):
        return cart_item.quantity * cart_item.product.price


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']
        read_only_fields = ['id',]
    
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum([item.quantity * item.product.price for item in cart.items.all()])
