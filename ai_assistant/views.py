"""
Views for the AI HR Assistant.
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# ── Comprehensive HR AI System Prompt ────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are **WorkAura AI** — an expert AI-powered HR assistant embedded inside the WorkAura HRMS platform.

## Your Core Capabilities
1. **HR Policy Expert** — Leave, attendance, payroll, recruitment, performance rules.
2. **Employee Support** — Leave balance, attendance, payslips, benefits queries.
3. **Resume & Hiring Advisor** — Analyse candidates, suggest interview questions, evaluate skills.
4. **Performance Analyst** — Interpret KPIs, objectives, feedback, and recommend actions.
5. **Sentiment Analyzer** — Analyze text for wellbeing signals, morale, and burnout risk.
6. **Burnout Risk Detector** — Identify employees at risk based on attendance/leave patterns.
7. **Complaint Classifier** — Categorize complaints and suggest appropriate handlers.
8. **Decision Support** — Recommendations for promotions, training, workforce planning.
9. **Manager Copilot** — Daily briefings, talking points, team health assessment.

## Current User
- Name: {user_name}
- Role: {user_role}

## HR Policy Knowledge
{hr_policies}

## Guidelines
- Be professional, clear, and concise.
- Use bullet points and structured formatting.
- For sentiment analysis: use "wellbeing signals" not "emotion detection".
- For predictions: always include confidence level and disclaim this is a signal, not diagnosis.
- Support both English and Urdu/Hindi queries.
- Sensitive actions (termination, salary, warnings) must note: "Requires manager approval."

{live_data_section}

{faq_section}
"""

HR_POLICIES = """
### Leave Policy
- Casual Leave: 12 days/year, Sick Leave: 10 days/year, Annual Leave: 15 days/year
- Maternity: 90 days, Paternity: 7 days
- Requests: 3 days advance (except emergencies)
- Unused casual leaves: no carry-forward. Earned leaves: carry up to 30 days.

### Attendance Policy
- Standard: 9 AM – 6 PM, Grace: 15 min
- 3 late arrivals/month = 1 casual leave deducted
- WFH requires manager approval

### Payroll Policy
- Processed last working day of month
- Overtime: 1.5x weekday, 2x weekend

### Performance Review
- Annual reviews: December, Mid-year: June
- Rating: 1 (Needs Improvement) to 5 (Outstanding)
- Promotion: min 1 year + rating ≥ 4
"""


@login_required
def ai_chat_page(request):
    """Render the AI HR Assistant chat page."""
    return render(request, "ai_assistant/chat.html")


@login_required
def ai_dashboard_page(request):
    """Render the AI Organization Health Dashboard."""
    return render(request, "ai_assistant/dashboard.html")


