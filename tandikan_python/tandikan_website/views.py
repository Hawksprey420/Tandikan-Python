from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages


def landing_page(request):
    return render(request, "tandikan_website/landing.html")

def admin_dashboard(request):
    return render(request, "tandikan_website/admin/dashboard.html")

def student_dashboard(request):
    return render(request, "tandikan_website/student/dashboard.html")

def officer_dashboard(request):
    return render(request, "tandikan_website/admin/dashboard.html")

def register_view(request):
    return render(request, "tandikan_website/registration/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on role
            if user.role == "admin":
                return redirect("admin_dashboard")
            elif user.role == "student":
                return redirect("student_dashboard")
            else:
                return redirect("officer_dashboard")

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "tandikan_website/login/login.html")

# Create your views here.
