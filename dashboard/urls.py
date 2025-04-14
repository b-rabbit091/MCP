from django.urls import path

from .views import PieChartDataView

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', PieChartDataView.as_view(), name='pie-chart-data'),
]
