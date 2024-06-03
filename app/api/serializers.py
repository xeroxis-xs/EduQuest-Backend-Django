from rest_framework import serializers
from django.contrib.auth.models import User
from .models import WooclapUser


class WooclapUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WooclapUser
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']
