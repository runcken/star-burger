import requests
from django import forms
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from geopy.distance import geodesic

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.conf import settings

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


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

    address_cache = {}
    
    for order in orders:
        product_ids = {item.product_id for item in order.items.all()}
        if not product_ids:
            order.available_restaurants_with_distance = []
            continue

        restaurants = (
            RestaurantMenuItem.objects
            .filter(product_id__in=product_ids, availability=True)
            .values('restaurant_id')
            .annotate(matched_products=Count('product_id', distinct=True))
            .filter(matched_products=len(product_ids))
            .values('restaurant_id', 'restaurant__name', 'restaurant__address')
        )

        customer_address = order.address
        if customer_address in address_cache:
            customer_coords = address_cache[customer_address]
        else:
            try:
                customer_coords = fetch_coordinates(
                    settings.YANDEX_API_KEY,
                    customer_address
                )
                address_cache[customer_address] = customer_coords
            except (requests.RequestException, KeyError, ValueError):
                customer_coords = None

        restaurants_with_distance = []

        for rest in restaurants:
            restaurant_address = rest['restaurant__address']
            
            if restaurant_address in address_cache:
                restaurant_coords = address_cache[restaurant_address]
            else:
                try:
                    restaurant_coords = fetch_coordinates(
                        settings.YANDEX_API_KEY,
                        restaurant_address
                    )
                    address_cache[restaurant_address] = restaurant_coords
                except (requests.RequestException, KeyError, ValueError):
                    restaurant_coords = None
            distance_km = None
            if customer_coords and restaurant_coords:
                try:
                    distance_km = geodesic(
                        customer_coords[::-1],
                        restaurant_coords[::-1]
                    ).km
                except Exception:
                    distance_km = None

            restaurants_with_distance.append({
                'name': rest['restaurant__name'],
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


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = (
        response.json()
        ['response']
        ['GeoObjectCollection']
        ['featureMember']
    )

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat
