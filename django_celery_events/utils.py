import importlib

from django.conf import settings


def bulk_create_with_ids(objs):
    if len(objs) > 0:
        model = objs[0]._meta.model
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            objs = model.objects.bulk_create(objs)
        else:
            for obj in objs:
                obj.save()

    return objs


def get_task_name_queue(task_name):
    task_routes = getattr(settings, 'CELERY_TASK_ROUTES', None)
    if task_routes:
        for route_func_name in task_routes:
            route_name = '.'.join(route_func_name.split('.')[:-1])
            func_name = route_func_name.split('.')[-1]
            route = importlib.import_module(route_name)
            route_func = getattr(route, func_name)

            class DummyTask:
                def __init__(self, name):
                    self.name = name

            r = route_func(name=None, args=None, kwargs=None, options=None, task=DummyTask(task_name))
            if isinstance(r, dict) and 'queue' in r:
                return r.get('queue')

    return None


def get_broadcast_queue():
    queue = getattr(settings, 'EVENTS_BROADCAST_QUEUE', None)
    return queue if queue else 'events_broadcast'


def get_backend_class():
    backend_class_path = getattr(
        settings,
        'EVENTS_BACKEND',
        None,
    )

    if not backend_class_path:
        return None

    backend_class_path_tokens = backend_class_path.split('.')
    backend_module = importlib.import_module('.'.join(backend_class_path_tokens[:-1]))
    backend_class = getattr(backend_module, backend_class_path_tokens[-1])

    return backend_class
