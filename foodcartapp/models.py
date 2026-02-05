from collections import defaultdict
from django.db import models
from django.db.models import Sum, F, DecimalField
from django.core.validators import MinValueValidator
from geopy.distance import geodesic
from phonenumber_field.modelfields import PhoneNumberField

from geocoding.utils import get_or_create_locations


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f'{self.restaurant.name} - {self.product.name}'


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(
                F('items__product__price') * F('items__quantity'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

    def with_restaurants_and_distances(self):
        from .models import RestaurantMenuItem

        menu_items = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .select_related('restaurant')
        )

        restaurant_products = defaultdict(set)
        restaurant_info = {}

        for item in menu_items:
            restaurant_products[item.restaurant_id].add(item.product_id)
            restaurant_info[item.restaurant_id] = {
                'name': item.restaurant.name,
                'address': item.restaurant.address
            }

        all_addresses = set()
        order_product_map = {}

        for order in self:
            product_ids = {item.product_id for item in order.items.all()}
            order_product_map[order.id] = product_ids
            if order.address.strip():
                all_addresses.add(order.address.strip())

        for info in restaurant_info.values():
            if info['address'].strip():
                all_addresses.add(info['address'].strip())

        coordinates = get_or_create_locations(list(all_addresses))

        restaurants_by_order_id = {}

        for order in self:
            product_ids = order_product_map[order.id]
            if not product_ids:
                restaurants_by_order_id[order.id] = []
                continue

            customer_address = order.address.strip() if order.address else ''
            customer_coords = coordinates.get(customer_address)

            if customer_coords == 'NOT_FOUND':
                restaurants_by_order_id[order.id] = 'ADDRESS_NOT_FOUND'
                continue

            restaurants_list = []

            for restaurant_id, products in restaurant_products.items():
                if not product_ids.issubset(products):
                    continue

                rest_info = restaurant_info[restaurant_id]
                restaurant_addr = (
                    rest_info['address'].strip()
                    if rest_info['address']
                    else ""
                )
                restaurant_coords = coordinates.get(restaurant_addr)

                if restaurant_coords == 'NOT_FOUND':
                    distance_km = None
                elif customer_coords and restaurant_coords:
                    try:
                        distance_km = geodesic(
                            customer_coords,
                            restaurant_coords
                        ).km
                    except Exception:
                        distance_km = None
                else:
                    distance_km = None

                restaurants_list.append({
                    'name': rest_info['name'],
                    'distance_km': (
                        round(distance_km, 2)
                        if distance_km
                        else None
                    )
                })

            restaurants_list.sort(
                key=lambda x: (
                    x['distance_km'] is None,
                    x['distance_km']
                )
            )
            restaurants_by_order_id[order.id] = restaurants_list

        for order in self:
            order.restaurants_with_distances = restaurants_by_order_id.get(
                order.id,
                []
            )

        return self


class Order(models.Model):
    class Status(models.TextChoices):
        UNPROCESSED = 'unprocessed', 'Необработанный'
        RESTAURANT_CONFIRMED = 'restaurant_confirmed', 'Готовится'
        DELIVERY_STARTED = 'delivery_started', 'Передан курьеру'
        COMPLETED = 'completed', 'Заказ выполнен'

    class Payment(models.TextChoices):
        CASH = 'cash', 'Наличными'
        CARD = 'card', 'Картой'

    first_name = models.CharField(
        'имя',
        max_length=100
    )
    last_name = models.CharField(
        'фамилия',
        max_length=100
    )
    phone_number = PhoneNumberField('телефон', db_index=True)
    address = models.CharField(
        'адрес',
        max_length=200,
    )
    comment = models.TextField(
        'комментарий',
        blank=True,
        null=False,
        help_text='Комментарий клиента к заказу')
    created_at = models.DateTimeField(
        'создан',
        auto_now_add=True,
        db_index=True
    )
    called_at = models.DateTimeField(
        'звонок',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'доставлен',
        blank=True,
        null=True,
        db_index=True
    )
    status = models.CharField(
        'статус',
        max_length=50,
        choices=Status.choices,
        default=Status.UNPROCESSED,
        db_index=True
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='ресторан',
        related_name='orders'
    )
    payment = models.CharField(
        'оплата',
        max_length=50,
        choices=Payment.choices,
        blank=True,
        db_index=True
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'Заказ {self.id} - {self.first_name} {self.last_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name='заказ',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        verbose_name='товар',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена на момент заказа',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f'{self.product} * {self.quantity} по {self.price} руб'
