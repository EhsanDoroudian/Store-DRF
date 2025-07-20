from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend

from store.filters import ProductFilter
from .serializers import CategorySerializer, CommentSerializer, ProductSerializer
from .models import Category, Product, Comment
from .paginations import DefaultPagination


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related('category').all()
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['name']
    filterset_class = ProductFilter
    OrderingFilter = ['name', 'price', 'inventory',]
    pagination_class = DefaultPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, pk):
        product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
        if product.order_items.count() > 0:
            return Response({'error': "You can not delte this product. it is order item of a order.",},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CategoryViewSet(ModelViewSet):
        queryset = Category.objects.prefetch_related('products').select_related('top_product').all()
        serializer_class = CategorySerializer

        def destroy(self, request, pk):
            category = get_object_or_404(Category.objects.prefetch_related('products'), pk=pk)
            if category.products.count() > 0:
                return Response({'error': "You can not delete this category. it is category of a product.",},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED)
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        product_pk = self.kwargs['product_pk']
        return Comment.objects.filter(product_id=product_pk).all()

    def get_serializer_context(self):
        return {"product_pk": self.kwargs['product_pk']}