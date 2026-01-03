from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('charts/dashboard/', views.dashboard_charts, name='dashboard_charts'),
]
