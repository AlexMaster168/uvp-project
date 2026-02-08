from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_superuser = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'status', 'password', 'is_superuser']

    def create(self, validated_data):
        is_superuser = validated_data.pop('is_superuser', False)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            is_staff=is_superuser,
            is_superuser=is_superuser
        )
        return user
