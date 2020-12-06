from django.urls import path
from rest_framework_jwt import views as view

from user import views

urlpatterns = [
    path('login/', view.obtain_jwt_token),
    path('captcha/', views.CaptchaAPIView.as_view()),
    path('token/', view.jwt_response_payload_handler),

]