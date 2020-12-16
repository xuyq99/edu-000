from datetime import datetime

from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from course.models import Course, CourseExpire
from order.models import Order, OrderDetail


class OrderModelSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'pay_type', 'order_number',)
        extra_kwargs = {
            'id': {'read_only': True},
            'order_number': {'read_only': True},
            'pay_type': {'write_only': True},
        }

    def validate(self, attrs):
        pay_type = attrs.get('pay_type')
        try:
            # 支付类型
            Order.pay_choices[pay_type]
        except Order.DoesNotExist:
            raise serializers.ValidationError("支付方式不支持")
        return attrs

    # 生成订单
    def create(self, validate_data):
        redis_connection = get_redis_connection('cart')

        # 通过context传递request对象
        user_id = self.context['request'].user.id
        incr = redis_connection.incr('number')

        # 生成唯一的订单编号: 时间戳 + 用户id + 随机字符串
        order_number = datetime.now().strftime('%Y%m%d%H%M%S') + '%06d' % user_id + '%06d' % incr

        with transaction.atomic():
            # 设置事务回滚点
            rollback_id = transaction.savepoint()

            # 生成订单
            order = Order.objects.create(
                order_title="百知教育线上课程订单",
                total_price=0,
                real_price=0,
                order_number=order_number,
                order_status=0,
                pay_type=validate_data.get('pay_type'),
                credit=0,
                coupon=0,
                order_desc="I love python",
                user_id=user_id,
            )

            # 生成订单详情
            cart_list = redis_connection.hgetall('cart_%s' % user_id)
            select_list = redis_connection.smembers('selected_%s' % user_id)

            for course_id_byte, expire_id_byte in cart_list.items():
                course_id = int(course_id_byte)
                expire_id = int(expire_id_byte)
                if course_id_byte in select_list:
                    try:
                        # 获取购物车中所有的课程信息
                        course = Course.objects.get(is_show=True, is_delete=False, id=course_id)
                    except Course.DoesNotExist:
                        continue

                    # 如果有效期 id > 0, 则需要通过有效期对应的价格来计算活动真实价格、id 为0，
                    # 使用课程本事原价
                    # 原始价格
                    origin_price = course.price
                    # 设置默认有效期为永久有效
                    expire_text = "永久有效"
                    try:
                        if expire_id > 0:
                            course_expire = CourseExpire.objects.get(id=expire_id)
                            origin_price = course_expire.price
                            expire_text = course_expire.expire_text
                    except CourseExpire.DoesNotExist:
                        pass

                    # 根据已勾选的商品对应的有效期的价格，来计算商品的最终价格
                    print(expire_id)
                    final_price = course.final_price(expire_id)
                    try:
                        OrderDetail.objects.create(
                            order=order,
                            course=course,
                            expire=expire_id,
                            discount_name=course.discount_name,
                            price=origin_price,
                            real_price=final_price,
                        )
                    except:
                        # 回滚事务
                        transaction.savepoint_rollback(rollback_id)
                        raise serializers.ValidationError("订单生成失败")

                    # 计算订单原始总价
                    order.total_price += float(origin_price)
                    # 计算订单实际总价
                    order.real_price += float(final_price)

                order.save()

                #  将订单生成成功后的课程从购物车移除
                carts = OrderDetail.objects.all()
                for cart in carts:
                    redis_connection = get_redis_connection("cart")
                    redis_connection.srem("selected_%s" % user_id, cart.course_id)
                    redis_connection.hdel("cart_%s" % user_id, cart.course_id)


            return order




