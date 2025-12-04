from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path("", views.landing_page, name="landing"),
    
    # Dashboard views per user role
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("cashier-dashboard/", views.cashier_dashboard, name="cashier_dashboard"),
    path("registrar-dashboard/", views.registrar_dashboard, name="registrar_dashboard"),
    path("college-dashboard/", views.college_dashboard, name="college_dashboard"),
    path("faculty-dashboard/", views.faculty_dashboard, name="faculty_dashboard"),
    
    # Authentication URLs
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),

    # Subject Management
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/update/<int:subject_id>/", views.subject_update, name="subject_update"),
    path("subjects/delete/<int:subject_id>/", views.subject_delete, name="subject_delete"),

    # College Management
    path("colleges/", views.college_list, name="college_list"),
    path("colleges/create/", views.college_create, name="college_create"),
    path("colleges/update/<int:college_id>/", views.college_update, name="college_update"),
    path("colleges/delete/<int:college_id>/", views.college_delete, name="college_delete"),

    # Faculty Management
    path("faculty/", views.faculty_list, name="faculty_list"),
    path("faculty/create/", views.faculty_create, name="faculty_create"),
    path("faculty/delete/<int:faculty_id>/", views.faculty_delete, name="faculty_delete"),

    # Registrar Management
    path("registrars/", views.registrar_list, name="registrar_list"),
    path("registrars/create/", views.registrar_create, name="registrar_create"),
    path("registrars/delete/<int:user_id>/", views.registrar_delete, name="registrar_delete"),

    # Enrollment
    path("enrollment/", views.enrollment_view, name="enrollment"),

    # Assessment & Payment
    path("assessment/", views.assessment_view, name="assessment"),
    path("payment/", views.payment_view, name="payment"),

    # Class Scheduling
    path("schedules/", views.schedule_list, name="schedule_list"),
    path("schedules/create/", views.schedule_create, name="schedule_create"),
    path("schedules/delete/<int:schedule_id>/", views.schedule_delete, name="schedule_delete"),

    # Reports
    path("reports/", views.reports_view, name="reports"),
    path("reports/export/", views.export_reports, name="export_reports"),

    # Academic Term Management
    path("terms/", views.academic_term_list, name="academic_term_list"),
    path("terms/create/", views.academic_term_create, name="academic_term_create"),
    path("terms/delete/<int:term_id>/", views.academic_term_delete, name="academic_term_delete"),

    # Admin Tandikan Functions
    path("school-admin/enrollments/", views.admin_enrollment_list, name="admin_enrollment_list"),
    path("school-admin/assessments/", views.admin_assessment_list, name="admin_assessment_list"),
    path("school-admin/payments/", views.admin_payment_list, name="admin_payment_list"),

    # Student Management
    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.student_create, name="student_create"),
    path("students/delete/<str:student_id>/", views.student_delete, name="student_delete"),
    path("students/update/<str:student_id>/", views.student_update, name="student_update"),
    path("students/enroll/<str:student_id>/", views.staff_enroll_student, name="staff_enroll_student"), # New

    # Enrollment & Validation
    path("enrollment/validate/<int:enrollment_id>/", views.validate_enrollment, name="validate_enrollment"), # New
    path("enrollment/cor/<int:enrollment_id>/", views.print_cor, name="print_cor"), # New

    # Prerequisite Management
    path("prerequisites/", views.prerequisite_list, name="prerequisite_list"),
    path("prerequisites/create/", views.prerequisite_create, name="prerequisite_create"),
    path("prerequisites/delete/<int:prereq_id>/", views.prerequisite_delete, name="prerequisite_delete"),
]
