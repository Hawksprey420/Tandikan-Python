from ..models import Payment, Assessment
from django.utils import timezone

def record_payment(assessment_id, amount, cashier_user):
    """
    Record a payment for an assessment.
    """
    try:
        assessment = Assessment.objects.get(pk=assessment_id)
        
        payment = Payment.objects.create(
            assessment=assessment,
            amount_paid=amount,
            cashier=cashier_user,
            date_paid=timezone.now()
        )
        
        return True, payment
    except Assessment.DoesNotExist:
        return False, "Assessment not found."
    except Exception as e:
        return False, str(e)
