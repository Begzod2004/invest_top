import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Use Redis as broker in production
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'memory://')
