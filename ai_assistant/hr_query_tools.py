"""
HR database query tools for the AI assistant.

These functions fetch live data from the Django ORM and return
human-readable text that gets injected into the LLM context.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from django.apps import apps


# ───────────────────────── Employee Tools ─────────────────────────


def get_employee_info(query: str) -> str:
    """Search for an employee by name and return their details."""
    from employee.models import Employee

    words = query.strip().split()
    qs = Employee.objects.filter(is_active=True)
    for w in words:
        qs = qs.filter(
            employee_first_name__icontains=w
        ) | Employee.objects.filter(
            employee_last_name__icontains=w
        ).filter(is_active=True)

    employee = qs.first()
    if not employee:
        return f"No employee found matching '{query}'."

    lines = [
        f"Name: {employee.get_full_name()}",
        f"Badge: {employee.badge_id or 'N/A'}",
        f"Email: {employee.email}",
        f"Phone: {employee.phone}",
        f"Gender: {employee.get_gender_display() if hasattr(employee, 'get_gender_display') else employee.gender}",
    ]

    work_info = getattr(employee, "employee_work_info", None)
    if work_info:
        lines.extend([
            f"Department: {work_info.department_id or 'N/A'}",
            f"Job Position: {work_info.job_position_id or 'N/A'}",
            f"Job Role: {work_info.job_role_id or 'N/A'}",
            f"Shift: {work_info.shift_id or 'N/A'}",
            f"Work Type: {work_info.work_type_id or 'N/A'}",
            f"Company: {work_info.company_id or 'N/A'}",
            f"Joining Date: {work_info.date_joining or 'N/A'}",
            f"Basic Salary: {work_info.basic_salary or 'N/A'}",
        ])
    return "\n".join(lines)


def get_employee_count() -> str:
    """Return total active employees and department-wise breakdown."""
    from employee.models import Employee, EmployeeWorkInformation
    from base.models import Department

    total = Employee.objects.filter(is_active=True).count()
    inactive = Employee.objects.filter(is_active=False).count()
    lines = [f"Total active employees: {total}", f"Inactive/archived: {inactive}"]

    departments = Department.objects.all()
    if departments.exists():
        lines.append("\nDepartment-wise breakdown:")
        for dept in departments:
            count = EmployeeWorkInformation.objects.filter(
                department_id=dept, employee_id__is_active=True
            ).count()
            if count > 0:
                lines.append(f"  • {dept.department}: {count}")

    return "\n".join(lines)


def get_recent_joiners(days: int = 30) -> str:
    """List employees who joined in the last N days."""
    from employee.models import EmployeeWorkInformation

    cutoff = date.today() - timedelta(days=days)
    recent = EmployeeWorkInformation.objects.filter(
        date_joining__gte=cutoff, employee_id__is_active=True
    ).select_related("employee_id", "department_id")

    if not recent.exists():
        return f"No employees joined in the last {days} days."

    lines = [f"Employees who joined in the last {days} days:"]
    for wi in recent[:20]:
        emp = wi.employee_id
        lines.append(
            f"  • {emp.get_full_name()} — {wi.department_id or 'No Dept'} — Joined {wi.date_joining}"
        )
    return "\n".join(lines)


# ───────────────────────── Leave Tools ────────────────────────────


def get_leave_summary(employee_name: str = "") -> str:
    """Get leave information."""
    if not apps.is_installed("leave"):
        return "Leave module is not installed."

    from employee.models import Employee

    lines = []

    if employee_name:
        emp = Employee.objects.filter(
            is_active=True, employee_first_name__icontains=employee_name
        ).first()
        if not emp:
            return f"No employee found matching '{employee_name}'."

        LeaveRequest = apps.get_model("leave", "LeaveRequest")
        requests = LeaveRequest.objects.filter(employee_id=emp).order_by("-start_date")[:10]
        lines.append(f"Leave requests for {emp.get_full_name()}:")
        if not requests:
            lines.append("  No leave requests found.")
        for lr in requests:
            lines.append(
                f"  • {lr.start_date} to {lr.end_date} | Status: {lr.status} | Type: {getattr(lr, 'leave_type_id', 'N/A')}"
            )
    else:
        LeaveRequest = apps.get_model("leave", "LeaveRequest")
        pending = LeaveRequest.objects.filter(status="requested").count()
        approved = LeaveRequest.objects.filter(status="approved").count()
        rejected = LeaveRequest.objects.filter(status="rejected").count()
        lines.append("Leave requests summary:")
        lines.append(f"  • Pending approval: {pending}")
        lines.append(f"  • Approved: {approved}")
        lines.append(f"  • Rejected: {rejected}")

    return "\n".join(lines)


# ───────────────────────── Attendance Tools ───────────────────────


def get_attendance_summary(employee_name: str = "") -> str:
    """Get attendance summary."""
    if not apps.is_installed("attendance"):
        return "Attendance module is not installed."

    Attendance = apps.get_model("attendance", "Attendance")
    today = date.today()
    month_start = today.replace(day=1)

    if employee_name:
        from employee.models import Employee
        emp = Employee.objects.filter(
            is_active=True, employee_first_name__icontains=employee_name
        ).first()
        if not emp:
            return f"No employee found matching '{employee_name}'."

        records = Attendance.objects.filter(
            employee_id=emp, attendance_date__gte=month_start
        )
        present = records.count()
        return (
            f"Attendance for {emp.get_full_name()} this month:\n"
            f"  • Days present: {present}\n"
            f"  • Period: {month_start} to {today}"
        )
    else:
        total_today = Attendance.objects.filter(attendance_date=today).count()
        from employee.models import Employee
        total_emp = Employee.objects.filter(is_active=True).count()
        return (
            f"Today's attendance ({today}):\n"
            f"  • Checked in: {total_today}\n"
            f"  • Total employees: {total_emp}\n"
            f"  • Attendance rate: {round(total_today / max(total_emp, 1) * 100, 1)}%"
        )


# ───────────────────────── Performance Tools ─────────────────────


def get_performance_summary() -> str:
    """Get PMS performance summary if module is installed."""
    if not apps.is_installed("pms"):
        return "Performance Management (PMS) module is not installed."

    lines = ["Performance Management Summary:"]
    try:
        Objective = apps.get_model("pms", "EmployeeObjective")
        total_obj = Objective.objects.count()
        lines.append(f"  • Total objectives: {total_obj}")
    except Exception:
        pass

    try:
        Feedback = apps.get_model("pms", "Feedback")
        total_fb = Feedback.objects.count()
        lines.append(f"  • Total feedback entries: {total_fb}")
    except Exception:
        pass

    try:
        KeyResult = apps.get_model("pms", "EmployeeKeyResult")
        total_kr = KeyResult.objects.count()
        lines.append(f"  • Total key results: {total_kr}")
    except Exception:
        pass

    if len(lines) == 1:
        lines.append("  No performance data available yet.")

    return "\n".join(lines)


# ───────────────────────── Recruitment Tools ─────────────────────


def get_recruitment_summary() -> str:
    """Get recruitment pipeline summary."""
    if not apps.is_installed("recruitment"):
        return "Recruitment module is not installed."

    lines = ["Recruitment Pipeline Summary:"]
    try:
        Recruitment = apps.get_model("recruitment", "Recruitment")
        active = Recruitment.objects.filter(is_active=True)
        lines.append(f"  • Active recruitments: {active.count()}")
        for r in active[:10]:
            lines.append(f"    - {r}")
    except Exception:
        pass

    try:
        Candidate = apps.get_model("recruitment", "Candidate")
        total = Candidate.objects.count()
        lines.append(f"  • Total candidates: {total}")
    except Exception:
        pass

    if len(lines) == 1:
        lines.append("  No recruitment data available.")

    return "\n".join(lines)


# ───────────────────────── Payroll Tools ─────────────────────────


def get_payroll_summary() -> str:
    """Get payroll summary."""
    if not apps.is_installed("payroll"):
        return "Payroll module is not installed."

    lines = ["Payroll Summary:"]
    try:
        Payslip = apps.get_model("payroll", "Payslip")
        total = Payslip.objects.count()
        lines.append(f"  • Total payslips generated: {total}")
    except Exception:
        pass

    try:
        Contract = apps.get_model("payroll", "Contract")
        active_contracts = Contract.objects.filter(contract_status="active").count()
        lines.append(f"  • Active contracts: {active_contracts}")
    except Exception:
        pass

    if len(lines) == 1:
        lines.append("  No payroll data available.")

    return "\n".join(lines)


# ───────────────────────── Dispatcher ────────────────────────────


def run_hr_query(question: str) -> str:
    """
    Dispatcher: analyse the user question and call the right tool(s).
    Returns context text to inject into the LLM prompt.
    """
    q = question.lower()
    results: list[str] = []

    # Employee count
    if any(kw in q for kw in ["how many employee", "total employee", "employee count", "kitne employee", "headcount", "workforce"]):
        results.append(get_employee_count())

    # Recent joiners
    if any(kw in q for kw in ["recent join", "new join", "who joined", "last month join", "naye employee", "new hire"]):
        days = 30
        m = re.search(r"(\d+)\s*day", q)
        if m:
            days = int(m.group(1))
        results.append(get_recent_joiners(days))

    # Leave
    if any(kw in q for kw in ["leave", "chutti", "leave balance", "leave request", "vacation", "time off", "pto"]):
        name = _extract_name(q, ["leave", "balance", "request", "status", "chutti", "ki", "ka", "ke", "kya", "hai", "show", "get", "for", "vacation", "time", "off", "pto"])
        results.append(get_leave_summary(name))

    # Attendance
    if any(kw in q for kw in ["attendance", "present", "absent", "hazri", "check in", "check-in"]):
        name = _extract_name(q, ["attendance", "present", "absent", "hazri", "summary", "report", "show", "get", "for", "today", "month", "of", "check"])
        results.append(get_attendance_summary(name))

    # Employee info lookup
    if any(kw in q for kw in ["employee info", "employee detail", "about employee", "tell me about", "show profile", "who is"]):
        name = _extract_name(q, ["employee", "info", "detail", "about", "tell", "me", "show", "profile", "who", "is", "the"])
        if name:
            results.append(get_employee_info(name))

    # Performance
    if any(kw in q for kw in ["performance", "kpi", "objective", "key result", "feedback", "appraisal", "review"]):
        results.append(get_performance_summary())

    # Recruitment
    if any(kw in q for kw in ["recruitment", "hiring", "candidate", "pipeline", "job opening", "vacancy", "recruit"]):
        results.append(get_recruitment_summary())

    # Payroll
    if any(kw in q for kw in ["payroll", "salary", "payslip", "contract", "compensation", "wage"]):
        results.append(get_payroll_summary())

    if not results:
        return ""

    return "\n\n---\n\n".join(results)


def _extract_name(question: str, stop_words: list) -> str:
    """Try to extract a person name from the question."""
    words = question.split()
    filtered = [w for w in words if w.lower() not in stop_words and len(w) > 2]
    return " ".join(filtered[-2:]) if filtered else ""
