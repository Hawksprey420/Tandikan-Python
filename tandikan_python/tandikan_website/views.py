from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, StudentInfo, College, Program, Subject, SubjectPrerequisite, ClassSchedule, AcademicTerm, Assessment, Payment, Enrollment, EnrollmentSubject, Faculty, ReportLog, Room, SystemLog
from .forms import FacultyForm, RegistrarForm, AcademicTermForm, StudentForm, SubjectPrerequisiteForm, ProgramForm
from .services.enrollment import enroll_student
from .services.assessment import generate_assessment
from .services.payments import record_payment
from .services.schedule_subject_validation import validate_prerequisites, validate_schedule_conflicts, validate_class_creation
from django.utils.crypto import get_random_string
from django.db import models
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
import datetime
import csv
from django.http import HttpResponse
from .mixins.role_mixins import AdminRequiredMixin, RegistrarRequiredMixin, CashierRequiredMixin, FacultyRequiredMixin, StudentRequiredMixin, AdminOrRegistrarRequiredMixin
from xhtml2pdf import pisa
from django.template.loader import get_template

def get_base_template(user):
    if user.role == 'registrar':
        return 'registrar_base.html'
    elif user.role == 'cashier':
        return 'cashier_base.html'
    elif user.role == 'instructor':
        return 'faculty_base.html'
    return 'admin_base.html'

def landing_page(request):
    return render(request, "tandikan_website/landing.html")

def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect("login")
    
    # Recent Users
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    # Chart Data: Users by Role
    users_by_role = User.objects.values('role')\
        .annotate(count=models.Count('id'))\
        .order_by('-count')
        
    chart_labels = [entry['role'].capitalize() for entry in users_by_role]
    chart_data = [entry['count'] for entry in users_by_role]

    # Chart Data: Enrollments per Program (Enrollment Statistics)
    enrollments_per_program = Enrollment.objects.values('student__program__program_code')\
        .annotate(count=models.Count('enrollment_id'))\
        .order_by('-count')
    enrollment_labels = [entry['student__program__program_code'] for entry in enrollments_per_program]
    enrollment_data = [entry['count'] for entry in enrollments_per_program]

    # Recent Activity (Report Logs)
    recent_activity = ReportLog.objects.all().order_by('-timestamp')[:5]
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Program.objects.count(),
        'total_colleges': College.objects.count(),
        'pending_enrollments': Enrollment.objects.filter(is_validated=False).count(),
        'recent_users': recent_users,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'enrollment_labels': enrollment_labels,
        'enrollment_data': enrollment_data,
        'recent_activity': recent_activity,
    }
    return render(request, "tandikan_website/admin/dashboard.html", context)

def student_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect("login")
    
    context = {}
    try:
        student = StudentInfo.objects.get(user=request.user)
        context['student'] = student
        
        # Get all terms for selection
        all_terms = AcademicTerm.objects.all().order_by('-academic_year', '-semester')
        context['all_terms'] = all_terms

        # Determine selected term
        term_id = request.GET.get('term_id')
        if term_id:
            try:
                term = AcademicTerm.objects.get(pk=term_id)
            except AcademicTerm.DoesNotExist:
                term = AcademicTerm.objects.order_by('-term_id').first()
        else:
            term = AcademicTerm.objects.order_by('-term_id').first()

        context['term'] = term

        if term:
            context['current_semester'] = f"{term.academic_year} - {term.get_semester_display()}"
            enrollment = Enrollment.objects.filter(student=student, term=term).first()
            if enrollment:
                context['enrollment'] = enrollment
                
                # Schedule
                enrolled_subjects = EnrollmentSubject.objects.filter(enrollment=enrollment).select_related('schedule__subject', 'schedule__instructor')
                context['enrolled_subjects'] = enrolled_subjects
                context['total_enrolled_subjects'] = enrolled_subjects.count()
                
                total_units = enrolled_subjects.aggregate(Sum('schedule__subject__units'))['schedule__subject__units__sum']
                context['total_units'] = total_units if total_units else 0
                
                # Financials
                try:
                    assessment = Assessment.objects.get(enrollment=enrollment)
                    total_paid_agg = Payment.objects.filter(assessment=assessment).aggregate(Sum('amount_paid'))
                    total_paid = total_paid_agg['amount_paid__sum'] or 0
                    balance = assessment.total_amount - total_paid
                    
                    context['financial_status'] = {
                        'total_assessment': assessment.total_amount,
                        'total_paid': total_paid,
                        'balance': balance
                    }
                except Assessment.DoesNotExist:
                    context['financial_status'] = None

            else:
                context['total_enrolled_subjects'] = 0
                context['total_units'] = 0
                context['enrolled_subjects'] = []
                context['financial_status'] = None
        else:
            context['current_semester'] = "No Active Term"
            context['total_enrolled_subjects'] = 0
            context['total_units'] = 0
            context['enrolled_subjects'] = []
            context['financial_status'] = None
            
    except StudentInfo.DoesNotExist:
        pass
        
    return render(request, "tandikan_website/student/dashboard.html", context)

