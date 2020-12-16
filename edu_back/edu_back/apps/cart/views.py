import logging

from django_redis import get_redis_connection
# from requests import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from course.models import Course, CourseExpire
from edu_back.settings.constants import IMG_SRC, IMG_SRC1

log = logging.getLogger('django')


# 购物车相关 需要使用 redis数据库
class CartViewSet(ViewSet):
    # 只有登陆成功且认证成功的才能添加购物车
    permission_classes = [IsAuthenticated]

    # 添加购物车
    def add_cart(self, request):
        """
        将用户提交的课程信息保存至购物车
        :param request: 课程 id 课程有效期 （用户id）
        :return:
        """
        course_id = request.data.get('course_id')
        print("课程id", course_id)
        user_id = request.user.id
        # 勾选状态
        select = True
        # 有效期
        expire = 0

        # 对前端传递的数据进行校验
        try:
            Course.objects.get(is_show=True, is_delete=False, id=course_id)
        except Course.DoesNotExist:
            return Response({
                'message': "您添加的课程不存在"
            }, status=status.HTTP_400_BAD_REQUEST)


        try:
            # 获取redis链接
            redis_connection = get_redis_connection('cart')
            # 使用管道操作redis
            pipeline = redis_connection.pipeline()
            # 开启管道
            pipeline.multi()
            # 将数据库保存到redis 购物车商品的信息 以及该商品对应的有效期
            pipeline.hset('cart_%s' % user_id, course_id, expire)
            # 被勾选的商品
            pipeline.sadd('selected_%s' % user_id, course_id)

            # 执行操作
            pipeline.execute()

            # 获取购物车的商品总数量
            course_len = redis_connection.hlen('cart_%s' % user_id)
        except:
            log.error("购物存储数据失败")
            return Response({
                'message': "参数有误，添加购物车失败！"
            }, status=status.HTTP_507_INSUFFICIENT_STORAGE)

        return Response({
            'message': "添加课程至购物车成功！",
            'data':course_len
        }, status=status.HTTP_200_OK)

    # 展示购物车
    def list_cart(self, request):
        _ = self
        user_id = request.user.id
        redis_connection = get_redis_connection('cart')
        cart_list_bytes = redis_connection.hgetall('cart_%s' % user_id)
        select_list_bytes = redis_connection.smembers('selected_%s' % user_id)

        # 循环从 mysql 中查询商品信息
        data = []
        # 获取购物车的商品总数量
        course_len = redis_connection.hlen('cart_%s' % user_id)

        for course_id_byte, expire_id_byte in cart_list_bytes.items():
            course_id = int(course_id_byte)
            expire_id = int(expire_id_byte)

            try:
                course = Course.objects.get(is_show=True, is_delete=False, pk=course_id)
            except Course.DoesNotExist:
                continue
                # 将购物车所需要的信息返回
            data.append({
                'selected': True if course_id_byte in select_list_bytes else False,
                'id': course.id,
                'name': course.name,
                'course_img': IMG_SRC1 + course.course_img.url,
                'expire_id': expire_id,
                'price': course.price,
                'expire_list': course.expire_list,
            })
        return Response({'data': data, 'course_len': course_len})

    # 改变勾选状态
    def change_select(self, request):
        _ = self
        selected = request.data.get('selected')
        course_id = request.data.get('course_id')
        user_id = request.user.id

        redis_connection = get_redis_connection('cart')
        if selected:
            redis_connection.sadd('selected_%s' % user_id, course_id)
        else:
            redis_connection.srem('selected_%s' % user_id, course_id)
        return Response('OK')

    # 删除数据
    def delete_cart(self, request):
        _ = self
        # 删除数据需要找到用户id 课程id
        course_id = request.data.get('course_id')
        user_id = request.user.id

        # 连接数据库，根据用户id， 课程id进行删除
        redis_connection = get_redis_connection("cart")
        redis_connection.srem("selected_%s" % user_id, course_id)
        redis_connection.hdel("cart_%s" % user_id, course_id)
        return Response("删除成功")

    # 修改有效期
    def modify_expire(self, request):
        _ = self
        course_id = request.data.get('course_id')
        user_id = request.user.id
        value = request.data.get('value')
        # 连接数据库
        redis_connection = get_redis_connection("cart")
        redis_connection.hset("cart_%s" % user_id, course_id, value)
        return Response('有效期已修改')

    # 获取购物车中已勾选的商品
    def get_select_course(self, request):
        _ = self

        user_id = request.user.id
        redis_connection = get_redis_connection("cart")

        # 获取购物车清单
        cart_list = redis_connection.hgetall("cart_%s" % user_id)
        # 获取选中的商品
        select_list = redis_connection.smembers("selected_%s" % user_id)
        print("购物车清单：", cart_list)
        total_price = 0
        data = []
        for course_id_byte, expire_id_byte in cart_list.items():
            course_id = int(course_id_byte)
            expire_id = int(expire_id_byte)
            print(course_id)

            if course_id_byte in select_list:
                try:
                    # 购物车中所有课程信息
                    course = Course.objects.get(is_show=True, is_delete=False, pk=course_id)
                except Course.DoesNotExist:
                    continue
                # 如果有效期的id大于0，则需要通过有效期对应的价格来计算活动真实价
                # id不大于0则使用课程本身的原价
                original_price = course.price
                expire_text = "永久有效"
                try:
                    if expire_id > 0:
                        course_expire = CourseExpire.objects.get(id=expire_id)
                        # 对应有效期的价格
                        original_price = course_expire.price
                        expire_text = course_expire.expire_text
                except CourseExpire.DoesNotExist:
                    pass
                # 根据已勾选的商品对应的有效期的价格来计算商品的最终价格
                print("有效期id: ", expire_id)
                final_price = course.final_price(expire_id)
                print("最终价格: ", final_price)
                # 将购物车所需的信息返回
                data.append({
                    "selected": True if course_id_byte in select_list else False,
                    "id": course.id,
                    "name": course.name,
                    "course_img": IMG_SRC1 + course.course_img.url,
                    "expire_id": expire_id,
                    "expire_text": expire_text,
                    "price": original_price,  # 原价
                    "final_price": final_price  # 实际价格
                })

                # 商品叠加后的真实总价
                total_price += float(final_price)

        return Response({"real_price": total_price, "course_list": data, "message": "ok"})

