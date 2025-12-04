from django import forms
from django.contrib.auth import get_user_model
from .models import Faculty, AcademicTerm, College, StudentInfo, SubjectPrerequisite, Program

User = get_user_model()

class FacultyForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Faculty
        fields = ['college', 'gender', 'address', 'contact_no', 'birth_date', 'emergency_contact', 'emergency_contact_name']
        widgets = {
            'college': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        # Custom save to handle User creation
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.role = 'instructor'
        user.save()

        faculty = super().save(commit=False)
        faculty.user = user
        faculty.first_name = self.cleaned_data['first_name']
        faculty.last_name = self.cleaned_data['last_name']
        faculty.email = self.cleaned_data['email']
        
        if commit:
            faculty.save()
        return faculty

class RegistrarForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.role = 'registrar'
        if commit:
            user.save()
        return user

class AcademicTermForm(forms.ModelForm):
    class Meta:
        model = AcademicTerm
        fields = ['academic_year', 'semester']

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['program_code', 'program_name', 'college']
        widgets = {
            'program_code': forms.TextInput(attrs={'class': 'form-control'}),
            'program_name': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.Select(attrs={'class': 'form-select'}),
        }

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StudentInfo
        fields = ['college', 'program', 'year_level', 'birth_date', 'contact_no', 'emergency_contact_name', 'emergency_contact_number', 'address']
        widgets = {
            'college': forms.Select(attrs={'class': 'form-select'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'year_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        # Custom save to handle User creation
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.role = 'student'
        user.save()

        # Generate Student ID (Simple logic: Year + Random)
        import datetime
        from django.utils.crypto import get_random_string
        year = datetime.date.today().year
        random_str = get_random_string(length=5, allowed_chars='0123456789')
        student_id = f"{year}-{random_str}"

        student = super().save(commit=False)
        student.student_id = student_id
        student.user = user
        student.first_name = self.cleaned_data['first_name']
        student.last_name = self.cleaned_data['last_name']
        student.email = self.cleaned_data['email']
        
        if commit:
            student.save()
        return student

class SubjectPrerequisiteForm(forms.ModelForm):
    class Meta:
        model = SubjectPrerequisite
        fields = ['subject', 'prerequisite']

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get("subject")
        prerequisite = cleaned_data.get("prerequisite")

        if subject and prerequisite and subject == prerequisite:
            raise forms.ValidationError("A subject cannot be a prerequisite of itself.")
        
        return cleaned_data
