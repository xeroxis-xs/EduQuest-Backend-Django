from django.urls import path, re_path
from .views import (
    WooclapUserListCreateView,
    WooclapUserManageView,
)


urlpatterns = [

    # path('', views.login_successful, name='login-successful'),
    path('WooclapUsers/', WooclapUserListCreateView.as_view(), name='WooclapUser-list-create'),
    path('WooclapUsers/<int:pk>/', WooclapUserManageView.as_view(), name='WooclapUser-retrieve-update-destroy'),
]
