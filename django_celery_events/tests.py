from unittest import mock

from celery_events.events import Event, Task

from django.test import TestCase
from django_celery_events.backends import DjangoDBBackend
from django_celery_events import models, utils, registry


class DjangoDBBackendTestCase(TestCase):

    def tearDown(self):
        registry.events = []

    def test_fetch_events_for_namespaces(self):
        event_objs = [
            models.Event.objects.create(app_name='app_1', event_name='event'),
            models.Event.objects.create(app_name='app_3', event_name='event')
        ]
        task_obj = models.Task.objects.create(name='task_1', queue='queue_1')
        event_objs[0].tasks.add(task_obj)

        backend = DjangoDBBackend(registry)
        events = backend.fetch_events_for_namespaces(['app_1', 'app_2'])

        self.assertEqual(1, len(events))
        event_obj, event = event_objs[0], events[0]
        self.assertEqual(event_obj.app_name, event.app_name)
        self.assertEqual(event_obj.event_name, event.event_name)
        self.assertEqual(event_obj, event.backend_obj)
        self.assertEqual(1, len(event.tasks))
        task = event.tasks[0]
        self.assertEqual(task_obj.name, task.name)
        self.assertEqual(task_obj.queue, task.queue)
        self.assertEqual(task_obj, task.backend_obj)

    def test_fetch_events(self):
        event_objs = [
            models.Event.objects.create(app_name='app_1', event_name='event'),
            models.Event.objects.create(app_name='app_3', event_name='event')
        ]
        task_obj = models.Task.objects.create(name='task_1', queue='queue_1')
        event_objs[0].tasks.add(task_obj)

        backend = DjangoDBBackend(registry)
        events = backend.fetch_events([
            Event('app_1', 'event'),
            Event('app_2', 'event')
        ])

        self.assertEqual(1, len(events))
        event_obj, event = event_objs[0], events[0]
        self.assertEqual(event_obj.app_name, event.app_name)
        self.assertEqual(event_obj.event_name, event.event_name)
        self.assertEqual(event_obj, event.backend_obj)
        self.assertEqual(1, len(event.tasks))
        task = event.tasks[0]
        self.assertEqual(task_obj.name, task.name)
        self.assertEqual(task_obj.queue, task.queue)
        self.assertEqual(task_obj, task.backend_obj)

    def test_fetch_events_for_no_events(self):
        backend = DjangoDBBackend(registry)
        events = backend.fetch_events([])
        self.assertEqual(0, len(events))

    def test_should_update_event(self):
        event = registry.create_local_event('app', 'event')
        event_obj = models.Event.objects.create(app_name='app', event_name='event')
        event.backend_obj = event_obj

        event_obj = models.Event.objects.get(app_name='app', event_name='event')
        event_obj.save()

        backend = DjangoDBBackend(registry)
        self.assertEqual(True, backend.should_update_event(event))

    def test_should_update_event_no_backend_obj(self):
        event_obj = models.Event.objects.create(app_name='app', event_name='event')
        event = registry.create_local_event('app', 'event')

        backend = DjangoDBBackend(registry)
        self.assertTrue(backend.should_update_event(event))

    def test_should_update_event_event_not_in_backend(self):
        event = registry.create_local_event('app', 'event')
        event_obj = models.Event.objects.create(app_name='app', event_name='event')
        event.backend_obj = event_obj
        event_obj.delete()

        backend = DjangoDBBackend(registry)
        self.assertFalse(backend.should_update_event(event))

    def test_delete_events(self):
        event_obj = models.Event.objects.create(app_name='app_1', event_name='event')
        task_obj = models.Task.objects.create(name='task_1', queue='queue_1')
        event_obj.tasks.add(task_obj)

        backend = DjangoDBBackend(registry)
        event = Event('app_1', 'event')
        event.backend_obj = event_obj
        backend.delete_events([event])

        self.assertEqual(0, models.Event.objects.all().count())
        self.assertEqual(1, models.Task.objects.all().count())

    def test_create_events(self):
        events = [
            Event('app_1', 'event'),
            Event('app_2', 'event'),
        ]
        tasks = [
            Task('task_1'),
            Task('task_2')
        ]
        for event in events:
            for task in tasks:
                event.add_task(task)

        backend = DjangoDBBackend(registry)
        backend.create_events(events)

        event_objs = models.Event.objects.order_by('app_name')
        self.assertEqual(2, event_objs.count())
        for event_obj, event in zip(event_objs, events):
            self.assertEqual(event_obj.app_name, event.app_name)
            self.assertEqual(event_obj.event_name, event.event_name)
            self.assertEqual(event_obj, event.backend_obj)
            task_objs = event_obj.tasks.all().order_by('name')
            self.assertEqual(2, task_objs.count())
            for task_obj, task in zip(task_objs, tasks):
                self.assertEqual(task_obj.name, task.name)
                self.assertEqual(task_obj.queue, task.queue)
                self.assertEqual(task_obj, task.backend_obj)

        task_objs = models.Task.objects.order_by('name')
        self.assertEqual(4, task_objs.count())

    def test_create_tasks(self):
        event_obj = models.Event.objects.create(app_name='app_1', event_name='event')
        current_task_obj = models.Task.objects.create(name='task_0')
        event_obj.tasks.add(current_task_obj)

        backend = DjangoDBBackend(registry)
        event = Event('app_1', 'event')
        event.backend_obj = event_obj
        tasks = [
            Task('task_1'),
            Task('task_2', queue='queue_2')
        ]
        backend.create_tasks(event, tasks)

        event_objs = models.Event.objects.all()
        self.assertEqual(1, event_objs.count())
        task_objs = event_objs.first().tasks.order_by('name')
        self.assertEqual(3, task_objs.count())
        for task_obj, task in zip(task_objs[1:], tasks):
            self.assertEqual(task_obj.name, task.name)
            self.assertEqual(task_obj.queue, task.queue)
            self.assertEqual(task_obj, task.backend_obj)

    def test_remove_tasks(self):
        event_obj = models.Event.objects.create(app_name='app_1', event_name='event')
        current_task_objs = [
            models.Task.objects.create(name='task_1'),
            models.Task.objects.create(name='task_2')
        ]
        event_obj.tasks.set(current_task_objs)

        backend = DjangoDBBackend(registry)
        event = Event('app_1', 'event')
        event.backend_obj = event_obj
        task = Task('task_1')
        task.backend_obj = current_task_objs[0]
        backend.remove_tasks(event, [task])

        event_objs = models.Event.objects.all()
        self.assertEqual(1, event_objs.count())
        task_objs = event_objs.first().tasks.order_by('name')
        self.assertEqual(1, task_objs.count())
        task_obj, task = task_objs.first(), Task('task_2')
        self.assertEqual(task_obj.name, task.name)
        self.assertEqual(task_obj.queue, task.queue)

    def test_update_tasks(self):
        current_task_objs = [
            models.Task.objects.create(name='task_1'),
            models.Task.objects.create(name='task_2')
        ]

        backend = DjangoDBBackend(registry)
        tasks = [
            Task('task_1', queue='queue_1'),
            Task('task_2', queue='queue_2')
        ]
        for task_obj, task in zip(current_task_objs, tasks):
            task.backend_obj = task_obj
        backend.update_tasks(tasks)

        task_objs = models.Task.objects.all().order_by('name')
        self.assertEqual(2, task_objs.count())
        for task_obj, task in zip(task_objs, tasks):
            self.assertEqual(task_obj.name, task.name)
            self.assertEqual(task_obj.queue, task.queue)

    def test_update_local_event(self):
        event = registry.create_local_event('django_celery_events', 'event')
        task = event.add_task_name('django_celery_events.task_1')
        event_obj = models.Event.objects.create(app_name='django_celery_events', event_name='event')
        remote_task_obj = models.Task.objects.create(name='another_app.task_1', queue='q')
        event_obj.tasks.add(remote_task_obj)

        backend = DjangoDBBackend(registry)
        backend.update_local_event(event)

        self.assertEqual(1, len(registry.local_events))
        local_event = registry.local_events[0]
        self.assertEqual(event, local_event)
        self.assertEqual(2, len(local_event.tasks))

        tasks = sorted(local_event.tasks, key=lambda t: t.name)
        remote_task = tasks[0]
        self.assertEqual(remote_task_obj.name, remote_task.name)
        self.assertEqual(remote_task_obj.queue, remote_task.queue)
        self.assertEqual(remote_task_obj, remote_task.backend_obj)
        local_task = tasks[1]
        self.assertEqual(task, local_task)
        self.assertEqual(0, len(registry.remote_events))

    def test_sync_local_events(self):
        local_event_to_add = registry.create_local_event('django_celery_events', 'event_1')
        local_task_to_add_to_local_event_to_add = local_event_to_add.add_task_name('django_celery_events.task_1')

        local_event_to_remove_obj = models.Event.objects.create(app_name='django_celery_events', event_name='event_2')

        backend = DjangoDBBackend(registry)
        backend.sync_local_events()

        event_objs = models.Event.objects.order_by('event_name')
        self.assertEqual(1, event_objs.count())
        event_obj = event_objs[0]
        self.assertEqual(local_event_to_add.app_name, event_obj.app_name)
        self.assertEqual(local_event_to_add.event_name, event_obj.event_name)
        task_objs = event_obj.tasks.order_by('name')
        self.assertEqual(1, task_objs.count())
        task_obj = task_objs[0]
        self.assertEqual(local_task_to_add_to_local_event_to_add.name, task_obj.name)
        self.assertEqual(local_task_to_add_to_local_event_to_add.queue, task_obj.queue)

    def test_sync_remote_events(self):
        remote_event = registry.remote_event('another_app', 'event')
        local_task_to_add = remote_event.add_task_name('django_celery_events.task_1')
        local_task_to_update = remote_event.add_task_name('django_celery_events.task_2', queue='new_queue')

        remote_event_obj = models.Event.objects.create(app_name='another_app', event_name='event')
        local_task_to_update_obj = models.Task.objects.create(name='django_celery_events.task_2', queue='old_queue')
        local_task_to_remove_obj = models.Task.objects.create(name='django_celery_events.task_3')
        remote_event_obj.tasks.add(local_task_to_update_obj, local_task_to_remove_obj)

        backend = DjangoDBBackend(registry)
        backend.sync_remote_events()

        event_objs = models.Event.objects.all()
        self.assertEqual(1, event_objs.count())
        event_obj = event_objs[0]
        self.assertEqual(remote_event_obj, event_obj)
        task_objs = event_obj.tasks.order_by('name')
        self.assertEqual(2, task_objs.count())
        task_obj = task_objs[0]
        self.assertEqual(local_task_to_add.name, task_obj.name)
        self.assertEqual(local_task_to_add.queue, task_obj.queue)
        task_obj = task_objs[1]
        self.assertEqual(local_task_to_update_obj, task_obj)
        self.assertEqual(local_task_to_update.name, task_obj.name)
        self.assertEqual(local_task_to_update.queue, task_obj.queue)


