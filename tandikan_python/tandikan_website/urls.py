from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.landing_page, name="landing"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    
    # dashboard views per user role
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("cashier-dashboard/", views.cashier_dashboard, name="cashier_dashboard"),
    path("registrar-dashboard/", views.registrar_dashboard, name="registrar_dashboard"),
    path("college-dashboard/", views.college_dashboard, name="college_dashboard"),
    path("faculty-dashboard/", views.faculty_dashboard, name="faculty_dashboard"),
    
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    
    # Authentication URLs
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
]
