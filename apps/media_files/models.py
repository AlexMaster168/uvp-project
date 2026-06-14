"""Media files models."""

from django.db import models
from apps.utils import translit_upload_to


class MediaFile(models.Model):
    """Media file model."""
    
    file = models.FileField(
        upload_to=translit_upload_to('project_media'),
        verbose_name='Файл'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Загружено'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name='Проект'
    )
    
    class Meta:
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
        db_table = 'media_files'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file.name} ({self.project.name})"
    
    @property
    def filename(self):
        return self.file.name.split('/')[-1]
    
    @property
    def is_image(self):
        ext = self.filename.split('.')[-1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    @property
    def is_video(self):
        ext = self.filename.split('.')[-1].lower()
        return ext in ['mp4', 'avi', 'mov', 'webm']
    
    @property
    def is_pdf(self):
        return self.filename.lower().endswith('.pdf')
