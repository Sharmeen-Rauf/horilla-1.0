"""
AI Workforce Intelligence Analyzers.

7 intelligence modules that collect live DB data
and send structured prompts to Ollama for analysis.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from django.apps import apps

# ─────────────────────────────────────────────────────────
# Helper: call Ollama
# ─────────────────────────────────────────────────────────

def _ask_ollama(system: str, user: str) -> str:
    """Send a system+user prompt to Ollama and return the reply."""
    from helpdesk.ai_service import chat
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return chat(messages)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. SENTIMENT & WELLBEING ANALYZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_sentiment(text: str) -> dict:
    """
    Analyze text for sentiment, risk level, issue type, and recommended action.
    Returns a dict with structured results.
    """
    system = """You are an HR Wellbeing Analyst. Analyze the text for workplace wellbeing signals.
Return ONLY valid JSON with these keys:
{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "confidence": 0.0-1.0,
  "risk_level": "none" | "low" | "medium" | "high",
  "risk_type": "none" | "burnout" | "disengagement" | "frustration" | "confusion" | "resignation_intent" | "toxic_environment",
  "issue_categories": ["workload", "communication", "management", "compensation", "culture", "growth", "other"],
  "morale_indicator": "high" | "moderate" | "low",
  "recommended_actions": ["action1", "action2"],
  "summary": "1-2 sentence professional summary"
}
Important: This is workplace wellbeing analysis, NOT medical diagnosis. Focus on actionable HR signals."""

    reply = _ask_ollama(system, f"Analyze this text:\n\n{text}")

    # Try to parse JSON from response
    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(reply[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "sentiment": "unknown",
        "confidence": 0,
        "risk_level": "unknown",
        "risk_type": "none",
        "issue_categories": [],
        "morale_indicator": "unknown",
        "recommended_actions": [],
        "summary": reply,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. BURNOUT RISK DETECTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_burnout_risk(employee=None) -> list[dict]:
    """
    Analyze burnout risk for one or all employees.
    Combines: attendance, late arrivals, overtime, leave frequency.
    Returns list of dicts with employee name and risk assessment.
    """
    from employee.models import Employee

    if employee:
        employees = [employee]
    else:
        employees = list(Employee.objects.filter(is_active=True)[:20])

    today = date.today()
    month_start = today.replace(day=1)
    three_months_ago = today - timedelta(days=90)

    results = []
    data_lines = []

    for emp in employees:
        stats = _collect_employee_stats(emp, month_start, three_months_ago, today)
        data_lines.append(f"Employee: {emp.get_full_name()}\n{stats}")

    if not data_lines:
        return [{"employee": "N/A", "risk": "No data available"}]

    system = """You are an HR Burnout Risk Analyst. Analyze employee data for burnout indicators.
