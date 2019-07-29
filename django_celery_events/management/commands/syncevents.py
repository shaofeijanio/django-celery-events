from django.core.management import BaseCommand

from django_celery_events import registry, utils


class Command(BaseCommand):
    help = 'Syncs events with backend.'

    def handle(self, *args, **options):
        backend_class = utils.get_backend_class()

        if backend_class is None:
            self.stdout.write(self.style.NOTICE('Not backend class specified. Nothing is done.'))

        else:
            backend = backend_class(registry)
            backend.sync_local_events()
            backend.sync_remote_events()
            self.stdout.write(self.style.SUCCESS('Events synced!'))
