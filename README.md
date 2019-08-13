## Installation

```shell script
pip install git+https://github.com/shaofeijanio/django-celery-events.git@master#egg=django-celery-events
```

Note that [celery-events](https://github.com/shaofeijanio/celery-events) is a dependency and should be installed 
separately.

Add `"django-celery-events"` to `INSTALLED_APPS` in `settings.py`.

Run migration.

## Usage
Usage of `celery-events` functionality is the same as before. The difference is that the `celery-events` application
object is already setup by `django-celery-events`. In addition, events should be declared in the `events.py` file of
application.

For example, for an Django application `my_app`, the following code should go into `my_app/events.py`.

**Declaring events**

```python
from django_celery_events import app

LOCAL_EVENT = app.registry.create_local_event('my_app', 'local_event')
```

**Adding task to events**

Adding of tasks can be done in the standard way by importing the events and calling `.add_local_c_task()` of the event.
However, this will result in error if there is circular import in the project. The recommended way is to provide a
`get_event_c_tasks()` method in `events.py` to return the celery tasks for each event.

```python
from my_app import tasks

LOCAL_EVENT = app.registry.create_local_event('my_app', 'local_event')


def get_event_c_tasks(event):
    # Import is done inside method to prevent circular import
    from another_app import events as another_app_events
    
    # Return tasks for each event
    if event == LOCAL_EVENT:
        return [tasks.task_1, tasks.task_2]

    if event == another_app_events.LOCAL_EVENT:
        return [tasks.task_3, tasks.task_4]
```

## Configurations

The follow variables can be set in `settings.py` to configure `celery-events` behaviour.

**`EVENTS_BROADCAST_QUEUE`**:

The queue for the broadcast task. Broadcast task is the task that trigger tasks registered for every event. Defaults to
`"events_broadcast"` if not set.

**`EVENTS_BACKEND`**:

The path to the backend class for the events backend. If not set, no backend is used and application can only process
local events and tasks. Set to `"django_celery_events.backends.DjangoDBBackend"` to used the backend provided by
`django-celery-events`.

## Syncing of events
If cross-application support is required (`EVENTS_BACKEND` is set), events need to be synced with the backend when
events and tasks change. This operation is similar to migrations in django. If events are not synced, remote
applications do not know about the local tasks added to their events and the current application also does not know
about the remote tasks added to the local events. To sync events use the below django admin command.

```shell script
python manage.py syncevents
```

## Routing of tasks

By default, tasks registered to events are routed to queues using the routes specified in the `CELERY_TASK_ROUTES`
variable in `settings.py`. If a custom queue is required for a task, specify is when adding the task to event.

```python
EVENT.add_local_c_task(task, queue='my_custom_queue')
```

