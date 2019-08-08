import importlib

from django.conf import settings


def get_routes():
    route_names = getattr(settings, 'CELERY_TASK_ROUTES', None)
    routes = []
    if route_names:
        for route_func_name in route_names:
            module_name = '.'.join(route_func_name.split('.')[:-1])
            func_name = route_func_name.split('.')[-1]
            module = importlib.import_module(module_name)
            route = getattr(module, func_name)
            routes.append(route)

    return routes


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
