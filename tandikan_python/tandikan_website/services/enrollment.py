from ..models import Enrollment, EnrollmentSubject, ClassSchedule, AcademicTerm
from .schedule_subject_validation import validate_prerequisites, validate_schedule_conflicts
from .assessment import generate_assessment
from django.db import transaction

def enroll_student(student, term_id, schedule_ids):
    """
    Enroll a student in a list of class schedules.
    """
    term = AcademicTerm.objects.get(pk=term_id)
    schedules = ClassSchedule.objects.filter(pk__in=schedule_ids)
    
    # 1. Validate Prerequisites
    for schedule in schedules:
        is_valid, error = validate_prerequisites(student, schedule.subject)
        if not is_valid:
            return False, error

    # 2. Validate Schedule Conflicts (Internal to the selection + Existing Enrollments)
    selected_schedules = []
    
    # Check for existing enrollment to validate against already enrolled subjects
    existing_enrollment = Enrollment.objects.filter(student=student, term=term).first()
    existing_schedules = []
    if existing_enrollment:
        existing_schedules = list(ClassSchedule.objects.filter(enrollmentsubject__enrollment=existing_enrollment))

    for schedule in schedules:
        # Check against other NEWLY selected schedules
        is_valid, error = validate_schedule_conflicts(schedule, selected_schedules)
        if not is_valid:
            return False, error
            
        # Check against EXISTING schedules
        is_valid, error = validate_schedule_conflicts(schedule, existing_schedules)
        if not is_valid:
            return False, f"Conflict with existing enrollment: {error}"

        selected_schedules.append(schedule)

    # 3. Create Enrollment
    try:
        with transaction.atomic():
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                term=term
            )
            
            for schedule in schedules:
                EnrollmentSubject.objects.get_or_create(
                    enrollment=enrollment,
                    schedule=schedule
                )
            
            # Generate assessment immediately after enrollment
            generate_assessment(enrollment)
                
            return True, enrollment
            
    except Exception as e:
        return False, str(e)
