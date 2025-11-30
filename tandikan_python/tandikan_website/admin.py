from django.contrib import admin
from .models import (
    User,
    College,
    Program,
    Faculty,
    StudentInfo,
    AcademicTerm,
    Subject,
    SubjectPrerequisite,
    ClassSchedule,
    Enrollment,
    EnrollmentSubject,
    Fee,
    Assessment,
    Payment,
    ReportLog
)

# --------------------------------------------------------
# USER
# --------------------------------------------------------

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")


# --------------------------------------------------------
# COLLEGES & PROGRAMS
# --------------------------------------------------------

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("college_id", "college_name")
    search_fields = ("college_name",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("program_id", "program_code", "program_name", "college")
    search_fields = ("program_code", "program_name")
    list_filter = ("college",)


# --------------------------------------------------------
# FACULTY & STUDENTS
# --------------------------------------------------------

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("faculty_id", "last_name", "first_name", "college", "email")
    search_fields = ("last_name", "first_name", "email")
    list_filter = ("college", "gender")


@admin.register(StudentInfo)
class StudentInfoAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "college", "program", "year_level")
    search_fields = ("student_id", "user__last_name", "user__first_name")
    list_filter = ("college", "program", "year_level")

    def full_name(self, obj):
        return f"{obj.user.last_name}, {obj.user.first_name}"


# --------------------------------------------------------
# ACADEMIC TERMS
# --------------------------------------------------------

@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ("term_id", "academic_year", "semester")
    list_filter = ("academic_year", "semester")


# --------------------------------------------------------
# SUBJECTS & PREREQUISITES
# --------------------------------------------------------

class SubjectPrerequisiteInline(admin.TabularInline):
    model = SubjectPrerequisite
    fk_name = "subject"
    extra = 1

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_code", "subject_name", "units", "year_level", "semester", "college", "program")
    search_fields = ("subject_code", "subject_name")
    list_filter = ("college", "program", "year_level", "semester")
    inlines = [SubjectPrerequisiteInline]


@admin.register(SubjectPrerequisite)
class SubjectPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("subject", "prerequisite")
    search_fields = ("subject__subject_code", "prerequisite__subject_code")


# --------------------------------------------------------
# CLASS SCHEDULING
# --------------------------------------------------------

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "schedule_id",
        "subject",
        "instructor",
        "day",
        "start_time",
        "end_time",
        "room",
    )
    search_fields = ("subject__subject_code", "room", "instructor__last_name")
    list_filter = ("day", "room", "instructor")


# --------------------------------------------------------
# ENROLLMENT SYSTEM
# --------------------------------------------------------

class EnrollmentSubjectInline(admin.TabularInline):
    model = EnrollmentSubject
    extra = 1


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("enrollment_id", "student", "term", "date_enrolled")
    search_fields = ("student__student_id", "student__user__last_name")
    list_filter = ("term", "student__program")
    inlines = [EnrollmentSubjectInline]


@admin.register(EnrollmentSubject)
class EnrollmentSubjectAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "schedule")
    search_fields = ("enrollment__student__student_id", "schedule__subject__subject_code")


# --------------------------------------------------------
# FEES, ASSESSMENT, PAYMENTS
# --------------------------------------------------------

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount")
    search_fields = ("name",)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("assessment_id", "enrollment", "total_units", "total_amount", "date_generated")
    search_fields = ("enrollment__student__student_id",)
    list_filter = ("date_generated",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "assessment", "amount_paid", "date_paid", "cashier")
    search_fields = ("assessment__enrollment__student__student_id",)
    list_filter = ("date_paid", "cashier")


# --------------------------------------------------------
# REPORT LOGGING
# --------------------------------------------------------

@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ("report_name", "generated_by", "timestamp")
    list_filter = ("timestamp", "generated_by")
    search_fields = ("report_name",)
