from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User, StudentInfo, College, Program, Subject, SubjectPrerequisite, ClassSchedule, AcademicTerm, Assessment, Payment, Enrollment, EnrollmentSubject, Faculty, ReportLog
from .forms import FacultyForm, RegistrarForm, AcademicTermForm, StudentForm, SubjectPrerequisiteForm
from .services.enrollment import enroll_student
from .services.assessment import generate_assessment
from .services.payments import record_payment
from django.utils.crypto import get_random_string
from django.db.models import Count, Sum, Q
import datetime
import csv
from django.http import HttpResponse
from .mixins.role_mixins import AdminRequiredMixin, RegistrarRequiredMixin, CashierRequiredMixin, FacultyRequiredMixin, StudentRequiredMixin, AdminOrRegistrarRequiredMixin

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
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Program.objects.count(),
        'total_colleges': College.objects.count(),
        'pending_enrollments': Enrollment.objects.count(), # Using total enrollments for now
    }
    return render(request, "tandikan_website/admin/dashboard.html", context)

def student_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect("login")
    
    context = {}
    try:
        student = StudentInfo.objects.get(user=request.user)
        # Get current term (simplified)
        term = AcademicTerm.objects.first()
        if term:
            context['current_semester'] = f"{term.academic_year} - {term.get_semester_display()}"
            enrollment = Enrollment.objects.filter(student=student, term=term).first()
            if enrollment:
                context['enrollment'] = enrollment
                enrolled_subjects = EnrollmentSubject.objects.filter(enrollment=enrollment)
                context['total_enrolled_subjects'] = enrolled_subjects.count()
                total_units = enrolled_subjects.aggregate(Sum('schedule__subject__units'))['schedule__subject__units__sum']
                context['total_units'] = total_units if total_units else 0
            else:
                context['total_enrolled_subjects'] = 0
                context['total_units'] = 0
        else:
            context['current_semester'] = "No Active Term"
            context['total_enrolled_subjects'] = 0
            context['total_units'] = 0
            
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

        # Generate Student ID (Simple logic: Year + Random)
        year = datetime.date.today().year
        random_str = get_random_string(length=5, allowed_chars='0123456789')
        student_id = f"{year}-{random_str}"

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
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
    }
    return render(request, "tandikan_website/cashier/dashboard.html", context)

def registrar_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'registrar':
        return redirect("login")
    
    context = {
        'total_students': StudentInfo.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Program.objects.count(),
        'total_colleges': College.objects.count(),
    }
    return render(request, "tandikan_website/registrar/dashboard.html", context)

def college_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "tandikan_website/college/dashboard.html")

def faculty_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'instructor':
        return redirect("login")
    return render(request, "tandikan_website/faculty/dashboard.html")

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

    # Get current term (simplified: just get the first one or active one)
    # In a real app, you'd have an 'is_active' flag or logic to determine current term
    term = AcademicTerm.objects.first() 
    if not term:
        messages.error(request, "No active academic term.")
        return redirect("student_dashboard")

    if request.method == "POST":
        schedule_ids = request.POST.getlist("schedule_ids")
        success, result = enroll_student(student, term.term_id, schedule_ids)
        
        if success:
            messages.success(request, "Enrollment successful!")
            return redirect("student_dashboard")
        else:
            messages.error(request, f"Enrollment failed: {result}")

    # Show available schedules
    schedules = ClassSchedule.objects.all()
    return render(request, "tandikan_website/student/enrollment.html", {'schedules': schedules, 'term': term})

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
    if not request.user.is_authenticated or request.user.role != 'cashier':
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
            
    return render(request, "tandikan_website/cashier/payment.html")

# --------------------------------------------------------
# CLASS SCHEDULING
# --------------------------------------------------------

def schedule_list(request):
    schedules = ClassSchedule.objects.all()
    base_template = get_base_template(request.user)
    return render(request, "shared_templates/college/schedule_list.html", {'schedules': schedules, 'base_template': base_template})

def schedule_create(request):
    base_template = get_base_template(request.user)
    if request.method == "POST":
        subject_id = request.POST.get("subject")
        instructor_id = request.POST.get("instructor")
        day = request.POST.get("day")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        room = request.POST.get("room")
        
        try:
            ClassSchedule.objects.create(
                subject_id=subject_id,
                instructor_id=instructor_id,
                day=day,
                start_time=start_time,
                end_time=end_time,
                room=room
            )
            messages.success(request, "Schedule created successfully.")
            return redirect("schedule_list")
        except Exception as e:
            messages.error(request, f"Error creating schedule: {e}")
            
    subjects = Subject.objects.all()
    instructors = Faculty.objects.all()
    return render(request, "shared_templates/college/schedule_form.html", {
        'subjects': subjects,
        'instructors': instructors,
        'base_template': base_template
    })

