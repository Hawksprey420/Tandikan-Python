from ..models import Assessment, EnrollmentSubject, Fee
from decimal import Decimal

def generate_assessment(enrollment):
    """
    Generate assessment for a given enrollment.
    """
    # Calculate total units
    enrollment_subjects = EnrollmentSubject.objects.filter(enrollment=enrollment)
    total_units = sum(es.schedule.subject.units for es in enrollment_subjects)
    
    # Calculate Tuition Fee
    # Assuming there is a Fee record for "Tuition per Unit"
    try:
        tuition_rate = Fee.objects.get(name="Tuition per Unit").amount
    except Fee.DoesNotExist:
        tuition_rate = Decimal('500.00') # Default fallback
        
    tuition_fee = total_units * tuition_rate
    
    # Calculate Other Fees
    # Sum of all other fees
    other_fees_qs = Fee.objects.exclude(name="Tuition per Unit")
    other_fees = sum(f.amount for f in other_fees_qs)
    
    total_amount = tuition_fee + other_fees
    
    # Create or Update Assessment
    assessment, created = Assessment.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            'total_units': total_units,
            'tuition_fee': tuition_fee,
            'other_fees': other_fees,
            'total_amount': total_amount
        }
    )
    
    return assessment
