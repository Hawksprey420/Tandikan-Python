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

def validate_class_creation(instructor, room, day, start_time, end_time, exclude_schedule_id=None):
    """
    Check for conflicts when creating/editing a class schedule.
    Checks for:
    1. Instructor double booking
    2. Room double booking
    
    Returns (True, None) if valid, or (False, error_message).
    """
    from ..models import ClassSchedule
    from django.db.models import Q
    
    # 1. Check Instructor Conflict
    instructor_conflicts = ClassSchedule.objects.filter(
        instructor=instructor,
        day=day,
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    
    if exclude_schedule_id:
        instructor_conflicts = instructor_conflicts.exclude(schedule_id=exclude_schedule_id)
        
    if instructor_conflicts.exists():
        conflict = instructor_conflicts.first()
        return False, f"Instructor {instructor} is already booked on {day} {conflict.start_time}-{conflict.end_time} ({conflict.subject.subject_code})."

    # 2. Check Room Conflict
    room_conflicts = ClassSchedule.objects.filter(
        room=room,
        day=day,
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    
    if exclude_schedule_id:
        room_conflicts = room_conflicts.exclude(schedule_id=exclude_schedule_id)
        
    if room_conflicts.exists():
        conflict = room_conflicts.first()
        return False, f"Room {room} is already booked on {day} {conflict.start_time}-{conflict.end_time} ({conflict.subject.subject_code})."
        
    return True, None
