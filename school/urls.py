from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('login/', views.school_login, name='login'),
    path('logout/', views.school_logout, name='logout'),
    path('register/', views.school_register, name='register'),
    path('dashboard/', views.school_dashboard, name='dashboard'),
    path('sales/new/', views.create_sale, name='create_sale'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='notification_read'),
    path('metrics/', views.metrics_list, name='metrics'),
]
