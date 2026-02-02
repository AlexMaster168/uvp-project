"""User models."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class GroupUsers(models.Model):
    """User groups for system roles."""
    
    GROUP_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('guest', 'Guest'),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=GROUP_CHOICES,
        unique=True,
        verbose_name='Название группы'
    )
    
    class Meta:
        verbose_name = 'Группа пользователей'
        verbose_name_plural = 'Группы пользователей'
        db_table = 'group_users'
    
    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    """Custom User model."""
    
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('blocked', 'Заблокирован'),
        ('pending', 'Ожидает подтверждения'),
    ]
    
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    u_group = models.ForeignKey(
        GroupUsers,
        on_delete=models.PROTECT,
        related_name='users',
        verbose_name='Группа',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users'
        ordering = ['username']
    
    def __str__(self):
        return self.username
    
    def is_super_admin(self):
        """Check if user is super admin."""
        return self.is_superuser or (self.u_group and self.u_group.name == 'admin' and self.is_staff)
    
    def is_admin(self):
        """Check if user is admin."""
        return self.u_group and self.u_group.name == 'admin'
    
    def is_manager(self):
        """Check if user is manager."""
        return self.u_group and self.u_group.name == 'manager'
    
    def is_guest(self):
        """Check if user is guest."""
        return self.u_group and self.u_group.name == 'guest'
    
    def block(self):
        """Block user account."""
        self.status = 'blocked'
        self.is_active = False
        self.save()
    
    def unblock(self):
        """Unblock user account."""
        self.status = 'active'
        self.is_active = True
        self.save()
