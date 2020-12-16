from django.urls import path
from rest_framework_jwt import views as view

from user import views

urlpatterns = [
    path('login/', view.obtain_jwt_token),
    path('token/', view.jwt_response_payload_handler),

    path('captcha/', views.CaptchaAPIView.as_view()),
    path('register/', views.UserAPIView.as_view()),
    path('message/', views.SendMessageAPIView.as_view()),
    path('isregister/', views.IsRegister.as_view()),

    path('phone_login/', views.HandleMessageAPIView.as_view({'post': 'login'})),

    path('check/', views.HandleMessageAPIView.as_view({'patch': 'check_code'})),
    path('delete/', views.HandleMessageAPIView.as_view({'delete': 'delete_code'})),



]