from django.urls import path

from course import views

urlpatterns = [
    path('category/', views.CourseCategoryAPIView.as_view()),
    path('courses/', views.CourseAPIView.as_view()),
    path('detail/<int:id>/', views.CourseDetailAPIView.as_view()),
    path('chapter/', views.CourseLessonAPIView.as_view({'get': 'chapter'})),

]