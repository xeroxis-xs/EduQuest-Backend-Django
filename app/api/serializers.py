from rest_framework import serializers
from .models import WooclapUser

class WooclapUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WooclapUser
        fields = '__all__'
