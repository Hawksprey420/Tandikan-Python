from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone


# --------------------------------------------------------
# USER / ROLE SYSTEM
# --------------------------------------------------------

class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("registrar", "Registrar"),
        ("cashier", "Cashier"),
        ("instructor", "Instructor"),
        ("student", "Student"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # DO NOT redefine:
    # groups
    # user_permissions
    # Django already provides them.
    #
    # If you want custom related names (to avoid clashes), you override like this:

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="tandikan_user_groups",
        blank=True,
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="tandikan_user_permissions",
        blank=True,
    )

# --------------------------------------------------------
# COLLEGES, PROGRAMS, FACULTY, STUDENTS
# --------------------------------------------------------

class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    college_name = models.CharField(max_length=150)

    def __str__(self):
        return self.college_name


class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_code = models.CharField(max_length=20, unique=True)
    program_name = models.CharField(max_length=200)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    def __str__(self):
        return self.program_code


class Faculty(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10)
    address = models.CharField(max_length=300, blank=True)
    contact_no = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField()

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class StudentInfo(models.Model):
    student_id = models.CharField(primary_key=True, max_length=20)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    year_level = models.PositiveIntegerField(default=1)
    birth_date = models.DateField(null=True, blank=True)
    contact_no = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_number = models.CharField(max_length=50)
    address = models.CharField(max_length=300, blank=True)
    email = models.EmailField(max_length=254, blank=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.last_name}"


# --------------------------------------------------------
# ACADEMIC TERMS
# --------------------------------------------------------

class AcademicTerm(models.Model):
    SEM_CHOICES = [('1', '1st Semester'), ('2', '2nd Semester')]
    term_id = models.AutoField(primary_key=True)
    academic_year = models.CharField(max_length=9)  # e.g. 2024-2025
    semester = models.CharField(max_length=1, choices=SEM_CHOICES)

    class Meta:
        unique_together = ('academic_year', 'semester')

    def __str__(self):
        return f"{self.academic_year} - {self.get_semester_display()}"


# --------------------------------------------------------
# SUBJECTS & CURRICULUM
# --------------------------------------------------------

class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=200)
    units = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    year_level = models.PositiveIntegerField(default=1)
    semester = models.CharField(max_length=1, choices=[('1', '1st'), ('2', '2nd')])
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.subject_code


class SubjectPrerequisite(models.Model):
    subject = models.ForeignKey(Subject, related_name='main_subject', on_delete=models.CASCADE)
    prerequisite = models.ForeignKey(Subject, related_name='required_subject', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'prerequisite')

    def __str__(self):
        return f"{self.prerequisite} → {self.subject}"


# --------------------------------------------------------
# CLASS SCHEDULING
# --------------------------------------------------------

class ClassSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    day = models.CharField(max_length=20)            # e.g. MWF, TTh
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    class Meta:
        constraints = [
            # Prevent instructor double booking
            models.UniqueConstraint(
                fields=['instructor', 'day', 'start_time', 'end_time'],
                name='unique_instructor_schedule'
            ),
            # Prevent room double booking
            models.UniqueConstraint(
                fields=['room', 'day', 'start_time', 'end_time'],
                name='unique_room_schedule'
            ),
        ]

    def __str__(self):
        return f"{self.subject.subject_code} - {self.day} {self.start_time}-{self.end_time}"


# --------------------------------------------------------
# ENROLLMENT PROCESS
# --------------------------------------------------------

class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(StudentInfo, on_delete=models.CASCADE)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'term')

    def __str__(self):
        return f"{self.student.student_id} - {self.term}"


class EnrollmentSubject(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('enrollment', 'schedule')

    def __str__(self):
        return f"{self.enrollment} → {self.schedule}"


# --------------------------------------------------------
# FEES, ASSESSMENT, PAYMENT
# --------------------------------------------------------

class Fee(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"


class Assessment(models.Model):
    assessment_id = models.AutoField(primary_key=True)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE)
    total_units = models.PositiveIntegerField(default=0)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_generated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Assessment for {self.enrollment}"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(default=timezone.now)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Payment {self.amount_paid} for {self.assessment}"


# --------------------------------------------------------
# REPORT LOGGING
# --------------------------------------------------------

class ReportLog(models.Model):
    report_name = models.CharField(max_length=100)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.report_name
