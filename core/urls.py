# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaticPageViewSet, NotificationViewSet, AnalyticsViewSet

app_name = 'core'

router = DefaultRouter()
router.register(r'static-pages', StaticPageViewSet, basename='static-page')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]
