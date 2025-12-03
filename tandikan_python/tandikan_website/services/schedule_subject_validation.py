from ..models import SubjectPrerequisite, Enrollment, EnrollmentSubject

def validate_prerequisites(student, subject):
    """
    Check if the student has passed all prerequisites for the given subject.
    Returns (True, None) if valid, or (False, error_message).
    """
    prerequisites = SubjectPrerequisite.objects.filter(subject=subject)
    
    for prereq in prerequisites:
        # Check if student has passed the prerequisite subject
        # This assumes we look at past enrollments. 
        # For simplicity, we check if they have enrolled in it in a previous term.
        # In a real system, we would check grades.
        has_taken = EnrollmentSubject.objects.filter(
            enrollment__student=student,
            schedule__subject=prereq.prerequisite
        ).exists()
        
        if not has_taken:
            return False, f"Prerequisite {prereq.prerequisite.subject_code} not taken."
            
    return True, None

def validate_schedule_conflicts(new_schedule, current_schedules):
    """
    Check if new_schedule conflicts with any of the current_schedules.
    Returns (True, None) if valid, or (False, error_message).
    """
    for schedule in current_schedules:
        if schedule.day == new_schedule.day:
            # Check time overlap
            # Overlap if (StartA < EndB) and (EndA > StartB)
            if new_schedule.start_time < schedule.end_time and new_schedule.end_time > schedule.start_time:
                return False, f"Conflict with {schedule.subject.subject_code} on {schedule.day} {schedule.start_time}-{schedule.end_time}"
                
    return True, None
