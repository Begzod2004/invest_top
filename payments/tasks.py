from celery import shared_task
from .models import Payment

@shared_task
def check_payments():
    pending_payments = Payment.objects.filter(status="pending_approval")
    for payment in pending_payments:
        if payment.amount > 0:
            payment.status = "admin_approved"
            payment.save()
    return f"{len(pending_payments)} payments checked."