def register_view(request):
    if request.method == "POST":
        # Extract data from POST
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        username = request.POST.get("username")
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "tandikan_website/registration/register.html")

        # Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = 'student'
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Generate Student ID (Unique)
        year = datetime.date.today().year
        while True:
            random_str = get_random_string(length=5, allowed_chars='0123456789')
            student_id = f"{year}-{random_str}"
            if not StudentInfo.objects.filter(student_id=student_id).exists():
                break

        # Create StudentInfo
        StudentInfo.objects.create(
            student_id=student_id,
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            # Add other fields as needed from the form
            address=request.POST.get("address", ""),
            contact_no=request.POST.get("contact_no", ""),
            emergency_contact_name=request.POST.get("emergency_contact_name", ""),
            emergency_contact_number=request.POST.get("emergency_contact_number", ""),
        )
        
        messages.success(request, "Registration successful! Your Student ID is " + student_id)
        return redirect("login")

    return render(request, "tandikan_website/registration/register.html")

def cashier_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'cashier':
        return redirect("login")
    
    # Calculate totals
    total_collections = Payment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    today_collections = Payment.objects.filter(date_paid__date=datetime.date.today()).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    # Recent transactions
    recent_payments = Payment.objects.all().order_by('-date_paid')[:5]
    
    # Chart Data: Last 7 days collections
    last_7_days = datetime.date.today() - timedelta(days=6)
    daily_collections = Payment.objects.filter(date_paid__date__gte=last_7_days)\
        .annotate(date=TruncDate('date_paid'))\
        .values('date')\
        .annotate(total=Sum('amount_paid'))\
        .order_by('date')
        
    # Format for Chart.js
    chart_labels = []
    chart_data = []
    
    # Fill in missing days with 0
    current_date = last_7_days
    while current_date <= datetime.date.today():
        found = False
        for entry in daily_collections:
            if entry['date'] == current_date:
                chart_labels.append(current_date.strftime('%b %d'))
                chart_data.append(float(entry['total']))
                found = True
                break
        if not found:
            chart_labels.append(current_date.strftime('%b %d'))
            chart_data.append(0)
        current_date += timedelta(days=1)
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_collections': total_collections,
        'today_collections': today_collections,
        'recent_payments': recent_payments,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, "tandikan_website/cashier/dashboard.html", context)

def registrar_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'registrar':
        return redirect("login")
    
    # Recent Enrollments
    recent_enrollments = Enrollment.objects.all().order_by('-date_enrolled')[:5]
    
    # Chart Data: Enrollments per Program
    enrollments_per_program = Enrollment.objects.values('student__program__program_code')\
        .annotate(count=models.Count('enrollment_id'))\
        .order_by('-count')
        
    chart_labels = [entry['student__program__program_code'] for entry in enrollments_per_program]
    chart_data = [entry['count'] for entry in enrollments_per_program]
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Program.objects.count(),
        'total_colleges': College.objects.count(),
        'recent_enrollments': recent_enrollments,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, "tandikan_website/registrar/dashboard.html", context)

def college_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "tandikan_website/college/dashboard.html")

