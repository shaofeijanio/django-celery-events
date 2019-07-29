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

```python
from django_celery_events import app

from my_app.tasks import task_1, task_2, task_3


# Declare events
LOCAL_EVENT = app.registry.create_local_event('my_app', 'local_event')
REMOTE_EVENT = app.registry.remote_event('another_app', 'remote_event')

# Add tasks to events
LOCAL_EVENT.add_c_task(task_1)
LOCAL_EVENT.add_c_task(task_2)
REMOTE_EVENT.add_c_task(task_3)
```

## Configurations

The follow variables can be set in `settings.py` to configure `celery-events` behaviour.

**`EVENTS_BROADCAST_QUEUE`**:

The queue for the broadcast task. Broadcast task is the task that trigger tasks registered for every event. Defaults to
"events_broadcast" if not set.

**`EVENTS_BACKEND`**:

The path to the backend class for the events backend. If not set, no backend is used and application can only process
local events and tasks. Set to `"django_celery_events.backends.DjangoDBBackend"` to used the backend provided by
`django-celery-events`.

## Routing of tasks

By default, tasks registered to events are routed to queues using the routes specified in the `CELERY_TASK_ROUTES`
variable in `settings.py`. If a custom queue is required for a task, specify is when adding the task to event.

```python
EVENT.add_c_task(task, queue='my_custom_queue')
```

