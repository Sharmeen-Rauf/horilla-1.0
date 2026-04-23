import os
import django

# Setup django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command

# The order specified in base/views.py load_demo_database plus all files in load_data
files = [
    "user_data.json",
    "employee_info_data.json",
    "base_data.json",
    "work_info_data.json",
    "attendance_data.json",
    "leave_data.json",
    "asset_data.json",
    "recruitment_data.json",
    "onboarding_data.json",
    "offboarding_data.json",
    "pms_data.json",
    "payroll_data.json",
    "payroll_loanaccount_data.json",
    "project_data.json",
    "tags.json",
    "faq_category.json",
    "faq.json",
    "mail_templates.json",
    "mail_automations.json"
]

for f in files:
    try:
        target = os.path.join('load_data', f)
        if os.path.exists(target):
            call_command('loaddata', target)
            print(f"Successfully loaded {f}")
        else:
            print(f"File not found: {target}")
    except Exception as e:
        print(f"Error loading {f}: {e}")
