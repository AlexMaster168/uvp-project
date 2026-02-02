"""Billing models."""

from django.db import models
from django.conf import settings


class Billing(models.Model):
    """Billing entry model."""
    
    TAG_CHOICES = [
        ('planned_expense', 'Планируемый расход'),
        ('approved_expense', 'Утверждённый расход'),
        ('expected_income', 'Ожидаемый доход'),
        ('actual_income', 'Фактический доход'),
    ]
    
    OPERATION_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='billings',
        verbose_name='Проект'
    )
    date = models.DateField(
        verbose_name='Дата'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Сумма'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    tag = models.CharField(
        max_length=50,
        choices=TAG_CHOICES,
        verbose_name='Тег'
    )
    operation = models.CharField(
        max_length=20,
        choices=OPERATION_CHOICES,
        verbose_name='Операция'
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='billing_entries',
        blank=True,
        verbose_name='Участники'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Финансовая запись'
        verbose_name_plural = 'Финансовые записи'
        db_table = 'billing'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_operation_display()}: {self.amount} ({self.date})"
