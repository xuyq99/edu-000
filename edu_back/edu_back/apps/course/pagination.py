from rest_framework.pagination import PageNumberPagination


class CoursePageNumberPagination(PageNumberPagination):
    # 课程列表的分页器
    page_query_param = 'page'
    page_size_query_param = 'size'
    page_size = 2
    max_page_size = 10


