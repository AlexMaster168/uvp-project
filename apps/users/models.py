from django.contrib.auth.models import AbstractUser
from django.db import models


class GroupUsers(models.Model):
    GROUP_CHOICES = [
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    ]
    name = models.CharField(max_length=50, choices=GROUP_CHOICES, unique=True)

    class Meta:
        db_table = 'group_users'


class User(AbstractUser):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('blocked', 'Заблокирован'),
        ('pending', 'Ожидает подтверждения'),
    ]
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    u_group = models.ForeignKey(GroupUsers, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    global_x = models.FloatField(default=0)
    global_y = models.FloatField(default=0)

    class Meta:
        db_table = 'users'
        ordering = ['username']

    def is_super_admin(self):
        return self.is_superuser or (self.u_group and self.u_group.name == 'admin' and self.is_staff)

    def is_admin(self):
        return self.u_group and self.u_group.name == 'admin'

    def is_guest(self):
        return self.u_group and self.u_group.name == 'guest'

    def block(self):
        self.status = 'blocked'
        self.is_active = False
        self.save()

    def unblock(self):
        self.status = 'active'
        self.is_active = True
        self.save()


class GlobalSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Light (Светлая)'),
        ('bg-gradient-1', 'Ocean Blue'),
        ('bg-gradient-2', 'Sunset Orange'),
        ('bg-gradient-3', 'Purple Dream'),
        ('bg-gradient-4', 'Forest Green'),
        ('bg-gradient-5', 'Night Sky'),
        ('bg-gradient-6', 'Cherry Blossom'),
        ('bg-gradient-7', 'Cosmic Fusion'),
        ('bg-gradient-8', 'Deep Sea'),
        ('bg-gradient-9', 'Tropical Sunrise'),
        ('bg-gradient-10', 'Arctic Frost'),
        ('bg-gradient-11', 'Neon Lights'),
        ('bg-gradient-12', 'Golden Hour'),
    ]
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('uk', 'Українська'),
        ('en', 'English'),
    ]
    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='light')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='ru')

    class Meta:
        db_table = 'global_settings'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
