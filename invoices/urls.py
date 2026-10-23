from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('<int:pk>/download/', views.invoice_download_pdf, name='invoice_download'),
    path('<int:pk>/email/', views.invoice_email, name='invoice_email'),
]