class GetTaskNameQueueTestCase(TestCase):

    def setUp(self):
        # Mock
        settings_patcher = mock.patch('django_celery_events.utils.settings')
        self.mock_settings = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)
        import_module_patcher = mock.patch('django_celery_events.utils.importlib.import_module')
        self.mock_import_module = import_module_patcher.start()
        self.addCleanup(import_module_patcher.stop)

    def test_with_route_queue(self):
        def route(task, **kwargs):
            return {
                'queue': 'queue_{0}'.format(task.name)
            }

        class RouteModule:
            pass

        RouteModule.route = route

        self.mock_settings.CELERY_TASK_ROUTES = ['app.tasks.route']
        self.mock_import_module.side_effect = lambda name: RouteModule if name == 'app.tasks' else None

        self.assertEqual('queue_task_1', utils.get_task_name_queue('task_1'))

    def test_with_route_no_queue(self):
        def route(task, **kwargs):
            return {'exchange': 'exchange'}

        class RouteModule:
            pass

        RouteModule.route = route

        self.mock_settings.CELERY_TASK_ROUTES = ['app.tasks.route']
        self.mock_import_module.side_effect = lambda name: RouteModule if name == 'app.tasks' else None

        self.assertIsNone(utils.get_task_name_queue('task_1'))

    def test_with_route_return_none(self):
        def route(task, **kwargs):
            return None

        class RouteModule:
            pass

        RouteModule.route = route

        self.mock_settings.CELERY_TASK_ROUTES = ['app.tasks.route']
        self.mock_import_module.side_effect = lambda name: RouteModule if name == 'app.tasks' else None

        self.assertIsNone(utils.get_task_name_queue('task_1'))

    def test_with_no_route(self):
        self.mock_settings.CELERY_TASK_ROUTES = None
        self.assertIsNone(utils.get_task_name_queue('task_1'))


