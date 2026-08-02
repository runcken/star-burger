from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product
from .serializers import OrderCreateSerializer


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
    serializer = OrderCreateSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        response_order = {
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
        return Response(response_order, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
