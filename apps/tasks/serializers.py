from rest_framework import serializers
from .models import Task, SubTask
from apps.projects.serializers import TagSerializer
from apps.users.serializers import UserSerializer


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assignees = UserSerializer(source='u_users', many=True, read_only=True)
    tags = TagSerializer(source='u_tags', many=True, read_only=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'estimated_time', 'actual_time', 'project', 'u_users', 'u_tags']
        read_only_fields = ['id']
