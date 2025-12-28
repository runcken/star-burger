import json
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.templatetags.static import static


from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
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
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


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
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def register_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    required_fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
    for fields in required_fields:
        if fields not in data:
            return JsonResponse({'error': f'Missing field: {field}'}, status=400)

    if not isinstance(data['products'], list) or not data['products']:
        return JsonResponse({'error': 'Products must be a non-empty list'}, status=400)

    products_ids = [item.get('product') for item in data['products']]
    if not all(isinstance(pid, int) for pid in products_ids):
        return JsonResponse({'error': 'Product IDs must be integers'}, status=400)

    products = {p.id: p for p in Product.objects.filter(id__in=products_ids)}
    if len(products) != len(products_ids):
        return JsonResponse({'error': 'One or more products not found'}, status=400)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                first_name=data['firstname'],
                last_name=data['lastname'],
                phone_number=data['phonenumber'],
                address=data['address']
            )

            order_items = []
            for item in data['products']:
                product_id = item['product']
                quantity = item.get('quantity', 1)
                if not isinstance(quantity, int) or quantity < 1:
                    return JsonResponse({'error': f'Invalid quantity for product {product_id}'}, status=400)

                order_items.append(
                    OrderItem(
                        order=order,
                        product=products[product_id],
                        quantity=quantity
                    )
                )

            OrderItem.objects.bulk_create(order_items)

    except Exception as e:
        return JsonResponse({'error': 'Failed to create order'}, status=500)

    return JsonResponse({
        'id': order.id,
        'firstname': order.first_name,
        'lastname': order.last_name,
        'address': order.address,
        'products': [
            {'product': item.product_id, 'quantity': item.quantity}
            for item in order.items.all()
        ]
    }, status=201)
