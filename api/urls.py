"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path,include
from django.core.cache import cache
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

def status_view(request):
    return JsonResponse({"status": "active"})

def clear_cache_view(request):
    cache.clear()
    return JsonResponse({"message": "Cache cleared successfully"})
# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Safari Konnect",
        default_version='v1',
        description="API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="sam@phinosoft.co.ke"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', status_view, name='status'),
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('clear-cache/', clear_cache_view, name='clear-cache'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]