def faculty_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'instructor':
        return redirect("login")
    
    try:
        faculty = Faculty.objects.get(user=request.user)
        
        # Get schedules assigned to this faculty
        schedules = ClassSchedule.objects.filter(instructor=faculty)
        total_subjects = schedules.count()
        
        # Get total students enrolled in these schedules
        # We need to count distinct students across all schedules
        enrolled_students = EnrollmentSubject.objects.filter(schedule__in=schedules).values('enrollment__student').distinct()
        total_students = enrolled_students.count()
        
        # Chart Data: Students per Subject
        students_per_subject = EnrollmentSubject.objects.filter(schedule__in=schedules)\
            .values('schedule__subject__subject_code')\
            .annotate(count=models.Count('enrollment__student'))\
            .order_by('-count')
            
        chart_labels = [entry['schedule__subject__subject_code'] for entry in students_per_subject]
        chart_data = [entry['count'] for entry in students_per_subject]
        
        # Recent Activity (e.g., recent enrollments in their classes)
        recent_enrollments = EnrollmentSubject.objects.filter(schedule__in=schedules)\
            .order_by('-enrollment__date_enrolled')[:5]

        # Detailed Class List with Counts
        my_classes = []
        for sched in schedules:
            count = EnrollmentSubject.objects.filter(schedule=sched).count()
            my_classes.append({
                'schedule': sched,
                'student_count': count
            })

        # Determine Today's Classes
        today_weekday = datetime.datetime.today().weekday() # 0=Mon, 6=Sun
        # Simple mapping for "MWF", "TTh" style strings
        # This is a heuristic.
        day_map = {
            0: ['M', 'Mon'],
            1: ['T', 'Tue'], # careful with Th
            2: ['W', 'Wed'],
            3: ['Th', 'Thu'],
            4: ['F', 'Fri'],
            5: ['S', 'Sat'],
            6: ['Su', 'Sun']
        }
        
        todays_classes = []
        target_tokens = day_map.get(today_weekday, [])
        
        for cls in my_classes:
            sched_day = cls['schedule'].day
            # Check if any token is in the schedule day string
            # Special case for T vs Th: if today is Tuesday (1), we look for 'T' but not followed by 'h' if possible, 
            # but 'TTh' contains 'T'. 
            # Let's keep it simple:
            is_today = False
            if today_weekday == 1: # Tuesday
                if 'T' in sched_day and 'Th' not in sched_day: # Matches T but not Th? No, TTh has T.
                     # If sched_day is "TTh", it means Tue AND Thu. So it IS today.
                     is_today = True
                elif 'Tue' in sched_day:
                    is_today = True
                elif 'TTh' in sched_day: # Explicit TTh
                    is_today = True
            elif today_weekday == 3: # Thursday
                if 'Th' in sched_day or 'Thu' in sched_day:
                    is_today = True
            else:
                # Mon, Wed, Fri, Sat, Sun
                for token in target_tokens:
                    if token in sched_day:
                        is_today = True
                        break
            
            if is_today:
                todays_classes.append(cls)
            
    except Faculty.DoesNotExist:
        total_subjects = 0
        total_students = 0
        chart_labels = []
        chart_data = []
        recent_enrollments = []
        my_classes = []
        todays_classes = []

    context = {
        'total_subjects': total_subjects,
        'total_students': total_students,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'recent_enrollments': recent_enrollments,
        'my_classes': my_classes,
        'todays_classes': todays_classes,
    }
    return render(request, "tandikan_website/faculty/dashboard.html", context)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Allow login by email
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass # Let authenticate fail naturally

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on role
            if user.role == "admin":
                return redirect("admin_dashboard")
            elif user.role == "student":
                return redirect("student_dashboard")
            elif user.role == "registrar":
                return redirect("registrar_dashboard")
            elif user.role == "cashier":
                return redirect("cashier_dashboard")
            elif user.role == "instructor":
                return redirect("faculty_dashboard")
            else:
                return redirect("admin_dashboard")

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "tandikan_website/login/login.html")

def logout_view(request):
    logout(request)
    return redirect("landing")

# --------------------------------------------------------
# SUBJECT MANAGEMENT
# --------------------------------------------------------

def subject_list(request):
    subjects = Subject.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/subjects/subject_list.html", {'subjects': subjects, 'base_template': base_template})

def subject_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        subject_code = request.POST.get("subject_code")
        subject_name = request.POST.get("subject_name")
        units = request.POST.get("units")
        year_level = request.POST.get("year_level")
        semester = request.POST.get("semester")
        
        Subject.objects.create(
            subject_code=subject_code,
            subject_name=subject_name,
            units=units,
            year_level=year_level,
            semester=semester
        )
        messages.success(request, "Subject created successfully.")
        return redirect("subject_list")
    return render(request, "shared_templates/subjects/subject_form.html", {'base_template': base_template})

def subject_update(request, subject_id):
    subject = Subject.objects.get(pk=subject_id)
    base_template = get_base_template(request.user)
    if request.method == "POST":
        subject.subject_code = request.POST.get("subject_code")
        subject.subject_name = request.POST.get("subject_name")
        subject.units = request.POST.get("units")
        subject.year_level = request.POST.get("year_level")
        subject.semester = request.POST.get("semester")
        subject.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("subject_list")
    return render(request, "shared_templates/subjects/subject_form.html", {'subject': subject, 'base_template': base_template})

