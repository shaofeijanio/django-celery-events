import importlib

from django.apps import AppConfig
from django.conf import settings

from celery_events import registry, update_local_events

from django_celery_events import utils


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

        # Set get methods
        registry.set_get_broadcast_queue(utils.get_broadcast_queue)
        registry.set_get_task_name_queue(utils.get_task_name_queue)

        # Sync with remote
        if getattr(settings, 'EVENTS_REQUIRE_BACKEND', False):
            backend_class = utils.get_backend_class()
            update_local_events(backend_class)
