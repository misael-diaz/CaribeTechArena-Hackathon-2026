from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.twilio_webhook, name='twilio_webhook'),
]