def subject_delete(request, subject_id):
    subject = Subject.objects.get(pk=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully.")
    return redirect("subject_list")

# --------------------------------------------------------
# ENROLLMENT
# --------------------------------------------------------

def enrollment_view(request):
    # Assuming logged in user is a student
    if not request.user.is_authenticated or request.user.role != 'student':
        messages.error(request, "Access denied.")
        return redirect("login")

    try:
        student = StudentInfo.objects.get(user=request.user)
    except StudentInfo.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_dashboard")

    # Get all terms for selection
    all_terms = AcademicTerm.objects.all().order_by('-academic_year', '-semester')
    
    # Determine selected term
    term_id = request.GET.get('term_id')
    if term_id:
        try:
            term = AcademicTerm.objects.get(pk=term_id)
        except AcademicTerm.DoesNotExist:
            term = AcademicTerm.objects.order_by('-term_id').first()
    else:
        term = AcademicTerm.objects.order_by('-term_id').first() # Get latest term

    if not term:
        messages.error(request, "No active academic term.")
        return redirect("student_dashboard")

    if request.method == "POST":
        # Use the term from the POST request to ensure consistency
        post_term_id = request.POST.get("term_id")
        if post_term_id:
            term = AcademicTerm.objects.get(pk=post_term_id)
            
        schedule_ids = request.POST.getlist("schedule_ids")
        success, result = enroll_student(student, term.term_id, schedule_ids)
        
        if success:
            messages.success(request, "Enrollment successful!")
            return redirect("student_dashboard")
        else:
            messages.error(request, f"Enrollment failed: {result}")

    # Show available schedules (Filtered by Program and Semester)
    # We include subjects for the student's program OR shared subjects (program is None)
    # We removed the year_level filter to allow students to see all available subjects for the term
    schedules = ClassSchedule.objects.filter(
        Q(subject__program=student.program) | Q(subject__program__isnull=True),
        subject__semester=term.semester
    )
    
    # Check if already enrolled
    current_enrollment = Enrollment.objects.filter(student=student, term=term).first()
    enrolled_schedule_ids = []
    if current_enrollment:
        enrolled_schedule_ids = list(EnrollmentSubject.objects.filter(enrollment=current_enrollment).values_list('schedule_id', flat=True))

    return render(request, "tandikan_website/student/enrollment.html", {
        'schedules': schedules, 
        'term': term,
        'all_terms': all_terms,
        'enrolled_schedule_ids': enrolled_schedule_ids
    })

# --------------------------------------------------------
# ASSESSMENT & PAYMENT
# --------------------------------------------------------

def assessment_view(request):
    # For student to view their assessment
    if not request.user.is_authenticated or request.user.role != 'student':
        messages.error(request, "Access denied.")
        return redirect("login")

    try:
        student = StudentInfo.objects.get(user=request.user)
        # Get latest enrollment
        enrollment = Enrollment.objects.filter(student=student).latest('date_enrolled')
        
        # Generate or get assessment
        assessment = generate_assessment(enrollment)
        
        payments = Payment.objects.filter(assessment=assessment)
        total_paid = sum(p.amount_paid for p in payments)
        balance = assessment.total_amount - total_paid
        
        return render(request, "tandikan_website/student/assessment.html", {
            'assessment': assessment,
            'payments': payments,
            'total_paid': total_paid,
            'balance': balance
        })
        
    except (StudentInfo.DoesNotExist, Enrollment.DoesNotExist):
        messages.error(request, "No enrollment record found.")
        return redirect("student_dashboard")

def payment_view(request):
    # For cashier to record payment
    if not request.user.is_authenticated or request.user.role not in ['cashier', 'admin']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    if request.method == "POST":
        assessment_id = request.POST.get("assessment_id")
        amount = request.POST.get("amount")
        
        success, result = record_payment(assessment_id, amount, request.user)
        
        if success:
            messages.success(request, "Payment recorded successfully.")
        else:
            messages.error(request, f"Payment failed: {result}")
            
    # Pre-fill assessment_id if provided in GET
    initial_assessment_id = request.GET.get('assessment_id', '')
            
    base_template = get_base_template(request.user)
    return render(request, "tandikan_website/cashier/payment.html", {
        'base_template': base_template,
        'initial_assessment_id': initial_assessment_id
    })

# --------------------------------------------------------
# CLASS SCHEDULING
# --------------------------------------------------------

def schedule_list(request):
    base_template = get_base_template(request.user)
    
    if request.user.role == 'instructor':
        try:
            faculty = Faculty.objects.get(user=request.user)
            schedules = ClassSchedule.objects.filter(instructor=faculty)
        except Faculty.DoesNotExist:
            schedules = ClassSchedule.objects.none()
    else:
        schedules = ClassSchedule.objects.all()

    return render(request, "shared_templates/college/schedule_list.html", {'schedules': schedules, 'base_template': base_template})

def schedule_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        subject_id = request.POST.get("subject")
        instructor_id = request.POST.get("instructor")
        day = request.POST.get("day")
        start_time_str = request.POST.get("start_time")
        end_time_str = request.POST.get("end_time")
        room = request.POST.get("room")
        section_name = request.POST.get("section_name", "")
        
        try:
            # Validate instructor mapping
            subject = Subject.objects.get(pk=subject_id)
            instructor = Faculty.objects.get(pk=instructor_id)
            
            # Parse times
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()

            if subject.college and instructor.college and subject.college != instructor.college:
                messages.warning(request, f"Note: Instructor {instructor} ({instructor.college}) is assigned to a subject under {subject.college}.")

            # Validate Conflicts
            is_valid, error_msg = validate_class_creation(instructor, room, day, start_time, end_time)
            if not is_valid:
                messages.error(request, error_msg)
                subjects = Subject.objects.all()
                instructors = Faculty.objects.all()
                rooms = Room.objects.all()
                return render(request, "shared_templates/college/schedule_form.html", {
                    'subjects': subjects,
                    'instructors': instructors,
                    'rooms': rooms,
                    'base_template': base_template,
                    'old_data': request.POST
                })

            ClassSchedule.objects.create(
                subject_id=subject_id,
                instructor_id=instructor_id,
                day=day,
                start_time=start_time,
                end_time=end_time,
                room=room,
                section_name=section_name
            )
            messages.success(request, "Schedule created successfully.")
            return redirect("schedule_list")
        except ValueError:
             messages.error(request, "Invalid time format.")
        except Exception as e:
            messages.error(request, f"Error creating schedule: {e}")
            
    subjects = Subject.objects.all()
    instructors = Faculty.objects.all()
    rooms = Room.objects.all()
    return render(request, "shared_templates/college/schedule_form.html", {
        'subjects': subjects,
        'instructors': instructors,
        'rooms': rooms,
        'base_template': base_template
    })

def schedule_delete(request, schedule_id):
    schedule = ClassSchedule.objects.get(pk=schedule_id)
    schedule.delete()
    messages.success(request, "Schedule deleted successfully.")
    return redirect("schedule_list")

# --------------------------------------------------------
# PROGRAM MANAGEMENT
# --------------------------------------------------------

def program_list(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
    
    programs = Program.objects.all().select_related('college')
    base_template = get_base_template(request.user)
    
    return render(request, "tandikan_website/admin/program_list.html", {
        'programs': programs,
        'base_template': base_template
    })

def program_create(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    base_template = get_base_template(request.user)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Program created successfully.")
            return redirect('program_list')
    else:
        form = ProgramForm()
        
    return render(request, "tandikan_website/admin/program_form.html", {
        'form': form,
        'base_template': base_template,
        'title': 'Create Program'
    })

def program_update(request, program_id):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    program = Program.objects.get(pk=program_id)
    base_template = get_base_template(request.user)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Program updated successfully.")
            return redirect('program_list')
    else:
        form = ProgramForm(instance=program)
        
    return render(request, "tandikan_website/admin/program_form.html", {
        'form': form,
        'base_template': base_template,
        'title': 'Edit Program'
    })

def program_delete(request, program_id):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    program = Program.objects.get(pk=program_id)
    program.delete()
    messages.success(request, "Program deleted successfully.")
    return redirect('program_list')

# --------------------------------------------------------
# REPORTS
# --------------------------------------------------------

def reports_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Access denied.")
        return redirect("login")

    # Initialize stats
    enrollment_stats = None
    semester_stats = None
    collection_stats = None
    faculty_subject_stats = None
    student_enrollment_history = None

    role = request.user.role

    # Admin: All reports
    if role == 'admin':
        enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
        semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))
        collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))

    # Registrar: Enrollment and Semester stats (Majority but not financial)
    elif role == 'registrar':
        enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
        semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))

    # Cashier: Only finances
    elif role == 'cashier':
        collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))

    # Faculty: Faculty related (Students per subject)
    elif role == 'instructor':
        try:
            faculty = Faculty.objects.get(user=request.user)
            faculty_subject_stats = EnrollmentSubject.objects.filter(schedule__instructor=faculty)\
                .values('schedule__subject__subject_code', 'schedule__subject__subject_name', 'schedule__section_name')\
                .annotate(count=Count('enrollment__student'))\
                .order_by('schedule__subject__subject_code')
        except Faculty.DoesNotExist:
            pass

    # Student: Enrollment History (Units per term)
    elif role == 'student':
        try:
            student = StudentInfo.objects.get(user=request.user)
            student_enrollment_history = Enrollment.objects.filter(student=student).order_by('-term__academic_year', '-term__semester')
            # We can annotate total units if needed, but let's just pass the enrollments for now
            # Or calculate units manually in template or here
        except StudentInfo.DoesNotExist:
            pass

    else:
        messages.error(request, "Access denied.")
        return redirect("login")
    
    # Log report generation
    ReportLog.objects.create(
        report_name=f"Report generated for {role}",
        generated_by=request.user
    )
    
    base_template = get_base_template(request.user)
    if role == 'student':
        base_template = 'student_base.html'

    return render(request, "tandikan_website/admin/reports.html", {
        'enrollment_stats': enrollment_stats,
        'semester_stats': semester_stats,
        'collection_stats': collection_stats,
        'faculty_subject_stats': faculty_subject_stats,
        'student_enrollment_history': student_enrollment_history,
        'base_template': base_template
    })

