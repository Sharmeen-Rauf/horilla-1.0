"""
WSGI config for horilla project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import shutil

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")

if os.environ.get("VERCEL"):
    db_path = "/tmp/db.sqlite3"
    source_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite3")
    # Copy the pre-seeded DB on first cold start
    if os.path.exists(source_db) and not os.path.exists(db_path):
        shutil.copy2(source_db, db_path)
    # Always run migrations to ensure all tables exist
    import django
    django.setup()
    from django.core.management import call_command
    try:
        call_command("migrate", "--run-syncdb", verbosity=0)
    except Exception:
        pass

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
