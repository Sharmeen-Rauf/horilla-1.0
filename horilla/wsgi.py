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
    
    print(f"DEBUG: VERCEL detected. source_db: {source_db}, db_path: {db_path}")
    
    if os.path.exists(source_db):
        if not os.path.exists(db_path):
            try:
                shutil.copy2(source_db, db_path)
                print(f"DEBUG: Copied {source_db} to {db_path}")
            except Exception as e:
                print(f"ERROR: Failed to copy DB: {e}")
        else:
            print(f"DEBUG: {db_path} already exists.")
    else:
        print(f"WARNING: {source_db} not found!")

    # Always ensure django is setup and migrations are run
    import django
    django.setup()
    from django.core.management import call_command
    try:
        print("DEBUG: Running migrations...")
        # Use migrate --noinput to avoid hanging, and removed --run-syncdb for standard apps
        call_command("migrate", "--noinput")
        print("DEBUG: Migrations finished.")
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        # Fallback if standard migrate fails (e.g. for dynamic apps)
        try:
            print("DEBUG: Attempting migrate --run-syncdb...")
            call_command("migrate", "--run-syncdb", "--noinput")
            print("DEBUG: migrate --run-syncdb finished.")
        except Exception as e2:
            print(f"ERROR: Fallback migration failed: {e2}")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