For EACH employee, return a JSON array with objects:
{
  "employee": "Name",
  "risk_level": "low" | "medium" | "high",
  "risk_score": 1-10,
  "indicators": ["indicator1", "indicator2"],
  "recommended_actions": ["action1", "action2"],
  "summary": "1 sentence assessment"
}
Return ONLY the JSON array. Analyze patterns like: excessive overtime, frequent late arrivals, high leave usage, low attendance."""

    reply = _ask_ollama(system, "\n\n---\n\n".join(data_lines))

    try:
        start = reply.find("[")
        end = reply.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(reply[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return [{"employee": "Analysis", "risk_level": "unknown", "summary": reply}]


def _collect_employee_stats(emp, month_start, three_months_ago, today) -> str:
    """Collect attendance/leave/overtime stats for an employee."""
    lines = []

    # Attendance this month
    if apps.is_installed("attendance"):
        Attendance = apps.get_model("attendance", "Attendance")
        LateComeEarlyOut = apps.get_model("attendance", "AttendanceLateComeEarlyOut")

        month_attendance = Attendance.objects.filter(
            employee_id=emp, attendance_date__gte=month_start
        ).count()
        lines.append(f"  Attendance days this month: {month_attendance}")

        # Late arrivals last 3 months
        late_count = LateComeEarlyOut.objects.filter(
            employee_id=emp,
            type="late_come",
            attendance_id__attendance_date__gte=three_months_ago,
        ).count()
        lines.append(f"  Late arrivals (90 days): {late_count}")

        # Overtime
        OT = apps.get_model("attendance", "AttendanceOverTime")
        ot_records = OT.objects.filter(
            employee_id=emp, year=str(today.year)
        ).order_by("-month_sequence")[:3]
        for ot in ot_records:
            lines.append(f"  OT {ot.month}: worked={ot.worked_hours}, overtime={ot.overtime}, pending={ot.pending_hours}")

    # Leave requests last 3 months
    if apps.is_installed("leave"):
        LeaveRequest = apps.get_model("leave", "LeaveRequest")
        leave_count = LeaveRequest.objects.filter(
            employee_id=emp,
            start_date__gte=three_months_ago,
        ).count()
        sick_leaves = LeaveRequest.objects.filter(
            employee_id=emp,
            start_date__gte=three_months_ago,
            leave_type_id__name__icontains="sick",
        ).count()
        lines.append(f"  Leave requests (90 days): {leave_count}")
        lines.append(f"  Sick leaves (90 days): {sick_leaves}")

    return "\n".join(lines) if lines else "  No data available"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ORGANIZATION HEALTH DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_org_health() -> dict:
    """
    Cross-module analysis: attendance, leave, complaints, performance.
    Returns dict with health score, insights, and alerts.
    """
    from employee.models import Employee

    today = date.today()
    month_start = today.replace(day=1)
    data_parts = []

    # Employee counts
    total_emp = Employee.objects.filter(is_active=True).count()
    data_parts.append(f"Total active employees: {total_emp}")

    # Attendance stats
    if apps.is_installed("attendance"):
        Attendance = apps.get_model("attendance", "Attendance")
        today_present = Attendance.objects.filter(attendance_date=today).count()
        LateCome = apps.get_model("attendance", "AttendanceLateComeEarlyOut")
        month_late = LateCome.objects.filter(
            type="late_come",
            attendance_id__attendance_date__gte=month_start,
        ).count()
        data_parts.append(f"Today present: {today_present}/{total_emp}")
        data_parts.append(f"Late arrivals this month: {month_late}")

    # Leave stats
    if apps.is_installed("leave"):
        LeaveRequest = apps.get_model("leave", "LeaveRequest")
        pending = LeaveRequest.objects.filter(status="requested").count()
        on_leave_today = LeaveRequest.objects.filter(
            status="approved", start_date__lte=today, end_date__gte=today
        ).count()
        data_parts.append(f"Pending leave requests: {pending}")
        data_parts.append(f"On leave today: {on_leave_today}")

    # Helpdesk / Complaints
    if apps.is_installed("helpdesk"):
        Ticket = apps.get_model("helpdesk", "Ticket")
        open_tickets = Ticket.objects.exclude(status__in=["resolved", "canceled"]).count()
        complaints = Ticket.objects.filter(
            ticket_type__type="complaint",
            created_date__gte=month_start,
        ).count()
        high_priority = Ticket.objects.filter(
            priority="high"
        ).exclude(status__in=["resolved", "canceled"]).count()
        data_parts.append(f"Open helpdesk tickets: {open_tickets}")
        data_parts.append(f"Complaints this month: {complaints}")
        data_parts.append(f"High priority open tickets: {high_priority}")

    # Performance
    if apps.is_installed("pms"):
        try:
            EmpObj = apps.get_model("pms", "EmployeeObjective")
            total_objectives = EmpObj.objects.count()
            data_parts.append(f"Total employee objectives: {total_objectives}")
            Feedback = apps.get_model("pms", "Feedback")
            total_feedback = Feedback.objects.count()
            data_parts.append(f"Total feedback entries: {total_feedback}")
        except Exception:
            pass

    data_text = "\n".join(data_parts)

    system = """You are an AI Organization Health Analyst. Analyze the HR data and produce a health report.
