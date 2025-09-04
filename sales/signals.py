from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from threading import Thread

from .models import Order

def _send_async(subject, message, recipient_list):
    def _worker():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                recipient_list=recipient_list,
                fail_silently=True,  # avoid breaking request flow
            )
        except Exception:
            # optional: log here
            pass
    Thread(target=_worker, daemon=True).start()

def _vendor_email(order: Order) -> str | None:
    # Adjust if your Vendor model uses a different field name
    return getattr(order.vendor, "email", None)

@receiver(post_save, sender=Order)
def email_on_order_create_update(sender, instance: Order, created, **kwargs):
    email = _vendor_email(instance)
    if not email:
        return
    if created:
        subject = f"New Order {instance.order_id}"
        message = (
            f"Hello {getattr(instance.vendor, 'name', 'Vendor')},\n\n"
            f"A new order has been created for {getattr(instance.product, 'name', '')}.\n"
            f"Order ID : {instance.order_id}\n"
            f"Quantity  : {instance.quantity}\n"
            f"Value     : ₹{instance.order_value}\n"
            f"Date      : {instance.order_date}\n"
            f"Status    : {instance.status}\n\n"
            "Thank you."
        )
    else:
        # If you only want on create, just `return` here.
        subject = f"Order Updated {instance.order_id}"
        message = (
            f"Hello {getattr(instance.vendor, 'name', 'Vendor')},\n\n"
            f"Your order {instance.order_id} was updated.\n"
            f"Status: {instance.status}\n"
        )
    _send_async(subject, message, [email])

@receiver(post_delete, sender=Order)
def email_on_order_delete(sender, instance: Order, **kwargs):
    email = _vendor_email(instance)
    if not email:
        return
    subject = f"Order Deleted {instance.order_id}"
    message = (
        f"Hello {getattr(instance.vendor, 'name', 'Vendor')},\n\n"
        f"Order {instance.order_id} has been deleted.\n"
        "If this wasn't expected, please contact support.\n"
    )
    _send_async(subject, message, [email])
