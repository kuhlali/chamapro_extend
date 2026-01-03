from django.urls import path
from . import views

app_name = 'chama'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('create/', views.create_chama, name='create'),
    path('members/', views.dashboard_view, name='members'),
    path('chama/<slug:slug>/<uuid:pk>/', views.chama_detail_view, name='chama_detail'),
    path('chama/<slug:slug>/<uuid:pk>/members/', views.list_members, name='members_list'),
    path('chama/<slug:slug>/<uuid:pk>/invite/', views.invite_member, name='invite_member'),
    path('chama/<slug:slug>/<uuid:pk>/remove/<int:member_id>/', views.remove_member, name='remove_member'),
    path('chama/<slug:slug>/<uuid:pk>/loans/', views.loan_list, name='loan_list'),
    path('chama/<slug:slug>/<uuid:pk>/loans/<int:loan_id>/approve/', views.approve_loan, name='approve_loan'),
    path('chama/<slug:slug>/<uuid:pk>/loans/<int:loan_id>/reject/', views.reject_loan, name='reject_loan'),
    path('chama/<slug:slug>/<uuid:pk>/investments/', views.investment_list, name='investment_list'),
    path('chama/<slug:slug>/<uuid:pk>/investments/add/', views.add_investment, name='add_investment'),
    path('chama/<slug:slug>/<uuid:pk>/investments/<int:investment_id>/edit/', views.edit_investment, name='edit_investment'),
    path('chama/<slug:slug>/<uuid:pk>/investments/<int:investment_id>/delete/', views.delete_investment, name='delete_investment'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('reports/', views.reports_view, name='reports'),
    path('features/', views.features_view, name='features'),
]