from django.urls import path

from cart import views

urlpatterns = [
    path('option/', views.CartViewSet.as_view({'get': 'list_cart',
                                               'post': 'add_cart',
                                               'put': 'modify_expire',
                                               'patch': 'change_select',
                                               'delete': 'delete_cart'})),
    
    
    path('order/', views.CartViewSet.as_view({'get': 'get_select_course'})),

]

