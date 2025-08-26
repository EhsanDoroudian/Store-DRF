from django.contrib import admin
from .models import Cart, CartItem, Product, Order, Customer, Comment, OrderItem
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages


class InventoryFilter(admin.SimpleListFilter):
    title = 'Critical Inventory Status'
    parameter_name = 'inventory'

    HIGH_CRITICAL_SATATUS = '<3'
    MEDIUM_CRITICAL_STATUS = '3<=10'
    LOW_CRITICAL_STATUS = '>10'

    def lookups(self, request, model_admin):
        return [
            (self.HIGH_CRITICAL_SATATUS, 'High'),
            (self.MEDIUM_CRITICAL_STATUS, 'Medium'),
            (self.LOW_CRITICAL_STATUS, 'Ok')
        ]

    def queryset(self, request, queryset):
        if self.value() == self.HIGH_CRITICAL_SATATUS:
            return queryset.filter(inventory__lt=3)
        
        if self.value() == self.MEDIUM_CRITICAL_STATUS:
            return queryset.filter(inventory__range=(3, 10))
        
        if self.value() == self.LOW_CRITICAL_STATUS:
            return queryset.filter(inventory__gt=10)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'inventory', 'price', 'inventory_status', 'product_category', 'num_of_comments']
    list_per_page = 20
    list_editable = ['price']
    list_select_related = ['category',]
    list_filter = ['datetime_created', InventoryFilter]
    actions = ['clear_inventory']
    search_fields = ['name', ]
    exclude = ['discount', ]
    readonly_fields = ['category', ]
    prepopulated_fields = {
        'slug': ['name', ],
    }

    @admin.action(description='Clear Inventory')
    def clear_inventory(self, request, queryset):
        update_count = queryset.update(inventory=0)
        self.message_user(
            request=request,
            message=f'{update_count} of products inventories cleared to Zero',
            level=messages.WARNING,  
        )
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('comments').annotate(comments_count=Count('comments'))
    
    def num_of_comments(self, product):
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                'product__id':product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.comments_count)

    @admin.display(ordering='category__title', description='category title')
    def product_category(self, prodcut):
        return prodcut.category.title
    
    def inventory_status(self, product:Product):
        if product.inventory < 10:
            return 'Low'
        if product.inventory > 50:
            return 'High'
        
        return 'Medium'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'price']
    extra = 3

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'datetime_created', 'num_of_items']
    list_editable = ['status']
    list_per_page = 10
    ordering = ["-datetime_created"]
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items').annotate(items_count=Count('items'))
    def num_of_items(self, order):
        return order.items_count
    

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    autocomplete_fields = ['product', ]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email']
    list_per_page = 10
    ordering = ['user__last_name', 'user__first_name']
    search_fields = ['user__first_name__istartswith', 'user__last_name__istartswith']
    
    def first_name(self, customer):
        return customer.user.first_name
    
    def last_name(self, customer):
        return customer.user.last_name
    
    def email(self, customer):
        return customer.user.email

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'body', 'status']
    autocomplete_fields = ['product',]


class CartItemInline(admin.TabularInline):
    model = CartItem
    fields = ['id', 'product', 'quantity']
    extra = 0
    min_num = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline]
