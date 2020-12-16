from datetime import datetime

from alipay import AliPay
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from course.models import CourseExpire
from order.models import Order
from payments.models import UserCourse


class AliPayAPIView(APIView):

    def get(self, request):
        """生成支付宝的支付链接"""

        # 获取订单
        order_number = request.query_params.get("order_number")
        print(order_number)
        print(111)

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"message": "对不起，您支付的订单不存在"}, status=status.HTTP_400_BAD_REQUEST)

        # 初始化支付宝的参数
        alipay = AliPay(
            appid=settings.ALIAPY_CONFIG['appid'],
            app_notify_url=settings.ALIAPY_CONFIG['app_notify_url'],  # 默认回调url
            # 应用私钥 需要开发者自己生成
            app_private_key_string=settings.ALIAPY_CONFIG['app_private_key_path'],
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=settings.ALIAPY_CONFIG['alipay_public_key_path'],
            sign_type=settings.ALIAPY_CONFIG['sign_type'],  # RSA 或者 RSA2
            debug=settings.ALIAPY_CONFIG['debug'],  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            # 订单号
            out_trade_no=order.order_number,
            # 订单总价
            total_amount=float(order.real_price),
            subject=order.order_title,
            return_url=settings.ALIAPY_CONFIG['return_url'],
            notify_url=settings.ALIAPY_CONFIG['notify_url'],  # 可选, 不填则使用默认notify url
        )

        # 根据生成好的地址与支付网关拼接起来
        url = settings.ALIAPY_CONFIG["gateway_url"] + order_string
        print(url)
        return Response(url)


class AliPayResultAPIView(APIView):
    """
    处理支付宝支付成功后的业务：验证一下支付成功
    修改订单状态  生成用户的购买记录   展示结算的信息
    """

    def get(self, request):
        # 初始化支付宝的参数
        alipay = AliPay(
            appid=settings.ALIAPY_CONFIG['appid'],
            app_notify_url=settings.ALIAPY_CONFIG['app_notify_url'],  # 默认回调url
            # 应用私钥 需要开发者自己生成
            app_private_key_string=settings.ALIAPY_CONFIG['app_private_key_path'],
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=settings.ALIAPY_CONFIG['alipay_public_key_path'],
            sign_type=settings.ALIAPY_CONFIG['sign_type'],  # RSA 或者 RSA2
            debug=settings.ALIAPY_CONFIG['debug'],  # 默认False
        )

        # 验证支付宝支付的异步通知
        data = request.query_params.dict()
        signature = data.pop("sign")

        # verification
        success = alipay.verify(data, signature)
        if success:
            # TODO 修改订单状态  生成用户的购买记录   展示结算的信息
            return self.order_result_pay(data)

        return Response("OK")

    def order_result_pay(self, data):
        """
        修改订单状态  生成用户的购买记录   展示结算的信息
        :param data:
        :return:
        """
        # 先查询订单是否成功
        order_number = data.get('out_trade_no')
        try:
            order = Order.objects.get(order_number=order_number, order_status=0)
        except Order.DoesNotExist:
            return Response({"message": "对不起，支付结果查询失败！"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order.pay_time = datetime.now()
            order.order_status = 1
            order.save()

            # g根据订单获取用户
            user = order.user
            # 获取当前订单所购买的所有的课程信息
            order_detail_list = order.order_courses.all()
            # 订单结算页所需的信息
            course_list = []

            for order_detail in order_detail_list:
                """遍历本次订单中所有的商品信息"""
                course = order_detail.course
                course.students += 1
                course.save()

                # TODO 判断用户购买的课程是否是长期有效  如果不是长期有效则为课程记录到期时间
                pay_time = order.pay_time.timestamp()
                if order_detail.expire > 0:
                    expire = CourseExpire.objects.get(pk=order_detail.expire)
                    expire_time = expire.expire_time * 24 * 60 * 60
                    # 当前购买时间 + 有效期时间 =最终的到期时间
                    end_time = datetime.fromtimestamp(pay_time + expire_time)
                else:
                    # 永久购买
                    end_time = None

                # 为用户生成购买记录
                UserCourse.objects.create(
                    user_id=user.id,
                    course_id=course.id,
                    trade_no=data.get('trade_no'),
                    buy_type=1,
                    pay_time=order.pay_time,
                    out_time=end_time
                )
                # time = str(order.pay_time).replace('-', '年', 1)
                # time = time.replace('-', '月', 1)
                # time = time.replace(' ', '日 ', 1)
                # time = time.split('.')[0]
                #  返回前端所需信息
                course_list.append({
                    "pay_time": order.pay_time,
                    "total_price": order_detail.real_price,
                    "name": course.name,
                })
                print("课程名", course.name)

        except:
            return Response({"message":"更新订单信息失败"}, status=status.HTTP_400_BAD_REQUEST)

        # 返回前端所需的数据
        return Response({
            "course_list": course_list,
        })

