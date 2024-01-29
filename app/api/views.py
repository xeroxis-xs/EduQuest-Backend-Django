from rest_framework import generics
from .models import WooclapUser
from .serializers import WooclapUserSerializer


class WooclapUserListCreateView(generics.ListCreateAPIView):
    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer


class WooclapUserManageView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WooclapUser.objects.all()
    serializer_class = WooclapUserSerializer
