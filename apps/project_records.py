"""Project choices and record permissions for finance and access forms."""
from django.db.models import Q
from django.urls import reverse_lazy
from apps.projects.models import Project


def record_projects(user):
    if user.is_superuser or user.is_admin():
        return Project.objects.all()
    return Project.objects.filter(
        Q(u_creator=user) | Q(members__user=user, members__role='owner')
    ).distinct()


class ProjectRecordMixin:
    def get_success_url(self):
        project = self.object.project
        if project.u_creator_id == self.request.user.pk or project.members.filter(user=self.request.user).exists():
            return reverse_lazy('projects:project_detail', kwargs={'pk': project.pk})
        app = self.model._meta.app_label
        return reverse_lazy(f'{app}:{app}_list')

    def get_queryset(self):
        return super().get_queryset().filter(project__in=record_projects(self.request.user))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'project' in self.get_form_class().base_fields:
            kwargs['user'] = self.request.user
        return kwargs
