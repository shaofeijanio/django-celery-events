from django.db import models


class Task(models.Model):
    name = models.CharField(max_length=255)
    queue = models.CharField(max_length=255, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name + ((' - ' + self.queue) if self.queue else '')


class Event(models.Model):
    app_name = models.CharField(max_length=255)
    event_name = models.CharField(max_length=255)
    tasks = models.ManyToManyField(Task, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.app_name + ' - ' + self.event_name
