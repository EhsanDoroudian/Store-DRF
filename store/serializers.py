from rest_framework import serializers
from .models import Category, Product, Comment
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


    