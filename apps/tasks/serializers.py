from rest_framework import serializers
from .models import Task
from apps.projects.serializers import TagSerializer
from apps.users.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assignees = UserSerializer(source='u_users', many=True, read_only=True)
    tags = TagSerializer(source='u_tags', many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'status', 'estimated_time', 'actual_time', 'project', 'u_users', 'u_tags']
