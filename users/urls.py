from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Public signup
    path('signup/', views.signup, name='signup'),
    
    # Admin-only user management
    path('', views.user_list, name='user_list'),
    path('<int:pk>/approve/', views.user_approve, name='user_approve'),
    path('<int:pk>/delete/', views.user_delete, name='user_delete'),
]