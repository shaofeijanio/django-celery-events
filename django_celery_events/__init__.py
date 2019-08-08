from celery_events import App

from django_celery_events import configs

default_app_config = 'django_celery_events.apps.DjangoCeleryEventsConfig'

app = None
registry = None
