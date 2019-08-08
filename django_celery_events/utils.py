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