Return ONLY valid JSON:
{
  "health_score": 1-100,
  "health_status": "excellent" | "good" | "fair" | "concerning" | "critical",
  "key_insights": ["insight1", "insight2", "insight3"],
  "risk_alerts": [
    {"type": "burnout|attrition|engagement|compliance", "severity": "low|medium|high", "message": "..."}
  ],
  "department_highlights": ["highlight1", "highlight2"],
  "recommended_actions": [
    {"action": "...", "priority": "immediate|soon|planned", "reason": "..."}
  ],
  "summary": "2-3 sentence executive summary"
}"""

    reply = _ask_ollama(system, f"Organization data as of {today}:\n\n{data_text}")

    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(reply[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "health_score": 0,
        "health_status": "unknown",
        "key_insights": [],
        "risk_alerts": [],
        "recommended_actions": [],
        "summary": reply,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. AI PERFORMANCE NARRATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def narrate_performance(employee_name: str) -> str:
    """
    Auto-generate a written performance summary from KPIs, objectives,
    attendance, and feedback data.
    """
    from employee.models import Employee

    emp = Employee.objects.filter(
        is_active=True, employee_first_name__icontains=employee_name
    ).first()
    if not emp:
        return f"No employee found matching '{employee_name}'."

    data_parts = [f"Employee: {emp.get_full_name()}"]

    # Work info
    wi = getattr(emp, "employee_work_info", None)
    if wi:
        data_parts.append(f"Department: {wi.department_id or 'N/A'}")
        data_parts.append(f"Position: {wi.job_position_id or 'N/A'}")
        data_parts.append(f"Joined: {wi.date_joining or 'N/A'}")

    today = date.today()
    three_months_ago = today - timedelta(days=90)

    # Attendance
    if apps.is_installed("attendance"):
        Attendance = apps.get_model("attendance", "Attendance")
        total_days = Attendance.objects.filter(
            employee_id=emp, attendance_date__gte=three_months_ago
        ).count()
        LateCome = apps.get_model("attendance", "AttendanceLateComeEarlyOut")
        late = LateCome.objects.filter(
            employee_id=emp, type="late_come",
            attendance_id__attendance_date__gte=three_months_ago,
        ).count()
        data_parts.append(f"Attendance (90 days): {total_days} days")
        data_parts.append(f"Late arrivals (90 days): {late}")

    # PMS
    if apps.is_installed("pms"):
        try:
            EmpObj = apps.get_model("pms", "EmployeeObjective")
            objectives = EmpObj.objects.filter(employee_id=emp)
            for obj in objectives[:5]:
                data_parts.append(f"Objective: {obj.objective_id} | Status: {obj.status}")
            EmpKR = apps.get_model("pms", "EmployeeKeyResult")
            krs = EmpKR.objects.filter(employee_id=emp)
            for kr in krs[:5]:
                data_parts.append(f"Key Result: {kr.key_result_id} | Progress: {kr.progress}%")
        except Exception:
            pass

    # Leave
    if apps.is_installed("leave"):
        LeaveRequest = apps.get_model("leave", "LeaveRequest")
        leaves = LeaveRequest.objects.filter(
            employee_id=emp, start_date__gte=three_months_ago
        ).count()
        data_parts.append(f"Leave requests (90 days): {leaves}")

    system = """You are an HR Performance Reviewer. Write a professional, narrative performance summary.
Guidelines:
- Write in third person, professional tone
- Cover: attendance consistency, goal achievement, strengths, areas for improvement
- Be balanced — mention both positives and development areas
- Keep it to 3-4 paragraphs
- End with a recommendation (promotion readiness, training needs, etc.)
Do NOT use JSON. Write natural prose."""

    return _ask_ollama(system, "\n".join(data_parts))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. SMART COMPLAINT CLASSIFIER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_complaint(text: str) -> dict:
    """Classify complaint text into categories with severity."""
    system = """You are an HR Complaint Classifier. Analyze the complaint and classify it.