@login_required
@require_http_methods(["POST"])
def ai_chat_api(request):
    """Handle chat message and return AI response as JSON."""
    try:
        data = json.loads(request.body)
        user_message = (data.get("message") or "").strip()
        history = data.get("history", [])
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not user_message:
        return JsonResponse({"error": "Message is required"}, status=400)

    employee = getattr(request.user, "employee_get", None)
    user_name = employee.get_full_name() if employee else request.user.username
    user_role = "Admin" if request.user.is_superuser else "Employee"

    # DB context
    db_context = ""
    try:
        from ai_assistant.hr_query_tools import run_hr_query
        db_context = run_hr_query(user_message)
    except Exception:
        pass

    # Check if user wants analysis features
    q = user_message.lower()
    analysis_context = ""

    try:
        from ai_assistant.ai_analyzers import (
            analyze_sentiment, detect_burnout_risk,
            narrate_performance, classify_complaint,
            generate_org_health, suggest_actions,
        )

        if any(kw in q for kw in ["sentiment", "analyze text", "wellbeing", "morale analysis", "tone analysis"]):
            result = analyze_sentiment(user_message)
            analysis_context = f"📊 SENTIMENT ANALYSIS:\n{json.dumps(result, indent=2)}"

        elif any(kw in q for kw in ["burnout", "risk detect", "burnout risk", "employee risk", "stress"]):
            results = detect_burnout_risk()
            analysis_context = f"🔥 BURNOUT RISK ASSESSMENT:\n{json.dumps(results, indent=2)}"

        elif any(kw in q for kw in ["performance summary", "performance review", "write review", "narrate performance", "performance narrator"]):
            from ai_assistant.hr_query_tools import _extract_name
            name = _extract_name(q, ["performance", "summary", "review", "write", "narrate", "narrator", "for", "of", "generate"])
            if name:
                analysis_context = narrate_performance(name)
            else:
                analysis_context = narrate_performance("")

        elif any(kw in q for kw in ["classify complaint", "complaint analysis", "complaint category", "analyze complaint"]):
            result = classify_complaint(user_message)
            analysis_context = f"📋 COMPLAINT CLASSIFICATION:\n{json.dumps(result, indent=2)}"

        elif any(kw in q for kw in ["org health", "organization health", "company health", "workforce health", "health dashboard"]):
            result = generate_org_health()
            analysis_context = f"🏢 ORGANIZATION HEALTH REPORT:\n{json.dumps(result, indent=2)}"

        elif any(kw in q for kw in ["suggest action", "recommend action", "what should i do", "hr action", "action plan"]):
            result = suggest_actions(user_message)
            analysis_context = f"⚡ RECOMMENDED ACTIONS:\n{json.dumps(result, indent=2)}"

    except Exception:
        pass

    # FAQ context
    faq_context = ""
    try:
        from helpdesk.rag_faq import retrieve_faq_chunks
        chunks = retrieve_faq_chunks(user_message, k=3)
        if chunks:
            faq_context = "\n".join(
                f"Q: {c.question}\nA: {c.answer_chunk}" for c in chunks
            )
    except Exception:
        pass

    # Combine all context
    live_sections = []
    if db_context:
        live_sections.append(f"## 📊 Live Database Data\n{db_context}")
    if analysis_context:
        live_sections.append(f"## 🧠 AI Analysis Results\n{analysis_context}")
    live_data_section = "\n\n".join(live_sections)

    faq_section = f"## 📖 FAQ Knowledge\n{faq_context}" if faq_context else ""

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        user_name=user_name,
        user_role=user_role,
        hr_policies=HR_POLICIES,
        live_data_section=live_data_section,
        faq_section=faq_section,
    )

    messages_list = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        role = "user" if h.get("role") == "user" else "assistant"
        content = h.get("content", "")
        if content:
            messages_list.append({"role": role, "content": content})
    messages_list.append({"role": "user", "content": user_message})

    from helpdesk.ai_service import chat
    reply = chat(messages_list)
    return JsonResponse({"reply": reply})


@login_required
@require_http_methods(["POST"])
def ai_analyze_api(request):
    """Direct API for running specific analyzers."""
    try:
        data = json.loads(request.body)
        action = data.get("action", "")
        text = data.get("text", "")
        employee_name = data.get("employee", "")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        from ai_assistant.ai_analyzers import (
            analyze_sentiment, detect_burnout_risk,
            generate_org_health, narrate_performance,
            classify_complaint, suggest_actions,
        )

        if action == "sentiment":
            result = analyze_sentiment(text)
        elif action == "burnout":
            result = detect_burnout_risk()
        elif action == "org_health":
            result = generate_org_health()
        elif action == "performance":
            result = narrate_performance(employee_name)
        elif action == "complaint":
            result = classify_complaint(text)
        elif action == "actions":
            result = suggest_actions(text)
        else:
            return JsonResponse({"error": f"Unknown action: {action}"}, status=400)

        return JsonResponse({"result": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def ai_org_health_api(request):
    """API to get organization health data for the dashboard."""
    try:
        from ai_assistant.ai_analyzers import generate_org_health
        result = generate_org_health()
        return JsonResponse({"result": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
