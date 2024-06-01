"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.defaults import bad_request
from rest_framework.authtoken.views import obtain_auth_token

def redirect_to_oath2_login(request):
    return redirect('oath2/login')

def redirect_to_admin(request):
    return redirect('/admin/')


def is_admin(user):
    return user.is_authenticated and user.is_staff

def custom_error_redirect(request):
    return redirect('https://eduquest-backend.azurewebsites.net/admin')

schema_view = get_schema_view(
   openapi.Info(
      title="NTU Leaderboard API",
      default_version='v1',
      description="This a documentation for the EduQuest API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="C210101@e.ntu.edu.sg"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_admin),
    # path('oath2/', include('django_auth_adfs.urls')),
    # path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    # path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # path('docs/', user_passes_test(is_admin)(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # # Custom view for handling 400 status code
    # path('custom_error_redirect/', custom_error_redirect, name='custom_error_redirect'),

    # # Override the default view for 400 status code
    # path('404/', bad_request, kwargs={'exception': Exception('Bad Request')}),
]

# # If DEBUG is False, include a catch-all URL pattern for handling 400 errors
# if not settings.DEBUG:
#     urlpatterns += [path('<path:path>', custom_error_redirect)]