class GetBroadcastQueueTestCase(TestCase):

    def setUp(self):
        # Mock
        settings_patcher = mock.patch('django_celery_events.utils.settings')
        self.mock_settings = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

    def test_with_settings(self):
        self.mock_settings.EVENTS_BROADCAST_QUEUE = 'queue'
        self.assertEqual('queue', utils.get_broadcast_queue())

    def test_with_settings_as_none(self):
        self.mock_settings.EVENTS_BROADCAST_QUEUE = None
        self.assertEqual('events_broadcast', utils.get_broadcast_queue())


class GetBackendClassTestCase(TestCase):

    def setUp(self):
        # Mock
        settings_patcher = mock.patch('django_celery_events.utils.settings')
        self.mock_settings = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

    @mock.patch('django_celery_events.utils.importlib.import_module')
    def test_with_settings(self, mock_import_module):
        self.mock_settings.EVENTS_BACKEND = 'app.backends.TestBackend'

        class BackendModule:
            class TestBackend(DjangoDBBackend):
                pass

        mock_import_module.side_effect = lambda name: BackendModule if name == 'app.backends' else None

        self.assertEqual(BackendModule.TestBackend, utils.get_backend_class())

    def test_with_settings_db_backend_class(self):
        self.mock_settings.EVENTS_BACKEND = 'django_celery_events.backends.DjangoDBBackend'
        self.assertEqual(DjangoDBBackend, utils.get_backend_class())

    def test_with_no_settings(self):
        self.mock_settings.EVENTS_BACKEND = None
        self.assertIsNone(utils.get_backend_class())
