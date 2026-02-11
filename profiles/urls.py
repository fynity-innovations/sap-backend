from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('initiate/', views.ProfileInitiateView.as_view(), name='profile_initiate'),
    path('verify/', views.ProfileVerifyView.as_view(), name='profile_verify'),
    path('detail/<str:phone>/', views.ProfileDetailView.as_view(), name='profile_detail'),
]