def export_reports(request):
    if not request.user.is_authenticated:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    report_format = request.GET.get('format', 'csv')
    role = request.user.role

    # Data Gathering (Same logic as reports_view)
    enrollment_stats = None
    semester_stats = None
    collection_stats = None
    faculty_subject_stats = None
    student_enrollment_history = None

    if role == 'admin':
        enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
        semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))
        collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))
    elif role == 'registrar':
        enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
        semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))
    elif role == 'cashier':
        collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))
    elif role == 'instructor':
        try:
            faculty = Faculty.objects.get(user=request.user)
            faculty_subject_stats = EnrollmentSubject.objects.filter(schedule__instructor=faculty)\
                .values('schedule__subject__subject_code', 'schedule__subject__subject_name', 'schedule__section_name')\
                .annotate(count=Count('enrollment__student'))\
                .order_by('schedule__subject__subject_code')
        except Faculty.DoesNotExist:
            pass
    elif role == 'student':
        try:
            student = StudentInfo.objects.get(user=request.user)
            student_enrollment_history = Enrollment.objects.filter(student=student).order_by('-term__academic_year', '-term__semester')
        except StudentInfo.DoesNotExist:
            pass

    if report_format == 'pdf':
        template_path = 'tandikan_website/reports/pdf_report.html'
        context = {
            'enrollment_stats': enrollment_stats,
            'semester_stats': semester_stats,
            'collection_stats': collection_stats,
            'faculty_subject_stats': faculty_subject_stats,
            'student_enrollment_history': student_enrollment_history,
            'generated_by': request.user,
            'date_generated': datetime.datetime.now()
        }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report.pdf"'
        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    # CSV Export (Default)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Report Type', 'Category', 'Count/Amount'])
    
    if enrollment_stats:
        for stat in enrollment_stats:
            writer.writerow(['Enrollment per Course/Year', f"{stat['student__program__program_code']} - Year {stat['student__year_level']}", stat['count']])
        
    if semester_stats:
        for stat in semester_stats:
            writer.writerow(['Enrollment per Semester', f"{stat['term__academic_year']} - {stat['term__semester']}", stat['count']])
        
    if collection_stats:
        for stat in collection_stats:
            writer.writerow(['Collection', str(stat['date_paid__date']), stat['total']])

    if faculty_subject_stats:
        writer.writerow([])
        writer.writerow(['Subject Code', 'Description', 'Section', 'Enrolled Count'])
        for stat in faculty_subject_stats:
            writer.writerow([stat['schedule__subject__subject_code'], stat['schedule__subject__subject_name'], stat['schedule__section_name'], stat['count']])

    if student_enrollment_history:
        writer.writerow([])
        writer.writerow(['Academic Year', 'Semester', 'Date Enrolled', 'Status'])
        for enrollment in student_enrollment_history:
            writer.writerow([enrollment.term.academic_year, enrollment.term.get_semester_display(), enrollment.date_enrolled, 'Validated' if enrollment.is_validated else 'Pending'])
        
    return response

