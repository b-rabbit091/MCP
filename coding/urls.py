from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CaseListView, SubmissionViewSet

app_name = 'coding'
router = DefaultRouter()
router.register(r'submission', SubmissionViewSet, basename='submission')
urlpatterns = [
    # Case related endpoints
    path('cases/', CaseListView.as_view(), name='case-list'),
    path('', include(router.urls)),
]
