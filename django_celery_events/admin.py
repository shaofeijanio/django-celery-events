from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from django_celery_events import models


def linkify(obj, display_obj=lambda o: str(o)):
    if obj is None:
        return '-'
    link = reverse(
        'admin:{0}_{1}_change'.format(
            obj._meta.app_label,
            obj._meta.model_name
        ),
        args=[obj.pk]
    )
    return format_html('<a href="{0}">{1}</a>'.format(link, display_obj(obj)))


def as_html_list(lines):
    if len(lines) > 0:
        value = '<p>'
        for line in lines:
            value += line + '<br>'
        return format_html(value + '</p>')
    else:
        return '-'


class EventAdmin(ModelAdmin):
    list_display = (
        'id',
        'app_name',
        'event_name',
        'task_list',
        'updated_on',
        'created_on'
    )

    def task_list(self, obj):
        tasks = sorted(obj.tasks.all(), key=lambda t: t.name)
        return as_html_list([linkify(task) for task in tasks])

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tasks').order_by('app_name', 'event_name')


class TaskAdmin(ModelAdmin):
    list_display = (
        'name',
        'queue'
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('name')


admin.site.register(models.Event, EventAdmin)
admin.site.register(models.Task, TaskAdmin)
