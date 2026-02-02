from rest_framework import serializers
from .models import Billing
from apps.users.serializers import UserSerializer

class BillingSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    participants = UserSerializer(source='users', many=True, read_only=True)
    
    class Meta:
        model = Billing
        fields = '__all__'
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
