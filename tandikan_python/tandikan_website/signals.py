from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import (
    SystemLog, User, StudentInfo, Faculty, Subject, 
    ClassSchedule, Enrollment, Assessment, Payment, Room, AcademicTerm
)

# List of models to track
TRACKED_MODELS = [
    User, StudentInfo, Faculty, Subject, 
    ClassSchedule, Enrollment, Assessment, Payment, Room, AcademicTerm
]

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    SystemLog.objects.create(
        user=user,
        action='LOGIN',
        details=f"User {user.username} logged in.",
        ip_address=get_client_ip(request)
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        SystemLog.objects.create(
            user=user,
            action='LOGOUT',
            details=f"User {user.username} logged out.",
            ip_address=get_client_ip(request)
        )

@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if sender in TRACKED_MODELS:
        # Avoid logging SystemLog itself to prevent infinite loops
        if sender == SystemLog:
            return

        action = 'CREATE' if created else 'UPDATE'
        
        # Try to get the user who made the change. 
        # This is tricky in signals because we don't have the request object.
        # We'll leave user null for now, or use a middleware approach if strict user tracking is needed for every DB change.
        # However, for many admin actions, we can infer or it's acceptable to just see the data change.
        # To strictly bind user to DB change, we'd need thread-local storage or passing user to save().
        
        # For now, we'll log the change.
        
        try:
            # Simple serialization of the instance
            details = f"{instance}"
        except:
            details = "Object modified"

        SystemLog.objects.create(
            action=action,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            details=details
        )

@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if sender in TRACKED_MODELS:
        if sender == SystemLog:
            return

        SystemLog.objects.create(
            action='DELETE',
            model_name=sender.__name__,
            object_id=str(instance.pk),
            details=f"Deleted: {instance}"
        )
