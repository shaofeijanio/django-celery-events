import importlib

from celery import Task
from celery_events.events import Event

from django.apps import AppConfig
from django.conf import settings


class DjangoCeleryEventsConfig(AppConfig):
    name = 'django_celery_events'

    def ready(self):
        app_module_list = []
        events = []

        # Import events
        for app in settings.INSTALLED_APPS:
            try:
                if not app == 'django_celery_events':
                    module = importlib.import_module(app + '.events')
                    app_module_list.append((app, module))
                    for o in module.__dict__.values():
                        if isinstance(o, Event):
                            events.append(o)

                    print('Imported events from {0}.'.format(app))

            except ModuleNotFoundError:
                pass

        # Add tasks to events
        for app, module in app_module_list:
            if hasattr(module, 'get_event_c_tasks'):
                for event in events:
                    c_tasks = module.get_event_c_tasks(event)
                    for c_task in c_tasks:
                        if not isinstance(c_task, Task):
                            raise ValueError('{0} is not a celery task.'.format(c_task))

                        event.add_local_c_task(c_task)

                print('Added tasks from {0}.'.format(app))
