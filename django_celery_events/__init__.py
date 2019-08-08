from celery_events import App

from django_celery_events import configs

default_app_config = 'django_celery_events.apps.DjangoCeleryEventsConfig'

app = App(
    backend_class=configs.get_backend_class(),
    broadcast_queue=configs.get_broadcast_queue(),
    routes=configs.get_routes()
)

registry = app.registry
