from decimal import Decimal
from ..models import Fee

def initialize_fees():
    """
    Initialize default fees if they don't exist.
    """
    default_fees = [
        ("Tuition per Unit", Decimal('500.00')),
        ("Miscellaneous Fee", Decimal('2000.00')),
        ("Library Fee", Decimal('500.00')),
        ("Laboratory Fee", Decimal('1000.00')),
        ("Registration Fee", Decimal('300.00')),
    ]
    
    for name, amount in default_fees:
        Fee.objects.get_or_create(name=name, defaults={'amount': amount})
