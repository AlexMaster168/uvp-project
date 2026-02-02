"""Task models."""

from django.db import models
from django.conf import settings


class Task(models.Model):
    """Task model."""
    
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        verbose_name='Статус'
    )
    estimated_time = models.FloatField(
        default=0,
        verbose_name='Планируемое время (ч)'
    )
    actual_time = models.FloatField(
        default=0,
        verbose_name='Фактическое время (ч)'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Проект'
    )
    u_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True,
        verbose_name='Исполнители'
    )
    u_tags = models.ManyToManyField(
        'projects.Tag',
        related_name='tasks',
        blank=True,
        verbose_name='Теги'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        db_table = 'tasks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (#{self.id})"
