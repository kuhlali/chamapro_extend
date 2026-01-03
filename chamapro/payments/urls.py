from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('contribute/<uuid:chama_id>/', views.initiate_contribution, name='initiate_contribution'),
    path('callback/', views.mpesa_callback, name='callback'),
    path('subscribe/<uuid:chama_id>/', views.pay_subscription, name='pay_subscription'),
    path('my-contributions/', views.contributions_view, name='contributions'),
    path('chama-contributions/<uuid:chama_id>/', views.chama_contributions_view, name='chama_contributions'),
    path('loans/', views.loans_view, name='loans'),
    path('transactions/', views.transactions_view, name='transactions'),
]