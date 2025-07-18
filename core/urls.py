from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('create-order/', views.create_order, name='create_order'),
    path('order/<slug:slug>/', views.view_order, name='view_order'),
    path('payment-success/<slug:slug>/', views.payment_success, name='payment_success'),
]
