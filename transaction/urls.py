from django.urls import path
from transaction import views

app_name = 'transaction'

urlpatterns = [
    path('api/loan/request/', views.request_loan_api, name='loan_request'),
    path('api/loan/approve/<str:approval_token>/', views.approve_loan_api, name='loan_approve'),
    path('api/loan/reject/<str:approval_token>/', views.reject_loan_api, name='loan_reject'),
    path('api/loan/pending/', views.pending_loans_api, name='loan_pending'),
]
