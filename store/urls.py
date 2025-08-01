from django.urls import path, include
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('carts', views.CartViewSet)

products_router = routers.NestedDefaultRouter(parent_router=router, parent_prefix='products', lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comments')
cart_items_router = routers.NestedDefaultRouter(parent_router=router, parent_prefix='carts', lookup='cart')
cart_items_router.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = router.urls + products_router.urls + cart_items_router.urls
