import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_post.settings")

app = Celery("blog_post")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


app.conf.beat_schedule = {
    "run-score-calculation-every-1-minute": {
        "task": "run_all_score_calculation",
        "schedule": 30.0,
    },
}
