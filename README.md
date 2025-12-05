# Tandikan Enrollment System

A comprehensive, role-based Enrollment and School Management System built with Django. This system streamlines the academic processes of a higher education institution, managing everything from student admission to grade encoding and financial assessment.

[📘 View Technical Documentation & Database Design](TECHNICAL_DOCS.md)

## 🚀 Features

### Core Functionality

* **Role-Based Access Control (RBAC)**: Distinct dashboards and permissions for Admins, Registrars, Cashiers, Faculty, and Students.
* **Secure Authentication**: Custom login/logout flows with session management.
* **System Logging**: Automated tracking of critical actions (logins, data modifications) for audit purposes.

### Academic Management

* **Structure Management**: Manage Colleges, Academic Programs, and Rooms.
* **Curriculum Management**: Create Subjects and define Prerequisites.
* **Term Management**: Open and close Academic Years and Semesters.

### Class Scheduling

* **Conflict Detection**: Smart validation prevents:
  * Room double-booking.
  * Instructor schedule conflicts.
  * Student schedule overlaps.
* **Flexible Schedules**: Supports complex day patterns (e.g., "MWF", "TTh").

### Enrollment Process

1. **Student Enrollment**: Students select subjects based on open schedules.
2. **Validation**: Registrars review and validate student study loads.
3. **Assessment & Payment**: Cashiers process payments and finalize enrollment.
4. **COR Generation**: Automatic generation of Certificate of Registration.

### Faculty Portal

* **Class Lists**: View students enrolled in specific sections.
* **Grading Sheet**: Input and submit student grades.
* **Schedule View**: Personalized view of teaching loads.

---

## 🛠️ Tech Stack

* **Backend**: Django 5.x (Python)
* **Frontend**: HTML5, CSS3, Bootstrap 5 (Mantis Template)
* **Database**: SQLite (Development) / MySQL/PostgreSQL (Production ready)
* **Styling**: Custom CSS overrides + Bootstrap utilities

---

## 📖 User Guide & Workflows

### 1. Initial System Setup (Admin)

Before enrollment can begin, the foundational data must be set up:

1. **Create Colleges**: Go to *Management > Colleges* to define the schools (e.g., College of Engineering).
2. **Create Programs**: Go to *Management > Programs* to define degrees (e.g., BSCS, BSIT) linked to Colleges.
3. **Create Rooms**: Go to *Management > Rooms* to define physical classrooms.
4. **Set Academic Term**: Go to *Management > Academic Terms* to create the current School Year and Semester.

### 2. Curriculum Setup (Registrar/Admin)

1. **Add Subjects**: Go to *Subjects > Subject List*. Define subject codes, descriptions, units, and lab fees.
2. **Set Prerequisites**: Go to *Subjects > Prerequisites* to enforce subject dependencies.

### 3. Class Scheduling (Registrar/Admin)

1. Navigate to *Class Schedules*.
2. Click **Create Schedule**.
3. Select the Subject, Instructor, Room, Day(s), and Time.
4. **Validation**: The system will automatically check for:
   * Is the room occupied at that time?
   * Is the instructor already teaching?
   * Does the schedule overlap with existing sections?

### 4. User Management

* **Faculty**: Create accounts for instructors. They will appear in the scheduling dropdowns.
* **Registrars/Cashiers**: Create staff accounts to delegate enrollment tasks.
* **Students**: Create student profiles. Students can then log in to view their dashboard.

### 5. The Enrollment Cycle

This is the core flow of the system:

#### Step A: Student Selection (Student/Staff)

* Students (or Staff on their behalf) select subjects from the *Open Schedules*.
* The system validates prerequisites and schedule conflicts.

#### Step B: Validation (Registrar)

* Registrar navigates to *Enrollment Management*.
* Reviews the student's selected subjects.
* Clicks **Validate** to approve the study load.

#### Step C: Payment (Cashier)

* Cashier navigates to *Payments*.
* Selects the student.
* Accepts payment (Full or Partial).
* The system records the transaction and updates the balance.

#### Step D: Finalization

* Once validated and paid, the student is officially **Enrolled**.
* The **Certificate of Registration (COR)** can be printed.
* The student appears in the Faculty's class list.

---

## ⚙️ Installation & Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Tandikan-Python
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations**

   ```bash
   cd tandikan_python
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the Server**

   ```bash
   python manage.py runserver
   ```

7. **Access the System**
   * Open browser at `http://127.0.0.1:8000`
   * Login with your superuser credentials.

---

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all modules, system logs, and user management. |
| **Registrar** | Manage students, subjects, schedules, and validate enrollments. |
| **Cashier** | Process payments and view assessment summaries. |
| **Faculty** | View class lists, schedules, and input grades. |
| **Student** | View grades, assessment, schedule, and enrollment status. |
