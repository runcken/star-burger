import requests
from django.conf import settings
from .models import Location


def fetch_coordinates(address):
    try:
        location = Location.objects.get(address=address)
        return location.coordinates
    except Location.DoesNotExist:
        pass

    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_API_KEY,
            "format": "json",
        }, timeout=10)
        response.raise_for_status()
        found_places = (
            response.json()
            ['response']
            ['GeoObjectCollection']
            ['featureMember']
        )
        if not found_places:
            Location.objects.update_or_create(
                address=address,
                defaults={'lat': None, 'lon': None}
            )
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
        lat, lon = float(lat), float(lon)

        Location.objects.update_or_create(
            address=address,
            defaults={'lat': lat, 'lon': lon}
        )
        return (lat, lon)

    except (requests.RequestException, KeyError, TypeError):
        Location.objects.update_or_create(
            address=address,
            defaults={'lat': None, 'lon': None}
        )
        return None
