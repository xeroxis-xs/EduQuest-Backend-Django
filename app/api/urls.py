from django.urls import path, re_path
from .views import (
    WooclapUserListCreateView,
    WooclapUserManageView,
    RegisterView,
    CustomTokenObtainPairView,
    UserProfileView,
    AzureLoginView
)
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/azure-login/', AzureLoginView.as_view(), name='azure_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('interesting-data/', views.interesting_data, name='interesting-data'),
    path('air-quality/', views.air_quality, name='air-quality'),
    # path('', views.login_successful, name='login-successful'),
    path('WooclapUsers/', WooclapUserListCreateView.as_view(), name='WooclapUser-list-create'),
    path('WooclapUsers/<int:pk>/', WooclapUserManageView.as_view(), name='WooclapUser-retrieve-update-destroy'),
]
