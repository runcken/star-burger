# import json
# from django.core.exceptions import ValidationError
from django.db import transaction
# from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
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

    required_fields = [
        'firstname',
        'lastname',
        'phonenumber',
        'address',
        'products'
    ]
    errors = {}

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        for field in missing_fields:
            errors[field] = 'Отсутствует обязательное поле'
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    text_fields = ['firstname', 'lastname', 'address']
    for field in text_fields:
        value = data[field]
        if value is None:
            errors[field] = 'Это поле не может быть пустым'
        elif not isinstance(value, str):
            errors[field] = 'Некорректное значение'
        elif value.strip() == '':
            errors[field] = 'Это поле не может быть пустым'

    phone_value = data['phonenumber']
    if phone_value is None:
        errors['phonenumber'] = 'Это поле не может быть пустым'
    elif not isinstance(phone_value, str):
        errors['phonenumber'] = 'Некорректное значение'
    elif phone_value.strip() == '':
        errors['phonenumber'] = 'Это поле не может быть пустым'
    else:
        try:
            phone_obj = PhoneNumber.from_string(phone_value)
            if not phone_obj.is_valid():
                errors['phonenumber'] = 'Введен некорректный номер телефона'
        except Exception:
            errors['phonenumber'] = 'Введен некорректный номер телефона'

    products_data = data['products']

    if products_data is None:
        errors['products'] = 'Это поле не может быть пустым'
    elif not isinstance(products_data, list):
        errors['products'] = 'Ожидался list со значениями, но был получен str'
    elif len(products_data) == 0:
        errors['products'] = 'Это список не может быть пустым'
    else:
        product_ids = []
        product_errors = []

        for i, item in enumerate(products_data):
            if not isinstance(item, dict):
                product_errors.append(f'Элемент #{i} должен быть объектом (dict), но получен {type(item).__name__}')
                continue
            if 'product' not in item:
                product_errors.append(f'Элемент #{i}: отсутствует обязательное поле "product"')
                continue

            pid = item['product']
            if not isinstance(pid, int):
                product_errors.append(f'Элемент #{i}: "product" должен быть целым числом, получено: {repr(pid)}')

            qty = item.get('quantity', 1)
            if not isinstance(qty, int) or qty < 1:
                product_errors.append(f'Элемент #{i}: "quantity" должно быть целым числом >= 1, получено: {repr(qty)}')

            product_ids.append(pid)

        if product_errors:
            errors['products'] = ' '.join(product_errors)
        else:
            existing_products = Product.objects.filter(id__in=product_ids)
            found_ids = set(p.id for p in existing_products)
            missing_ids = set(product_ids) - found_ids
            if missing_ids:
                first_missing = sorted(missing_ids)[0]
                errors['products'] = f'Недопустимый первичный ключ "{first_missing}"'

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                first_name=data['firstname'],
                last_name=data['lastname'],
                phone_number=data['phonenumber'],
                address=data['address']
            )

            existing_products_dict = {
                p.id: p for p in Product.objects.filter(
                    id__in=[item['product'] for item in products_data]
                )
            }
            order_items = [
                OrderItem(
                    order=order,
                    product=existing_products_dict[item['product']],
                    quantity=item.get('quantity', 1)
                )
                for item in products_data
            ]

            OrderItem.objects.bulk_create(order_items)

    except Exception:
        return Response(
            {'error': 'Failed to create order'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
