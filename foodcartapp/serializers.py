from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from django.db import transaction

from .models import Product, Order, OrderItem


class OrderProductSerializer(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Недопустимый первичный ключ "{value}"'
            )
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True)
    phonenumber = PhoneNumberField(write_only=True)

    firstname = serializers.CharField(write_only=True, required=True)
    lastname = serializers.CharField(write_only=True, required=True)
    address = serializers.CharField(required=True)

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'address',
            'products',
            'phonenumber'
        ]

    def validate_firstname(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value.strip()

    def validate_lastname(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value.strip()

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value.strip()

    def validate_phonenumber(self, value):
        if not value or str(value).strip() == "":
            raise serializers.ValidationError('Это поле не может быть пустым')
        if not value.is_valid():
            raise serializers.ValidationError(
                'Введен некорректный номер телефона'
            )
        return value

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError(
                'Этот список не может быть пустым'
            )
        return value

    def create(self, validated_data):
        with transaction.atomic():
            validated_data['first_name'] = validated_data.pop('firstname')
            validated_data['last_name'] = validated_data.pop('lastname')
            validated_data['phone_number'] = validated_data.pop('phonenumber')
            validated_data['status'] = Order.Status.UNPROCESSED
            products_data = validated_data.pop('products')
            order = Order.objects.create(**validated_data)

            order_items = []
            for item in products_data:
                product = Product.objects.get(id=item['product'])
                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=product.price
                    )
                )

            OrderItem.objects.bulk_create(order_items)
            return order