def schedule_delete(request, schedule_id):
    schedule = ClassSchedule.objects.get(pk=schedule_id)
    schedule.delete()
    messages.success(request, "Schedule deleted successfully.")
    return redirect("schedule_list")

# --------------------------------------------------------
# REPORTS
# --------------------------------------------------------

def reports_view(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar', 'cashier']:
        messages.error(request, "Access denied.")
        return redirect("login")

    # 1. Enrolled students per course and year level
    enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
    
    # 2. Total enrollment per semester
    semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))
    
    # 3. Collection report
    collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))
    
    # Log report generation
    ReportLog.objects.create(
        report_name="General Summary Report",
        generated_by=request.user
    )
    
    base_template = "admin_base.html"
    if request.user.role == "cashier":
        base_template = "cashier_base.html"
    elif request.user.role == "registrar":
        base_template = "registrar_base.html"

    return render(request, "tandikan_website/admin/reports.html", {
        'enrollment_stats': enrollment_stats,
        'semester_stats': semester_stats,
        'collection_stats': collection_stats,
        'base_template': base_template
    })

def export_reports(request):
    if not request.user.is_authenticated or request.user.role not in ['admin', 'registrar', 'cashier']:
        messages.error(request, "Access denied.")
        return redirect("login")
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="enrollment_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Report Type', 'Category', 'Count/Amount'])
    
    # 1. Enrolled students per course and year level
    enrollment_stats = Enrollment.objects.values('student__program__program_code', 'student__year_level').annotate(count=Count('student'))
    for stat in enrollment_stats:
        writer.writerow(['Enrollment per Course/Year', f"{stat['student__program__program_code']} - Year {stat['student__year_level']}", stat['count']])
        
    # 2. Total enrollment per semester
    semester_stats = Enrollment.objects.values('term__academic_year', 'term__semester').annotate(count=Count('student'))
    for stat in semester_stats:
        writer.writerow(['Enrollment per Semester', f"{stat['term__academic_year']} - {stat['term__semester']}", stat['count']])
        
    # 3. Collection report
    collection_stats = Payment.objects.values('date_paid__date').annotate(total=Sum('amount_paid'))
    for stat in collection_stats:
        writer.writerow(['Collection', str(stat['date_paid__date']), stat['total']])
        
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
    terms = AcademicTerm.objects.all().order_by('-academic_year', '-semester')
    return render(request, "shared_templates/academic_term/term_list.html", {'terms': terms})

def academic_term_create(request):
    if request.method == "POST":
        form = AcademicTermForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Academic Term created successfully.")
            return redirect("academic_term_list")
    else:
        form = AcademicTermForm()
    return render(request, "shared_templates/academic_term/term_form.html", {'form': form})

def academic_term_delete(request, term_id):
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
    return render(request, "tandikan_website/admin/assessment_list.html", {'assessments': assessments})

def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-date_paid')
    return render(request, "tandikan_website/admin/payment_list.html", {'payments': payments})

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
    term = AcademicTerm.objects.first() # Simplified: get active term

    if not term:
        messages.error(request, "No active academic term.")
        return redirect("student_list")

    if request.method == "POST":
        schedule_ids = request.POST.getlist("schedule_ids")
        success, result = enroll_student(student, term.term_id, schedule_ids)
        
        if success:
            messages.success(request, f"Successfully enrolled {student.first_name} {student.last_name}.")
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
        'base_template': base_template,
        'enrolled_schedule_ids': enrolled_schedule_ids
    })

def validate_enrollment(request, enrollment_id):
    # Cashier validates enrollment after payment
    if not request.user.is_authenticated or request.user.role != 'cashier':
        messages.error(request, "Access denied.")
        return redirect("login")
        
    enrollment = Enrollment.objects.get(pk=enrollment_id)
    enrollment.is_validated = True
    enrollment.save()
    
    messages.success(request, "Enrollment validated successfully.")
    return redirect("admin_payment_list")

def print_cor(request, enrollment_id):
    # Certificate of Registration
    enrollment = Enrollment.objects.get(pk=enrollment_id)
    
    if not enrollment.is_validated:
        messages.warning(request, "This enrollment is not yet validated.")
    
    subjects = EnrollmentSubject.objects.filter(enrollment=enrollment)
    assessment = Assessment.objects.filter(enrollment=enrollment).first()
    
    return render(request, "tandikan_website/student/cor.html", {
        'enrollment': enrollment,
        'subjects': subjects,
        'assessment': assessment
    })
