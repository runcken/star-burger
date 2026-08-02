from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def update_order_status(sender, instance, **kwargs):
    if (
        instance.restaurant is not None and
        instance.status ==Order.Status.UNPROCESSED
    ):
        Order.objects.filter(pk=instance.pk).update(
            status=Order.Status.RESTAURANT_CONFIRMED
        )
