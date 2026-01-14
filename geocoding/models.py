from django.db import models


class Location(models.Model):
    address = models.CharField('адрес', max_length=200, unique=True)
    lat = models.FloatField('широта', null=True, blank=True)
    lon = models.FloatField('долгота', null=True, blank=True)
    created_at = models.DateTimeField('запрос создан', auto_now_add=True)
    updated_at = models.DateTimeField('последнее обновление', auto_now=True)

    class Meta:
        verbose_name = 'локация'
        verbose_name_plural = 'локации'

    def __str__(self):
        return f'{self.address} ({self.lat} {self.lon})'

    @property
    def coordinates(self):
        if self.lat is not None and self.lon is not None:
            return (self.lat, self.lon)
        return None
