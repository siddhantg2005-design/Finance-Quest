"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import health, ProfileViewSet, TransactionViewSet, GoalViewSet, XPLogViewSet
from core.views_profile_example import profile_snapshot
from core.auth_views import signup_view, login_view, me_profile
from core.xp_views import award_xp_view

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'xp-log', XPLogViewSet, basename='xp-log')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('api/', include(router.urls)),
    # Auth endpoints (bypass middleware)
    path('api/auth/signup/', signup_view),
    path('api/auth/login/', login_view),
    path('api/profile/', me_profile),
    path('api/profile/snapshot/', profile_snapshot),
    path('api/xp/award/', award_xp_view),
]
