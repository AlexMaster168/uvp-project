from rest_framework import serializers
from .models import Access

class AccessSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    password_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = Access
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_password_masked(self, obj):
        return '•' * 8
