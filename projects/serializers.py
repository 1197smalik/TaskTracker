from rest_framework import serializers
from .models import Project
from django.contrib.auth.models import User

class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    members = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'owner', 'members']

    def create(self, validated_data):
        if not validated_data.get('owner'):
            owner = User.objects.first()
            if owner is None:
                owner = User.objects.create_user(
                    username='system',
                    password=None,
                )
            validated_data['owner'] = owner
        return super().create(validated_data)
