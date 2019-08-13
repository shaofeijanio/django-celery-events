from celery_events import App
from celery_events.app import Registry

from django_celery_events import configs

default_app_config = 'django_celery_events.apps.DjangoCeleryEventsConfig'

app: App = None
registry: Registry = None