Return ONLY valid JSON:
{
  "category": "payroll" | "harassment" | "workload" | "manager_issue" | "policy_confusion" | "leave_issue" | "discrimination" | "workplace_safety" | "other",
  "severity": "low" | "medium" | "high" | "critical",
  "urgency": "routine" | "soon" | "immediate",
  "suggested_handler": "HR Manager" | "Department Head" | "Legal" | "Senior Management" | "Compliance Officer",
  "risk_flags": ["harassment_risk", "legal_risk", "attrition_risk", "compliance_risk"],
  "recommended_actions": ["action1", "action2"],
  "needs_investigation": true | false,
  "summary": "1 sentence professional summary"
}"""

    reply = _ask_ollama(system, f"Complaint:\n{text}")

    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(reply[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"category": "other", "severity": "unknown", "summary": reply}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. MANAGER COPILOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_manager_copilot(manager_employee) -> dict:
    """
    Generate AI briefing for a manager about their direct reports.
    """
    from employee.models import Employee, EmployeeWorkInformation

    # Find team members
    team = EmployeeWorkInformation.objects.filter(
        reporting_manager_id=manager_employee, employee_id__is_active=True
    ).select_related("employee_id")

    if not team.exists():
        return {"team_size": 0, "briefing": "No direct reports found."}

    today = date.today()
    month_start = today.replace(day=1)
    data_parts = [f"Manager: {manager_employee.get_full_name()}", f"Team size: {team.count()}", ""]

    for wi in team[:15]:
        emp = wi.employee_id
        emp_data = [f"- {emp.get_full_name()} ({wi.job_position_id or 'N/A'})"]

        if apps.is_installed("attendance"):
            Attendance = apps.get_model("attendance", "Attendance")
            days = Attendance.objects.filter(
                employee_id=emp, attendance_date__gte=month_start
            ).count()
            LateCome = apps.get_model("attendance", "AttendanceLateComeEarlyOut")
            late = LateCome.objects.filter(
                employee_id=emp, type="late_come",
                attendance_id__attendance_date__gte=month_start
            ).count()
            emp_data.append(f"  Attendance this month: {days} days, Late: {late}")

        if apps.is_installed("leave"):
            LR = apps.get_model("leave", "LeaveRequest")
            pending = LR.objects.filter(employee_id=emp, status="requested").count()
            if pending:
                emp_data.append(f"  Pending leave requests: {pending}")

        data_parts.append("\n".join(emp_data))

    system = """You are an AI Manager Copilot. Provide a daily briefing for the manager.
Return ONLY valid JSON:
{
  "team_health": "excellent" | "good" | "fair" | "needs_attention",
  "priority_alerts": [
    {"employee": "Name", "alert": "...", "action": "..."}
  ],
  "talking_points": ["point1 for 1:1 meetings", "point2"],
  "recognitions": ["Name deserves appreciation for..."],
  "concerns": ["Name may need support because..."],
  "weekly_focus": "1 sentence suggested focus area"
}"""

    reply = _ask_ollama(system, "\n".join(data_parts))

    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(reply[start:end])
            result["team_size"] = team.count()
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    return {"team_size": team.count(), "briefing": reply}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. AI ACTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def suggest_actions(context: str) -> dict:
    """
    Given an HR context/situation, suggest specific actions with
    confidence scores and reasons.
    """
    system = """You are an HR Action Advisor. Based on the context, recommend specific HR actions.
Return ONLY valid JSON:
{
  "actions": [
    {
      "action": "Schedule 1:1 meeting" | "Send wellbeing survey" | "Recommend leave" | "Draft warning email" | "Draft appreciation note" | "Suggest training" | "Mark for HR review" | "Assign mentor" | "Create follow-up task" | "other",
      "target": "employee or team name",
      "priority": "immediate" | "within_48h" | "this_week" | "planned",
      "confidence": 0.0-1.0,
      "reason": "why this action",
      "requires_approval": true | false
    }
  ],
  "risk_assessment": "low" | "medium" | "high",
  "summary": "1-2 sentence overview"
}
Important: Sensitive actions (termination, salary changes, final warnings) MUST have requires_approval=true."""

    reply = _ask_ollama(system, context)

    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(reply[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"actions": [], "summary": reply}
