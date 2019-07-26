from celery_events import create_app

from django_celery_events import utils

default_app_config = 'django_celery_events.apps.DjangoCeleryEventsConfig'

app = create_app(
    backend_class=utils.get_backend_class(),
    get_broadcast_queue=utils.get_broadcast_queue,
    get_task_name_queue=utils.get_task_name_queue
)

registry = app.registry
