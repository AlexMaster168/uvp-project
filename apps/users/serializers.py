"""Serializers for users app."""
from rest_framework import serializers
from .models import User, GroupUsers

class GroupUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupUsers
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    u_group_name = serializers.CharField(source='u_group.get_name_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'u_group', 'u_group_name', 'status', 'is_staff', 'is_active']
        read_only_fields = ['is_staff']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'u_group']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
