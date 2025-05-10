from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

from . import views
router = DefaultRouter()

app_name = 'user'
router.register(r'user', UserViewSet, basename='user')

urlpatterns = [
    path('login', views.login_view, name='login'),
    path('register', views.register_view, name='register'),
    path('logout', views.logout_view, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify-email'),
              ]+ router.urls
