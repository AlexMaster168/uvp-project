"""Read-only management reports using existing task estimates (eight-hour days)."""
from collections import defaultdict
from django.utils import timezone


def management_report(project, tasks=None):
    if tasks is None:
        tasks = project.tasks.prefetch_related('subtasks', 'u_users').order_by('created_at', 'pk')
    rows, workload = [], defaultdict(float)
    unassigned = 0
    for task in tasks:
        subtasks = list(task.subtasks.all())
        completed = len(subtasks) if task.status == 'done' else sum(sub.status == 'done' for sub in subtasks)
        progress = 100 if task.status == 'done' else (int(completed * 100 / len(subtasks)) if subtasks else 0)
        remaining = 0 if task.status == 'done' else max(task.estimated_time - task.actual_time, 0)
        risk = task.status != 'done' and task.estimated_time > 0 and task.actual_time >= task.estimated_time
        people = list(task.u_users.all())
        if people:
            for person in people:
                workload[person.username] += remaining / len(people) / 8
        else:
            unassigned += remaining / 8
        rows.append({
            'task': task, 'people': people, 'progress': progress,
            'segments': (progress * 4 + 50) // 100,
            'remaining_days': remaining / 8, 'risk': risk,
            'planned_days': max(task.estimated_time, 0) / 8,
            'spent_days': max(task.actual_time, 0) / 8,
            'done': completed if subtasks else int(task.status == 'done'),
            'pending': len(subtasks) - completed if subtasks else int(task.status != 'done'),
            'unestimated': task.status != 'done' and task.estimated_time <= 0,
        })
    done = sum(row['done'] for row in rows)
    pending = sum(row['pending'] for row in rows)
    total_units = done + pending
    progress = int(done * 100 / total_units) if total_units else 0
    deadline_days = (project.end_date - timezone.localdate()).days if project.end_date else None
    return {
        'rows': rows, 'progress': progress, 'segments': (progress * 4 + 50) // 100,
        'remaining_days': sum(r['remaining_days'] for r in rows),
        'planned_days': sum(r['planned_days'] for r in rows),
        'spent_days': sum(r['spent_days'] for r in rows),
        'done': done, 'risks': sum(r['risk'] for r in rows),
        'pending': pending,
        'unestimated': sum(r['unestimated'] for r in rows),
        'deadline_days': deadline_days, 'overdue_days': abs(deadline_days) if deadline_days is not None and deadline_days < 0 else 0,
        'workload': sorted(workload.items(), key=lambda item: (-item[1], item[0])),
        'unassigned_days': unassigned,
    }