# --------------------------------------------------------
# COLLEGE MANAGEMENT
# --------------------------------------------------------

def college_list(request):
    colleges = College.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/college/college_list.html", {'colleges': colleges, 'base_template': base_template})

def college_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        college_name = request.POST.get("college_name")
        College.objects.create(college_name=college_name)
        messages.success(request, "College created successfully.")
        return redirect("college_list")
    return render(request, "shared_templates/college/college_form.html", {'base_template': base_template})

def college_update(request, college_id):
    college = College.objects.get(pk=college_id)
    base_template = get_base_template(request.user)
    if request.method == "POST":
        college.college_name = request.POST.get("college_name")
        college.save()
        messages.success(request, "College updated successfully.")
        return redirect("college_list")
    return render(request, "shared_templates/college/college_form.html", {'college': college, 'base_template': base_template})

def college_delete(request, college_id):
    college = College.objects.get(pk=college_id)
    college.delete()
    messages.success(request, "College deleted successfully.")
    return redirect("college_list")

# --------------------------------------------------------
# FACULTY MANAGEMENT
# --------------------------------------------------------

def faculty_list(request):
    faculty_members = Faculty.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/faculty/faculty_list.html", {'faculty_members': faculty_members, 'base_template': base_template})

def faculty_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty member created successfully.")
            return redirect("faculty_list")
    else:
        form = FacultyForm()
    return render(request, "shared_templates/faculty/faculty_form.html", {'form': form, 'base_template': base_template})

