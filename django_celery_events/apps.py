import importlib

from django.apps import AppConfig
from django.conf import settings


class DjangoCeleryEventsConfig(AppConfig):
    name = 'django_celery_events'

    def ready(self):
        # Import all events
        for app in settings.INSTALLED_APPS:
            try:
                if not app == 'django_celery_events':
                    importlib.import_module(app + '.events')
                    print('Imported events from {0}.'.format(app))
            except ModuleNotFoundError:
                pass
