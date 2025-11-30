from django.db import models
from django.contrib.auth.models import AbstractUser


class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    college_name = models.CharField(max_length=255)


    def __str__(self):
        return self.college_name

class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_code = models.CharField(max_length=50)
    program_name = models.CharField(max_length=255)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.program_code} - {self.program_name}"


class Faculty(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    address = models.TextField()
    religion = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=50)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_number = models.CharField(max_length=50)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True)
    email = models.EmailField()

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class StudentInfo(models.Model):
    student_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    address = models.TextField()
    religion = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=50)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_number = models.CharField(max_length=50)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    year_level = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return f"{self.student_id} - {self.last_name}, {self.first_name}"


class AcademicTerm(models.Model):
    term_id = models.AutoField(primary_key=True)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.academic_year} - {self.semester}"



class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=255)
    units = models.IntegerField()
    year_level = models.IntegerField()
    semester = models.CharField(max_length=50)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"




class SubjectPrerequisite(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="prerequisites")
    prerequisite = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="required_for")

    def __str__(self):
        return f"{self.prerequisite} is a prerequisite for {self.subject}"