def faculty_delete(request, faculty_id):
    faculty = Faculty.objects.get(pk=faculty_id)
    user = faculty.user
    faculty.delete()
    user.delete() # Delete associated user
    messages.success(request, "Faculty member deleted successfully.")
    return redirect("faculty_list")

# --------------------------------------------------------
# REGISTRAR MANAGEMENT
# --------------------------------------------------------

def registrar_list(request):
    registrars = User.objects.filter(role='registrar')
    return render(request, "tandikan_website/admin/registrar_list.html", {'registrars': registrars})

def registrar_create(request):
    if request.method == "POST":
        form = RegistrarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registrar account created successfully.")
            return redirect("registrar_list")
    else:
        form = RegistrarForm()
    return render(request, "tandikan_website/admin/registrar_form.html", {'form': form})

def registrar_delete(request, user_id):
    user = User.objects.get(pk=user_id)
    if user.role == 'registrar':
        user.delete()
        messages.success(request, "Registrar account deleted successfully.")
    return redirect("registrar_list")

# --------------------------------------------------------
# ACADEMIC TERM MANAGEMENT
# --------------------------------------------------------

def academic_term_list(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    terms = AcademicTerm.objects.all().order_by('-academic_year', '-semester')
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/academic_term/term_list.html", {'terms': terms, 'base_template': base_template})

def academic_term_create(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    base_template = get_base_template(request.user)
    if request.method == "POST":
        form = AcademicTermForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Academic Term created successfully.")
            return redirect("academic_term_list")
    else:
        form = AcademicTermForm()
    return render(request, "shared_templates/academic_term/term_form.html", {'form': form, 'base_template': base_template})

def academic_term_delete(request, term_id):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    term = AcademicTerm.objects.get(pk=term_id)
    term.delete()
    messages.success(request, "Academic Term deleted successfully.")
    return redirect("academic_term_list")

# --------------------------------------------------------
# ADMIN TANDIKAN FUNCTIONS (VIEW ONLY)
# --------------------------------------------------------

def admin_enrollment_list(request):
    enrollments = Enrollment.objects.all().order_by('-date_enrolled')
    base_template = get_base_template(request.user)
    return render(request, "tandikan_website/admin/enrollment_list.html", {'enrollments': enrollments, 'base_template': base_template})

def admin_assessment_list(request):
    assessments = Assessment.objects.all().order_by('-date_generated')
    base_template = get_base_template(request.user)
    return render(request, "tandikan_website/admin/assessment_list.html", {'assessments': assessments, 'base_template': base_template})

def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-date_paid')
    return render(request, "tandikan_website/admin/payment_list.html", {'payments': payments})

def admin_logs(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect("login")
        
    logs = SystemLog.objects.all()
    return render(request, "tandikan_website/admin/system_logs.html", {'logs': logs})

# --------------------------------------------------------
# STUDENT MANAGEMENT
# --------------------------------------------------------

def student_list(request):
    query = request.GET.get('q')
    if query:
        students = StudentInfo.objects.filter(
            Q(last_name__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(student_id__icontains=query)
        )
    else:
        students = StudentInfo.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/student/student_list.html", {'students': students, 'base_template': base_template})

def student_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student created successfully.")
            return redirect("student_list")
    else:
        form = StudentForm()
    return render(request, "shared_templates/student/student_form.html", {'form': form, 'base_template': base_template})

def student_update(request, student_id):
    student = StudentInfo.objects.get(pk=student_id)
    base_template = get_base_template(request.user)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("student_list")
    else:
        form = StudentForm(instance=student)
    return render(request, "shared_templates/student/student_form.html", {'form': form, 'update': True, 'base_template': base_template})

def student_delete(request, student_id):
    student = StudentInfo.objects.get(pk=student_id)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, "Student deleted successfully.")
    return redirect("student_list")

# --------------------------------------------------------
# PREREQUISITE MANAGEMENT
# --------------------------------------------------------

def prerequisite_list(request):
    prerequisites = SubjectPrerequisite.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/subjects/prerequisite_list.html", {'prerequisites': prerequisites, 'base_template': base_template})

def prerequisite_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        form = SubjectPrerequisiteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Prerequisite added successfully.")
            return redirect("prerequisite_list")
    else:
        form = SubjectPrerequisiteForm()
    return render(request, "shared_templates/subjects/prerequisite_form.html", {'form': form, 'base_template': base_template})

def prerequisite_delete(request, prereq_id):
    prereq = SubjectPrerequisite.objects.get(pk=prereq_id)
    prereq.delete()
    messages.success(request, "Prerequisite deleted successfully.")
    return redirect("prerequisite_list")

# --------------------------------------------------------
# STAFF ASSISTED ENROLLMENT
# --------------------------------------------------------

def staff_enroll_student(request, student_id):
    # Allow Admin, Registrar, or Faculty (if acting as advisor) to enroll students
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar', 'instructor']:
        messages.error(request, "Access denied.")
        return redirect("login")

    student = StudentInfo.objects.get(pk=student_id)
    
    # Get all terms for selection
    all_terms = AcademicTerm.objects.all().order_by('-academic_year', '-semester')
    
    # Determine selected term
    term_id = request.GET.get('term_id')
    if term_id:
        try:
            term = AcademicTerm.objects.get(pk=term_id)
        except AcademicTerm.DoesNotExist:
            term = AcademicTerm.objects.order_by('-term_id').first()
    else:
        term = AcademicTerm.objects.order_by('-term_id').first() # Get latest term

    if not term:
        messages.error(request, "No active academic term.")
        return redirect("student_list")

    if request.method == "POST":
        # Use the term from the POST request to ensure consistency
        post_term_id = request.POST.get("term_id")
        if post_term_id:
            term = AcademicTerm.objects.get(pk=post_term_id)
            
        schedule_ids = request.POST.getlist("schedule_ids")
        success, result = enroll_student(student, term.term_id, schedule_ids)
        
        if success:
            messages.success(request, f"Successfully enrolled {student.first_name} {student.last_name} for {term}.")
            return redirect("student_list")
        else:
            messages.error(request, f"Enrollment failed: {result}")

    # Show available schedules
    schedules = ClassSchedule.objects.all()
    base_template = get_base_template(request.user)
    
    # Check if already enrolled
    current_enrollment = Enrollment.objects.filter(student=student, term=term).first()
    enrolled_schedule_ids = []
    if current_enrollment:
        enrolled_schedule_ids = list(EnrollmentSubject.objects.filter(enrollment=current_enrollment).values_list('schedule_id', flat=True))

    return render(request, "tandikan_website/admin/staff_enrollment.html", {
        'student': student,
        'schedules': schedules,
        'term': term,
        'all_terms': all_terms,
        'base_template': base_template,
        'enrolled_schedule_ids': enrolled_schedule_ids
    })

def validate_enrollment(request, enrollment_id):
    # Cashier validates enrollment after payment
    if not request.user.is_authenticated or request.user.role not in ['cashier', 'admin']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    enrollment = Enrollment.objects.get(pk=enrollment_id)
    enrollment.is_validated = True
    enrollment.save()
    
    messages.success(request, "Enrollment validated successfully.")
    return redirect("admin_payment_list")

def print_cor(request, enrollment_id):
    # Certificate of Registration
    if not request.user.is_authenticated:
        return redirect("login")

    enrollment = Enrollment.objects.get(pk=enrollment_id)
    
    # Permission check
    if request.user.role == 'student' and enrollment.student.user != request.user:
        messages.error(request, "Access denied. You can only view your own COR.")
        return redirect("student_dashboard")
    
    if not enrollment.is_validated:
        messages.warning(request, "This enrollment is not yet validated.")
    
    subjects = EnrollmentSubject.objects.filter(enrollment=enrollment)
    assessment = Assessment.objects.filter(enrollment=enrollment).first()
    
    base_template = get_base_template(request.user)
    return render(request, "tandikan_website/student/cor.html", {
        'enrollment': enrollment,
        'subjects': subjects,
        'assessment': assessment,
        'base_template': base_template
    })

# --------------------------------------------------------
# ROOM MANAGEMENT
# --------------------------------------------------------

def room_list(request):
    rooms = Room.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/college/room_list.html", {'rooms': rooms, 'base_template': base_template})

def room_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        capacity = request.POST.get("capacity")
        building = request.POST.get("building")
        
        try:
            Room.objects.create(room_name=room_name, capacity=capacity, building=building)
            messages.success(request, "Room created successfully.")
            return redirect("room_list")
        except Exception as e:
            messages.error(request, f"Error creating room: {e}")
            
    return render(request, "shared_templates/college/room_form.html", {'base_template': base_template})

def room_delete(request, room_id):
    room = Room.objects.get(pk=room_id)
    room.delete()
    messages.success(request, "Room deleted successfully.")
    return redirect("room_list")
