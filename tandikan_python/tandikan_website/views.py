from django.shortcuts import render

def landing_page(request):
    return render(request, "tandikan_website/landing.html")

def admin_dashboard(request):
    return render(request, "tandikan_website/admin/dashboard.html")

def student_dashboard(request):
    return render(request, "tandikan_website/student/dashboard.html")


def officer_dashboard(request):
    return render(request, "tandikan_website/admin/dashboard.html")

def login_view(request):
    return render(request, "tandikan_website/registration/login.html")

# Create your views here.
