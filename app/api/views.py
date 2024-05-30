from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import WooclapUser
from .serializers import WooclapUserSerializer
from django.http import HttpResponse


class WooclapUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer


class WooclapUserManageView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer
