from django.contrib import admin
from .models import (
    College,
    Program,
    Faculty,
    StudentInfo,
    AcademicTerm,
    Subject,
    SubjectPrerequisite
)

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("college_id", "college_name")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("program_id", "program_code", "program_name", "college")
    search_fields = ("program_code", "program_name")


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("faculty_id", "last_name", "first_name", "college", "email")
    search_fields = ("last_name", "first_name", "email")
    list_filter = ("college", "gender")


@admin.register(StudentInfo)
class StudentInfoAdmin(admin.ModelAdmin):
    list_display = ("student_id", "last_name", "first_name", "program", "year_level")
    search_fields = ("student_id", "last_name", "first_name")
    list_filter = ("college", "program", "year_level")


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ("term_id", "academic_year", "semester")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_id", "subject_code", "subject_name", "units", "year_level", "semester", "college")
    search_fields = ("subject_code", "subject_name")
    list_filter = ("college", "year_level", "semester")


@admin.register(SubjectPrerequisite)
class SubjectPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("subject", "prerequisite")
