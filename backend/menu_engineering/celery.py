import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "menu_engineering.settings")

app = Celery("menu_engineering")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
