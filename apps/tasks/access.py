from django.db.models import Q
from apps.projects.models import Project


def task_projects(user):
    """Customers receive project summaries, not internal task management."""
    if user.is_superuser:
        return Project.objects.all()
    return Project.objects.filter(
        Q(u_creator=user) | Q(members__user=user, members__role__in=['owner', 'member'])
    ).distinct()
