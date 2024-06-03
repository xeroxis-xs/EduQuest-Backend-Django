from rest_framework import generics

from rest_framework.permissions import IsAuthenticated
from .models import WooclapUser
from django.contrib.auth.models import User
from .serializers import WooclapUserSerializer, UserSerializer
from django.http import HttpResponse


class WooclapUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer


class WooclapUserManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer


class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = User.objects.all()
    serializer_class = UserSerializer


    def get_object(self):
        return self.request.user