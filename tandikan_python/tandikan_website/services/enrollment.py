from ..models import Enrollment, EnrollmentSubject, ClassSchedule, AcademicTerm
from .schedule_subject_validation import validate_prerequisites, validate_schedule_conflicts
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

    # 2. Validate Schedule Conflicts (Internal to the selection)
    selected_schedules = []
    for schedule in schedules:
        is_valid, error = validate_schedule_conflicts(schedule, selected_schedules)
        if not is_valid:
            return False, error
        selected_schedules.append(schedule)

    # 3. Create Enrollment
    try:
        with transaction.atomic():
            enrollment = Enrollment.objects.create(
                student=student,
                term=term
            )
            
            for schedule in schedules:
                EnrollmentSubject.objects.create(
                    enrollment=enrollment,
                    schedule=schedule
                )
                
            return True, enrollment
            
    except Exception as e:
        return False, str(e)
