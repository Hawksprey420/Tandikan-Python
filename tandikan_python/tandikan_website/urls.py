from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.landing_page, name="landing"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("officer-dashboard/", views.officer_dashboard, name="officer_dashboard"),
    path("login/", views.login_view, name="login"),
]
