from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMixin(AccessMixin):
    """
    Mixin to allow access only to users with specific roles.
    Usage:
    class MyView(RoleRequiredMixin, View):
        allowed_roles = ['admin', 'registrar']
        ...
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.role not in self.allowed_roles:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('login')
            
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']

class RegistrarRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['registrar']

class CashierRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['cashier']

class FacultyRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['instructor']

class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['student']

class AdminOrRegistrarRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'registrar']
