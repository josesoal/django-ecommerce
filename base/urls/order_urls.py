from django.urls import path
from base.views import order_views as views

urlpatterns = [
    path('myorders/', views.getMyOrders, name='myorders'),
    path('add/', views.addOrderItems, name='order-add'),
    path('<str:pk>/', views.getOrderById, name='user-order'),
    path('<str:pk>/pay/', views.updateOrderToPaid, name='pay'),
]