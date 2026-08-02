import requests
from django.conf import settings

from .models import Location


def get_or_create_locations(addresses):
    if not addresses:
        return {}

    unique_addresses = list(
        set(addr.strip() for addr in addresses if addr.strip())
    )
    if not unique_addresses:
        return {addr: None for addr in addresses}

    existing_locations = Location.objects.filter(address__in=unique_addresses)
    location_cache = {}

    for loc in existing_locations:
        if loc.lat is None and loc.lon is None:
            location_cache[loc.address] = 'NOT_FOUND'
        else:
            location_cache[loc.address] = (loc.lat, loc.lon)

    missing_addresses = [
        addr for addr in unique_addresses
        if addr not in location_cache
    ]

    if missing_addresses:
        new_locations = []
        for address in missing_addresses:
            coords = fetch_coordinates_from_yandex(address)
            if coords is None:
                location_cache[address] = 'NOT_FOUND'
                new_locations.append(
                    Location(address=address, lat=None, lon=None)
                )
            else:
                location_cache[address] = coords
                new_locations.append(
                    Location(
                        address=address,
                        lat=coords[0] if coords else None,
                        lon=coords[1] if coords else None
                    )
                )

        if new_locations:
            Location.objects.bulk_create(new_locations, ignore_conflicts=True)

    return {
        addr: location_cache.get(
            addr.strip(),
            'NOT_FOUND'
        ) for addr in addresses
    }


def fetch_coordinates_from_yandex(address):
    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(
            base_url,
            params={
                "geocode": address,
                "apikey": settings.YANDEX_API_KEY,
                "format": "json",
            },
            timeout=10
        )
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
        lat, lon = float(lat), float(lon)

        return (lat, lon)

    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None
