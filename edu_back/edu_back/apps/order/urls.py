from django.urls import path

from order import views

urlpatterns = [
    path('option/', views.OrderAPIView.as_view()),

]