from django.urls import path, re_path
from .views import (
    WooclapUserListCreateView,
    WooclapUserManageView,
    UserDetailView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [

    # path('', views.login_successful, name='login-successful'),
    # path("token/refresh/", TokenRefreshView.as_view(), name="refresh_token"),
    # path("token/register/", WooclapUserListCreateView.as_view(), name="register"),
    # path("token/", TokenObtainPairView.as_view(), name="get_token"),
    path("Users/", UserDetailView.as_view(), name='User-detail'),
    path("WooclapUsers/", WooclapUserListCreateView.as_view(), name='WooclapUser-list-create'),
    path("WooclapUsers/<int:pk>/", WooclapUserManageView.as_view(), name='WooclapUser-retrieve-update-destroy'),
]
