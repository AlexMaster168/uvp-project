from rest_framework import serializers
from .models import MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_video = serializers.BooleanField(read_only=True)
    is_pdf = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MediaFile
        fields = '__all__'
