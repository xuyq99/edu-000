
from rest_framework.generics import ListAPIView

from home.models import Banner, Nav
from home.serializer import BannerModelSerializer, NavModelSerializer, FNavModelSerializer


# 轮播图接口
class BannerAPIView(ListAPIView):
    queryset = Banner.objects.filter(is_show=True, is_delete=False).order_by("-orders")
    serializer_class = BannerModelSerializer


# 导航栏头部接口
class NavAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, is_delete=False, is_position=1).order_by("orders")
    serializer_class = NavModelSerializer


# 导航栏底部接口
class FNavAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, is_delete=False, is_position=2).order_by("orders")
    serializer_class = FNavModelSerializer
