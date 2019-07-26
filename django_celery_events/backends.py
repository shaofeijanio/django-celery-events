from abc import ABC

from celery_events.backends import Backend
from celery_events.events import Event, Task

from django.apps import apps
from django.db import transaction
from django.db.models import Q
from django_bulk_update.helper import bulk_update


class BaseDjangoBackend(Backend, ABC):

    def get_local_namespaces(self):
        return apps.all_models.keys()

    def get_task_namespace(self, task):
        return task.name.split('.')[0]


class DjangoDBBackend(BaseDjangoBackend):

    def _convert_backend_events_to_events(self, backend_events):
        events = []
        for backend_event in backend_events:
            event = Event(backend_event.app_name, backend_event.event_name)
            event.backend_obj = backend_event

            for backend_task in backend_event.tasks.all():
                task = Task(backend_task.name, queue=backend_task.queue)
                task.backend_obj = backend_task

                event.add_task(task)

            events.append(event)

        return events

    def _create_events(self, events):
        from django_celery_events import models, utils

        backend_events = utils.bulk_create_with_ids([
            models.Event(app_name=event.app_name, event_name=event.event_name)
            for event in events
        ])
        for event, backend_event in zip(events, backend_events):
            event.backend_obj = backend_event

    def _create_tasks(self, tasks):
        from django_celery_events import models, utils

        backend_tasks = utils.bulk_create_with_ids([
            models.Task(name=task.name, queue=task.queue)
            for task in tasks
        ])
        for task, backend_task in zip(tasks, backend_tasks):
            task.backend_obj = backend_task

    def _add_tasks_to_event(self, event, tasks):
        from django_celery_events import models, utils

        backend_event = models.Event(pk=event.backend_obj.pk)
        backend_tasks = [models.Task(pk=task.backend_obj.pk) for task in tasks]
        backend_event.tasks.add(*backend_tasks)

    def commit_changes(self, events_to_create=None, events_to_delete=None, events_to_update=None):
        with transaction.atomic():
            super().commit_changes(
                events_to_create=events_to_create,
                events_to_delete=events_to_delete,
                events_to_update=events_to_update
            )

    def fetch_events_for_namespaces(self, namespaces):
        from django_celery_events import models

        return self._convert_backend_events_to_events(
            models.Event.objects.filter(app_name__in=namespaces).prefetch_related('tasks')
        )

    def fetch_events(self, events):
        from django_celery_events import models

        if len(events) > 0:
            qs = [Q(app_name=event.app_name, event_name=event.event_name) for event in events]
            ored_qs = None
            for q in qs:
                if ored_qs is None:
                    ored_qs = q
                else:
                    ored_qs |= q

            return self._convert_backend_events_to_events(
                models.Event.objects.filter(ored_qs).prefetch_related('tasks')
            )
        else:
            return []

    def delete_events(self, events):
        from django_celery_events import models

        backend_event_pks = [event.backend_obj.pk for event in events]
        models.Event.objects.filter(pk__in=backend_event_pks).delete()

    def create_events(self, events):
        self._create_events(events)
        tasks = [task for event in events for task in event.tasks]
        self._create_tasks(tasks)
        for event in events:
            self._add_tasks_to_event(event, event.tasks)

    def create_tasks(self, event, tasks):
        self._create_tasks(tasks)
        self._add_tasks_to_event(event, tasks)

    def remove_tasks(self, event, tasks):
        from django_celery_events import models

        backend_event = models.Event(pk=event.backend_obj.pk)
        backend_tasks = [models.Task(pk=task.backend_obj.pk) for task in tasks]
        backend_event.tasks.remove(*backend_tasks)

    def update_tasks(self, tasks):
        from django_celery_events import models

        backend_tasks = [models.Task(pk=task.backend_obj.pk, queue=task.queue) for task in tasks]
        bulk_update(backend_tasks, update_fields=['queue'])