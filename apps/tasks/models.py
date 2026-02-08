from django.db import models
from django.conf import settings


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
    ]

    title = models.CharField(max_length=255, verbose_name='Название')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Статус')
    description = models.TextField(blank=True, verbose_name='Описание')
    estimated_time = models.FloatField(default=0, verbose_name='Планируемое время (ч)')
    actual_time = models.FloatField(default=0, verbose_name='Фактическое время (ч)')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks',
                                verbose_name='Проект')
    u_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_tasks', blank=True,
                                     verbose_name='Исполнители')
    u_tags = models.ManyToManyField('projects.Tag', related_name='tasks', blank=True, verbose_name='Теги')
    previous_tasks = models.ManyToManyField('self', symmetrical=False, related_name='next_tasks', blank=True,
                                            verbose_name='Предыдущие задачи')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        db_table = 'tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (#{self.id})"


class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks',
                             verbose_name='Родительская задача', null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name='Название')
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='todo', verbose_name='Статус')
    u_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_subtasks', blank=True,
                                     verbose_name='Исполнители')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Подзадача'
        verbose_name_plural = 'Подзадачи'
        db_table = 'subtasks'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.title} (Sub of #{self.task.id if self.task else 'None'})"
