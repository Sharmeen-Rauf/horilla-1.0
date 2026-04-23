# WorkAura HRMS — Project Documentation

**Version:** 1.0  
**Product name:** WorkAura (HRMS)  
**Purpose:** Human Resource Management System to streamline HR processes and improve organizational efficiency.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Features & Modules](#4-features--modules)
5. [How Key Features Work](#5-how-key-features-work)
6. [What’s New / Customizations](#6-whats-new--customizations)
7. [Setup & Running the Project](#7-setup--running-the-project)
8. [First-Time Access & Login](#8-first-time-access--login)
9. [Configuration Reference](#9-configuration-reference)

---

## 1. Project Overview

WorkAura is a **full-featured HRMS** (Human Resource Management System) built on Django. It supports:

- **Multi-company** — Manage multiple companies from one installation.
- **Role-based access** — Permissions and user groups for employees, managers, and admins.
- **Multi-language** — English, German, Spanish, French, Arabic, Portuguese (BR), Chinese (Simplified & Traditional), Italian.
- **Audit trail** — History and change tracking on important data.
- **REST API** — For integrations and mobile apps.
- **White-label ready** — Brand name (e.g. WorkAura) configurable via context and UI.

The application is suitable for **HR teams** to manage the entire employee lifecycle: recruitment, onboarding, attendance, leave, payroll, performance, assets, and offboarding.

---

## 2. Technology Stack

| Layer        | Technology |
|-------------|------------|
| **Backend** | Python 3, Django 4.x |
| **Database**| SQLite (default in this setup) or PostgreSQL |
| **Frontend**| HTML5, CSS3, JavaScript, Bootstrap, HTMX, Alpine.js |
| **Charts**  | Chart.js |
| **Scheduling** | django-apscheduler (e.g. leave reset, disciplinary actions) |
| **Auth**    | Django auth, optional 2FA, password reset |
| **API**     | Django REST framework (REST API under `/api/`) |
| **Other**   | django-filter, simple-history, notifications, auditlog, Whitenoise (static files) |

---

## 3. System Architecture

- **Monolithic Django app** with multiple **Django apps** (modules).
- **Base** app provides: companies, departments, job positions, shifts, holidays, mail templates, and core auth/settings.
- **Feature apps** (employee, recruitment, leave, attendance, payroll, etc.) depend on **base** and **employee**.
- **Sidebar navigation** is driven by `SIDEBARS` in `horilla_apps.py` (recruitment, onboarding, employee, attendance, leave, payroll, PMS, offboarding, asset, helpdesk, project).
- **Context processors** supply global data (e.g. `white_label_company_name` for branding, breadcrumbs, companies).
- **Background jobs** (APScheduler) run tasks such as leave reset and disciplinary block/unblock on a schedule.

---

## 4. Features & Modules

### 4.1 Base (Core)

- **Companies** — Multiple companies; HQ and subsidiaries.
- **Departments** — Department hierarchy and management.
- **Job positions & job roles** — Define roles and positions.
- **Shifts & work types** — Employee shifts, rotating shifts, work types, shift requests.
- **Holidays** — Company holidays used for leave and attendance.
- **Company leaves** — Predefined company-wide leave days.
- **Mail templates** — Configurable email templates for notifications.
- **Mail automations** — Trigger-based email automation.
- **User groups & permissions** — Django groups and permission assignment.
- **Authentication** — Login, logout, forgot password, change password, optional 2FA.
- **Database initialization** — First-time setup: create admin user, company, department, job positions.
- **Demo data** — Load demo data (employees, leave, attendance, etc.) for testing.

### 4.2 Employee Management

- **Employee records** — Personal info, contact, gender, marital status, etc.
- **Work information** — Company, department, job position, shift, work type, reporting manager.
- **Badge ID** — Unique employee identifier.
- **Documents** — Employee document storage and management.
- **Tags** — Tag employees for filtering and grouping.
- **Disciplinary actions** — Track and manage disciplinary actions; scheduled block/unblock.
- **Policies** — View and manage HR policies.
- **Organisation chart** — Visual org structure.
- **Reports & pivot** — Employee reports and pivot views.

### 4.3 Recruitment

- **Recruitment pipeline** — Stages and pipeline view for open positions.
- **Candidates** — Candidate profiles, resumes, stages, hiring workflow.
- **Job positions** — Link recruitments to job positions.
- **Surveys** — Survey templates and candidate surveys.
- **Interview** — Schedule and manage interviews.
- **Offer letters** — Generate and manage offer letters.
- **Recruitment reports & pivot** — Analytics and pivot tables.

### 4.4 Onboarding

- **Onboarding dashboard** — Overview of onboarding progress.
- **Onboarding tasks** — Task lists and stages for new joiners.
- **Employee creation** — Create employee and user accounts from onboarding.
- **Welcome / portal** — Onboarding portal and welcome content.

### 4.5 Attendance

- **Check-in / Check-out** — Employees check in and out from navbar.
- **Attendance view** — Daily attendance records and validation.
- **Shifts & schedules** — Shift definitions and assignments.
- **Overtime** — Overtime tracking and approval.
- **Late come / early out** — Validation and grace settings.
- **Activity view** — Attendance activity log.
- **Request attendance** — Request attendance corrections.
- **Work records** — Work history and reports.
- **Reports & pivot** — Attendance reports and pivot views.
- **Biometric** (optional) — Integration with biometric devices.

### 4.6 Leave Management

- **Leave types** — Configure leave types (annual, sick, etc.) and reset rules.
- **Leave requests** — Employees request leave; multi-level approval supported.
- **Leave allocation** — Allocate leave days per employee/type.
- **Leave dashboard** — Overview of leave balance and requests.
- **Company leaves & holidays** — Integration with base holidays and company leaves.
- **Restrict leaves** — Rules to restrict leave by date or policy.
- **Compensatory leave** — Configure and use compensatory leave.
- **Reports & pivot** — Leave reports and pivot views.
- **Scheduled job** — Automatic leave reset (e.g. yearly) via scheduler.

### 4.7 Payroll

- **Contract** — Employee contracts.
- **Allowances & deductions** — Define allowances and deductions.
- **Payslip** — Generate and view payslips.
- **Loan / reimbursement** — Employee loans and reimbursement tracking.
- **Payroll dashboard** — Summary and quick actions.
- **Reports & pivot** — Payroll reports and pivot views.

### 4.8 Performance Management (PMS)

- **Objectives** — Set and track objectives (OKRs/KPIs).
- **Feedback** — Collect and manage feedback.
- **Key results** — Key results linked to objectives.
- **Meetings** — Schedule and log meetings.
- **Question templates** — Templates for reviews and surveys.
- **Periods** — Review periods and cycles.
- **Reports & pivot** — PMS reports and pivot views.

### 4.9 Asset Management

- **Asset category** — Categories for assets.
- **Assets** — Register and track assets.
- **Asset request & allocation** — Requests and allocation to employees.
- **Asset history** — History of allocations and returns.
- **Reports & pivot** — Asset reports and pivot views.

### 4.10 Offboarding

- **Offboarding pipeline** — Stages for offboarding.
- **Resignation requests** — Employee resignation requests and workflow.
- **Action types** — Types of offboarding actions.

### 4.11 Helpdesk

- **Tickets** — Create and manage support tickets.
- **Ticket types** — Categorize tickets.
- **FAQ** — FAQ categories and entries.
- **Tags** — Tag tickets.

### 4.12 Project (Optional module)

- **Project dashboard** — Overview of projects.
- **Projects** — Create and manage projects.
- **Timesheet** — Time logging per project/task.
- **Tasks** — Task management linked to projects.

### 4.13 Supporting / Platform Features

- **Notifications** — In-app notifications (navbar bell); mark read, clear.
- **Audit log** — Audit trail for model changes (auditlog).
- **Horilla audit** — Custom audit tags and logging.
- **Documents** — Central document management (horilla_documents).
- **Views** — Reusable view components (horilla_views).
- **Automations** — Mail and workflow automations (horilla_automations).
- **Backup** — Google Drive backup (horilla_backup) when configured.
- **Breadcrumbs** — Navigation breadcrumbs (horilla_crumbs) with configurable first item (e.g. WorkAura).
- **Accessibility** — Accessibility options (accessibility).
- **API** — REST API under `/api/` for external integrations.

---

## 5. How Key Features Work

### 5.1 First-Time Setup

1. Open **http://localhost:8000**.
2. Use **Initialize Database** or **Load Demo Data**.
3. Enter **DB_INIT_PASSWORD** from `.env`.
4. **Initialize Database**: create admin user (name, email, password), then company, department, job positions.
5. **Load Demo Data**: loads fixtures (users, employees, leave, attendance, etc.); then login with **admin** / **admin**.

### 5.2 Daily Usage (High Level)

- **Employees** — Log in → Dashboard shows announcements, quick stats, and widgets (e.g. attendance, leave).
- **Check-in/out** — Use the navbar button to check in and check out (attendance app).
- **Leave** — Request leave from Leave → Request; manager approves; balance updates.
- **Recruitment** — Create recruitment → add candidates → move through pipeline → hire.
- **Payroll** — Configure contract, allowances, deductions → generate payslips.
- **Settings** — Under Settings (gear icon): companies, departments, shifts, holidays, user groups, permissions, etc.

### 5.3 Permissions & Multi-Company

- Permissions are Django-based (groups and per-user permissions).
- **Company selection** (navbar) allows switching context when user has access to multiple companies.
- Sidebar and lists respect selected company where applicable.

### 5.4 Scheduled Jobs

- **Leave reset** — Runs on an interval (e.g. every 20 seconds in dev); resets leave balances per leave type rules.
- **Block/unblock disciplinary** — Runs on an interval; applies disciplinary action dates (block/unblock).
- Jobs require a **working database**; with SQLite they run when the server is running.

---

## 6. What’s New / Customizations

This section summarizes what has been customized or fixed in this project for your environment and branding.

### 6.1 WorkAura Branding

- **Product name** in the UI is **WorkAura** (replaced “Horilla” in user-facing text).
- **Where changed:**
  - **Context processor** (`base/context_processors.py`): default `white_label_company_name` set to **WorkAura**.
  - **Sidebar**: Brand title next to logo shows **WorkAura** (uses `white_label_company_name`).
  - **Breadcrumbs**: First breadcrumb (next to hamburger menu) shows **WorkAura**.
  - **Templates**: Login, auth, error pages, initialize-database, and related templates use WorkAura and example emails like `*@workaura.com`.
- **Unchanged:** Internal package/module names (e.g. `horilla`, `horilla_widgets`) to avoid breaking code and imports.

### 6.2 Database: SQLite by Default

- **Default database** is **SQLite** (`db.sqlite3`) so the project runs without installing PostgreSQL.
- **Configuration** in `.env`:
  - `DB_ENGINE=django.db.backends.sqlite3`
  - `DB_NAME=db.sqlite3`
  - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` left empty.
- **DATABASE_URL** is commented out so it does not override the above.
- For **production or larger deployments**, you can switch back to PostgreSQL by setting `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (and optionally `DATABASE_URL`) in `.env`.

### 6.3 OpenBLAS / NumPy Fix (Windows)

- On Windows, NumPy/OpenBLAS could cause: **“OpenBLAS error: Memory allocation still failed after 10 retries.”**
- **Fix applied:** In `manage.py`, set `OPENBLAS_NUM_THREADS=1` before any imports so OpenBLAS uses a single thread and avoids the allocation failure.

### 6.4 Other Fixes and Tweaks

- **PyMuPDF** — Version relaxed to `>=1.25.0` in `requirements.txt` for compatibility with Python 3.13 on Windows (avoids building from source).
- **Requests/chardet** — `chardet` pinned (e.g. `>=3.0.2,<6`) and a warning filter added in `manage.py` to suppress dependency version warnings during management commands.
- **Database init password** — Still read from `.env` (`DB_INIT_PASSWORD`); used for “Initialize Database” and “Load Demo Data” actions.

---

## 7. Setup & Running the Project

### 7.1 Prerequisites

- **Python** 3.10+ (3.13 supported with current requirements).
- **pip** and **venv** (for virtual environment).

### 7.2 Steps (Windows)

```powershell
# 1. Go to project directory
cd D:\horilla-1.0

# 2. Create and activate virtual environment (if not already done)
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Ensure .env exists (copy from .env.dist if needed) and has:
#   DB_ENGINE=django.db.backends.sqlite3
#   DB_NAME=db.sqlite3
#   DB_INIT_PASSWORD=<your-secret>

# 5. Run migrations
python manage.py migrate

# 6. (Optional) Compile translations
python manage.py compilemessages

# 7. Run the server
# If you previously had OpenBLAS errors on Windows:
set OPENBLAS_NUM_THREADS=1
python manage.py runserver
```

- Open **http://127.0.0.1:8000** in the browser.

### 7.3 Steps (Linux / macOS)

Use the same steps as above, but:

- Activate venv with: `source venv/bin/activate`
- Use `python3` and `pip3` if your system defaults to Python 2 for `python`.
- For OpenBLAS: `export OPENBLAS_NUM_THREADS=1` before `python manage.py runserver`.

### 7.4 Using PostgreSQL Instead of SQLite

1. Install and start PostgreSQL; create database and user (e.g. `horilla_main`, `horilla`).
2. In `.env` set:
   - `DB_ENGINE=django.db.backends.postgresql`
   - `DB_NAME=horilla_main`
   - `DB_USER=horilla`
   - `DB_PASSWORD=horilla`
   - `DB_HOST=localhost`
   - `DB_PORT=5432`
3. Run `python manage.py migrate` again.

---

## 8. First-Time Access & Login

| Action | What to do |
|--------|------------|
| **Create your own admin** | Click **Initialize Database** → enter **DB_INIT_PASSWORD** from `.env` → create admin user (name, email, password) → then complete company, department, job positions. |
| **Use demo data** | Click **Load Demo Data** → enter **DB_INIT_PASSWORD** → after load, login with **Username:** `admin`, **Password:** `admin`. |
| **DB init password** | Stored in `.env` as `DB_INIT_PASSWORD` (e.g. `d3f6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d` in this setup). |

After login, you land on the **Dashboard** (announcements, widgets, quick links). Use the **sidebar** to open each module (Employee, Recruitment, Attendance, Leave, Payroll, etc.).

---

## 9. Configuration Reference

### 9.1 Key `.env` Variables

| Variable | Purpose |
|----------|--------|
| `DEBUG` | Set to `False` in production. |
| `SECRET_KEY` | Django secret key; keep secure in production. |
| `ALLOWED_HOSTS` | Comma-separated hosts (e.g. `*` for dev). |
| `TIME_ZONE` | e.g. `Asia/Kolkata`. |
| `DB_ENGINE` | e.g. `django.db.backends.sqlite3` or `django.db.backends.postgresql`. |
| `DB_NAME` | Database name or path (e.g. `db.sqlite3`). |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Used when using PostgreSQL. |
| `DB_INIT_PASSWORD` | Password for Initialize Database and Load Demo Data. |

### 9.2 Optional Features

- **White labelling** — In `horilla/horilla_apps.py`, set `WHITE_LABELLING = True` to use company name from database as brand name.
- **Two-factor auth** — Set `TWO_FACTORS_AUTHENTICATION = True` in `horilla_apps.py` (and configure accordingly).
- **GCP storage** — Set `GOOGLE_APPLICATION_CREDENTIALS`, `GS_BUCKET_NAME`, and related vars in `.env` for media storage.
- **AWS** — If `AWS_ACCESS_KEY_ID` is set, the project can enable the `storages` app for S3.

---

## Summary for Your Boss

- **What it is:** WorkAura is an HRMS covering the full employee lifecycle: recruitment, onboarding, attendance, leave, payroll, performance, assets, offboarding, and helpdesk.
- **How it works:** Web app (Django); users log in and use the dashboard and sidebar to access modules; permissions and multi-company are built-in.
- **What’s new/done in this project:** Rebranded to WorkAura, default database set to SQLite for easy run, Windows OpenBLAS fix, dependency updates, and small stability fixes. The product is ready to demo and to hand over with this documentation for feature walkthrough and setup.

---

*End of documentation.*
