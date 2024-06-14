from django.urls import path, re_path
from .views import (
    WooclapUserListCreateView,
    WooclapUserManageView,
    UserDetailView,
)

urlpatterns = [
    path("Users/", UserDetailView.as_view(), name='User-detail'),
    path("WooclapUser/", WooclapUserListCreateView.as_view(), name='WooclapUser-list-create'),
    path("WooclapUser/<int:pk>/", WooclapUserManageView.as_view(), name='WooclapUser-retrieve-update-destroy'),
]
