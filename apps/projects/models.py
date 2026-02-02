"""Project models."""

from django.db import models
from django.conf import settings


class Tag(models.Model):
    """Tags for projects and tasks."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название'
    )
    range = models.IntegerField(
        default=0,
        verbose_name='Диапазон'
    )
    importance = models.IntegerField(
        default=0,
        verbose_name='Важность'
    )
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        db_table = 'tags'
        ordering = ['-importance', 'name']
    
    def __str__(self):
        return self.name


class Project(models.Model):
    """Project model."""
    
    STATUS_CHOICES = [
        ('planned', 'Запланирован'),
        ('in_progress', 'В работе'),
        ('idle', 'Простой'),
        ('sleep', 'Заморожен'),
        ('my', 'Мой'),
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата начала'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name='Статус'
    )
    logo = models.ImageField(
        upload_to='project_logos/',
        null=True,
        blank=True,
        verbose_name='Логотип'
    )
    u_creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_projects',
        verbose_name='Создатель'
    )
    u_tags = models.ManyToManyField(
        Tag,
        related_name='projects',
        blank=True,
        verbose_name='Теги'
    )
    
    # For Rete.js structure
    structure_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Структура проекта (JSON)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        db_table = 'projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (#{self.id})"
    
    @property
    def duration_days(self):
        """Calculate project duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    def get_owners(self):
        """Get project owners."""
        return self.members.filter(role='owner')
    
    def get_tasks_count(self):
        """Get total tasks count."""
        return self.tasks.count()
    
    def get_financial_summary(self):
        """Calculate financial summary."""
        from apps.billing.models import Billing
        
        billings = Billing.objects.filter(project=self)
        income = billings.filter(operation='income').aggregate(
            total=models.Sum('amount'))['total'] or 0
        expense = billings.filter(operation='expense').aggregate(
            total=models.Sum('amount'))['total'] or 0
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense
        }


class ProjectMembership(models.Model):
    """Project membership with roles."""
    
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
        ('member', 'Участник'),
        ('viewer', 'Наблюдатель'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Проект'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name='Пользователь'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name='Роль'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Участие в проекте'
        verbose_name_plural = 'Участия в проектах'
        db_table = 'project_membership'
        unique_together = ['project', 'user']
        ordering = ['project', '-role']
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"


class Plan(models.Model):
    """Project plan items."""
    
    u_project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='plan_items',
        verbose_name='Проект'
    )
    u_task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='plan_items',
        verbose_name='Задача'
    )
    order_index = models.IntegerField(
        default=0,
        verbose_name='Порядок'
    )
    
    class Meta:
        verbose_name = 'Элемент плана'
        verbose_name_plural = 'Элементы плана'
        db_table = 'plan'
        ordering = ['u_project', 'order_index']
    
    def __str__(self):
        return f"План: {self.u_project.name} - {self.u_task.title}"
