from django import forms
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from geopy.distance import geodesic

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order
from geocoding.utils import fetch_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects
        .prefetch_related('items')
        .with_total_price()
        .order_by('-created_at')
    )

    for order in orders:
        product_ids = {item.product_id for item in order.items.all()}
        if not product_ids:
            order.available_restaurants_with_distance = []
            continue

        suitable_restaurants = (
            Restaurant.objects
            .filter(
                menu_items__product_id__in=product_ids,
                menu_items__availability=True
            )
            .annotate(
                matched_products=Count('menu_items__product_id', distinct=True)
            )
            .filter(matched_products=len(product_ids))
            .values('id', 'name', 'address')
        )

        customer_coords = fetch_coordinates(order.address)

        restaurants_with_distance = []
        for rest in suitable_restaurants:
            restaurant_coords = fetch_coordinates(rest['address'])

            distance_km = None
            if customer_coords and restaurant_coords:
                try:
                    distance_km = geodesic(
                        customer_coords,
                        restaurant_coords
                    ).km
                except Exception:
                    distance_km = None

            restaurants_with_distance.append({
                'name': rest['name'],
                'distance_km': round(distance_km, 2) if distance_km else None
            })

        restaurants_with_distance.sort(
            key=lambda x: (x['distance_km'] is None, x['distance_km'])
        )

        order.available_restaurants_with_distance = restaurants_with_distance

    unassigned_orders = [o for o in orders if not o.restaurant]
    assigned_orders = [o for o in orders if o.restaurant]

    return render(request, 'order_items.html', {
        'unassigned_orders': unassigned_orders,
        'assigned_orders': assigned_orders
    })
