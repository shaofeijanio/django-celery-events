import importlib

from django.conf import settings


def _import_class(path):
    path_tokens = path.split('.')
    module = importlib.import_module('.'.join(path_tokens[:-1]))
    cls = getattr(module, path_tokens[-1])
    return cls


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


def get_broadcast_task_base():
    broadcast_task_base_path = getattr(settings, 'EVENTS_BROADCAST_TASK_BASE', None)
    if broadcast_task_base_path:
        return _import_class(broadcast_task_base_path)

    return None


def get_backend_class():
    backend_class_path = getattr(settings, 'EVENTS_BACKEND', None)
    if backend_class_path:
        return _import_class(backend_class_path)

    return None
