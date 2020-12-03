from django.urls import path, re_path

from home import views

urlpatterns = [
    path('banners/', views.BannerAPIView.as_view()),
    # re_path(r'nav/(?P<is_position>\d*)', views.NavAPIView.as_view()),
    path('nav/', views.NavAPIView.as_view()),
    path('f_nav/', views.FNavAPIView.as_view()),

]