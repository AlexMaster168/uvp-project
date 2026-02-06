"""Access models."""

from django.db import models


class Access(models.Model):
    """Access credentials model."""
    
    TAGS_CHOICES = [
        ('critical', 'Критичный'),
        ('info', 'Информационный'),
        ('provider', 'Провайдер'),
        ('hosting', 'Хостинг'),
    ]
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='accesses',
        verbose_name='Проект'
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='URL'
    )
    url_drive = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='URL диска'
    )
    login = models.CharField(
        max_length=255,
        verbose_name='Логин'
    )
    password = models.CharField(
        max_length=255,
        verbose_name='Пароль'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    registration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата регистрации'
    )
    update_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата обновления'
    )
    change_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к изменению'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Теги'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Доступ'
        verbose_name_plural = 'Доступы'
        db_table = 'access'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.login} - {self.url or 'N/A'}"
