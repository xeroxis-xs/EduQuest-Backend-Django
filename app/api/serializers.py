from rest_framework import serializers
from django.contrib.auth.models import User
from .models import WooclapUser


# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class WooclapUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WooclapUser
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'password', 'first_name', 'last_name', 'role')
#         extra_kwargs = {'password': {'write_only': True}}
#
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user
#
#     def update(self, instance, validated_data):
#         instance.first_name = validated_data.get('first_name', instance.first_name)
#         instance.last_name = validated_data.get('last_name', instance.last_name)
#         instance.role = validated_data.get('role', instance.role)
#         instance.save()
#         return instance
#
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#
#         # Add custom claims
#         token['user_id'] = user.id
#         token['role'] = user.role
#
#         return token
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         refresh = self.get_token(self.user)
#
#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#
#         # Add extra responses here
#         data['user_id'] = self.user.id
#         data['username'] = self.user.username
#         data['role'] = self.user.role
#
#         return data
