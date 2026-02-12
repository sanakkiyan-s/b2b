import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "b2b_course_platform.settings")

app = Celery("b2b_course_platform")

# Load config from settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto discover tasks.py
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'print-every-minute': {
        'task': 'accounts.tasks.print_every_minute',
        'schedule': crontab(minute='*'),
        'options': {'queue': 'default_queue'},
    },
}
