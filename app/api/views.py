from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import WooclapUser
from .serializers import WooclapUserSerializer
from django.http import HttpResponse

import jwt
import os
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
# from nameparser import HumanName
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from dotenv import load_dotenv, find_dotenv
from django.http import JsonResponse
import requests
from decouple import config

load_dotenv(find_dotenv())

# OTHER SECRETS
TENANT_ID = 'common'
CLIENT_ID = config('AZURE_AD_CLIENT_ID', '')

from .serializers import CustomTokenObtainPairSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AzureLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        id_token = request.data.get('idToken')
        if not id_token:
            return Response({'detail': 'ID token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Replace with your tenant ID and client ID
            tenant_id = TENANT_ID
            client_id = CLIENT_ID
            audience = f'api://{client_id}'

            payload = jwt.decode(
                id_token,
                options={'verify_signature': False},
                audience=audience,
                issuer=f'https://sts.windows.net/{tenant_id}/'
            )
        except (jwt.DecodeError, ValidationError):
            return Response({'detail': 'Invalid ID token.'}, status=status.HTTP_401_UNAUTHORIZED)

        name = payload.get('name')
        email = payload.get('email') or payload.get('preferred_username')
        if not email:
            return Response({'detail': 'Email not found in ID token.'}, status=status.HTTP_400_BAD_REQUEST)

        if not name:
            return Response({'detail': 'Name not found in ID token.'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse human name
        first_name = name.first
        last_name = name.last

        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email,
                      'first_name': first_name.title(),
                      'last_name': last_name.title()}
        )

        if created:
            message = 'User created and logged in.'
        else:
            message = 'User logged in.'

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            'message': message,
            'access': access_token,
            'refresh': refresh_token,
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
        }, status=status.HTTP_200_OK)


#####-----------------------------Start of Customer facing API----------------------------------#####
def interesting_data(request):
    data = {
        "fact": "The Earth revolves around the Sun in about 365.25 days."
    }
    return JsonResponse(data)


def air_quality(request):
    url = "https://api.openaq.org/v1/latest?country=US&parameter=pm25"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        data = {"error": "Failed to fetch air quality data."}
    return JsonResponse(data)


class WooclapUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer


class WooclapUserManageView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer
