
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from course.models import CourseCategory, Course, CourseChapter
from course.pagination import CoursePageNumberPagination
from course.serializer import CourseCategoryModelSerializer, CourseModelSerializer, CourseDetailModelSerializer, \
    CourseChapterModelSerializer


# 课程分类查询接口
class CourseCategoryAPIView(ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategoryModelSerializer


# 课程查询接口
class CourseAPIView(ListAPIView):
    queryset = Course.objects.filter(is_show=True, is_delete=False).order_by('orders')
    serializer_class = CourseModelSerializer

    # 根据点击的分类的id的不同来展示对应课程
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filter_fields = ("course_category",)

    # 排序
    ordering_fields = ('id', 'students', 'lessons', 'price')

    # 分页的实现
    pagination_class = CoursePageNumberPagination


# 课程详细信息查询接口( 查询单个课程的详细信息 )
class CourseDetailAPIView(RetrieveAPIView):
    queryset = Course.objects.filter(is_show=True, is_delete=False)
    serializer_class = CourseDetailModelSerializer

    lookup_field = 'id'


# 课程章节查询接口
class CourseChapterAPIView(ListAPIView):
    queryset = CourseChapter.objects.all()


# 章节的课程课时查询接口
class CourseLessonAPIView(ModelViewSet):

    def chapter(self,  request):
        id = request.query_params.get('id')
        print(id)
        chap = CourseChapter.objects.filter(is_show=True, is_delete=False, course=id).order_by('orders').all()

        return Response({
            'message': '查询成功',
            #
            'data': CourseChapterModelSerializer(chap, many=True).data
        }, status=status.HTTP_200_OK)


