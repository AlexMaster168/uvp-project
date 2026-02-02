from rest_framework import serializers
from .models import Tag, Project, ProjectMembership, Plan
from apps.users.serializers import UserSerializer

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'range', 'importance']

class ProjectMembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'user_name', 'role']

class ProjectListSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='u_creator.username', read_only=True)
    tags = TagSerializer(source='u_tags', many=True, read_only=True)
    tasks_count = serializers.IntegerField(source='get_tasks_count', read_only=True)
    financial_summary = serializers.SerializerMethodField()
    owners = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'start_date', 'end_date',
                  'logo', 'creator_name', 'tags', 'tasks_count', 'financial_summary', 'owners']
    
    def get_financial_summary(self, obj):
        return obj.get_financial_summary()
    
    def get_owners(self, obj):
        owners = obj.get_owners()
        return [{'id': m.user.id, 'username': m.user.username} for m in owners]

class ProjectDetailSerializer(serializers.ModelSerializer):
    u_creator_name = serializers.CharField(source='u_creator.username', read_only=True)
    tags = TagSerializer(source='u_tags', many=True, read_only=True)
    members = ProjectMembershipSerializer(many=True, read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'logo', 'u_tags']
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError("end_date must be >= start_date")
        return data

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'
