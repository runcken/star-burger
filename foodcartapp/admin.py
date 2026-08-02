from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html

from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from .models import OrderItem
from geocoding.models import Location


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'address',
        'phone_number',
        'first_name',
        'last_name',
        'created_at'
    ]
    fieldsets = (
        ('ОСНОВНАЯ ИНФОРМАЦИЯ', {
            'fields': (
                'first_name',
                'last_name',
                'phone_number',
                'address',
                'payment',
                'comment'
            )
        }),
        ('СТАТУС И РЕСТОРАН', {
            'fields': ('status', 'restaurant')
        }),
        ('РАСПИСАНИЕ', {
            'fields': ('created_at', 'called_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    actions = [
        'mark_restaurant_confirmed',
        'mark_delivery_started',
        'mark_completed'
    ]

    def mark_restaurant_confirmed(self, request, queryset):
        queryset.update(status=Order.Status.RESTAURANT_CONFIRMED)
    mark_restaurant_confirmed.short_description = 'Отметить: Ресторан подтвердил'

    def mark_delivery_started(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERY_STARTED)
    mark_delivery_started.short_description = 'Отметить: Передан курьеру'

    def mark_completed(self, request, queryset):
        queryset.update(status=Order.Status.COMPLETED)
    mark_completed.short_description = 'Отметить: Заказ выполнен'

    list_display_links = [
        'address',
    ]
    inlines = [
        OrderItemInline
    ]

    def response_post_save_change(self, request, obj):
        if request.GET.get('_from_order_items') == '1':
            return HttpResponseRedirect(reverse('restaurateur:view_orders'))
        return super().response_post_save_change(request, obj)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        'address',
        'lat',
        'lon',
        'created_at',
        'updated_at',
    ]

