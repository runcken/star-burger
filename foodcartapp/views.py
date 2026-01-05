import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderItem


@api_view(['GET'])
def banners_list_api(request):
    banners = [
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ]
    return Response(banners)


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


@api_view(['POST'])
def register_order(request):
    data = request.data

    required_fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
    for field in required_fields:
        if field not in data:
            if field == 'products':
                return Response({'error': 'products: Обязательное поле.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': f'Missing field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

    products_data = data['products']

    if products_data is None:
        return Response({'error': 'products: Это поле не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(products_data, list):
        return Response({'error': 'products: Ожидался list со значениями, но был получен str'}, status=status.HTTP_400_BAD_REQUEST)

    if len(products_data) == 0:
        return Response({'error': 'products: Этот список не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)

    products_ids = [item.get('product') for item in products_data]
    if not all(isinstance(pid, int) for pid in products_ids):
        return Response({'error': 'Product IDs must be integers'}, status=status.HTTP_400_BAD_REQUEST)

    products = {p.id: p for p in Product.objects.filter(id__in=products_ids)}
    if len(products) != len(products_ids):
        return Response({'error': 'One or more products not found'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                first_name=data['firstname'],
                last_name=data['lastname'],
                phone_number=data['phonenumber'],
                address=data['address']
            )

            order_items = []
            for item in products_data:
                product_id = item['product']
                quantity = item.get('quantity', 1)
                if not isinstance(quantity, int) or quantity < 1:
                    return Response({'error': f'Invalid quantity for product {product_id}'}, status=status.HTTP_400_BAD_REQUEST)

                order_items.append(
                    OrderItem(
                        order=order,
                        product=products[product_id],
                        quantity=quantity
                    )
                )

            OrderItem.objects.bulk_create(order_items)

    except Exception as e:
        return Response({'error': 'Failed to create order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    response_data = {
        'id': order.id,
        'firstname': order.first_name,
        'lastname': order.last_name,
        'phonenumber': str(order.phone_number),
        'address': order.address,
        'products': [
            {'product': item.product_id, 'quantity': item.quantity}
            for item in order.items.all()
        ]
    }
    # print(response_data)
    return Response(response_data, status=status.HTTP_201_CREATED)
