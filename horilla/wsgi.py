"""
WSGI config for horilla project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import shutil

if os.environ.get("VERCEL"):
    db_path = "/tmp/db.sqlite3"
    source_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite3")
    if os.path.exists(source_db) and not os.path.exists(db_path):
        shutil.copy2(source_db, db_path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")

application = get_wsgi_application()
app = application
