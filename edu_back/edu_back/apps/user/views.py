from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as http_status, status
from rest_framework.viewsets import ModelViewSet
from rest_framework_jwt.settings import api_settings

from edu_back.libs.geetest import GeetestLib
from edu_back.settings import constants
from edu_back.utils.send_msg import Message
from user.models import UserInfo
from user.serializer import UserModelSerializer
from user.service import get_user_by_account

from django_redis import get_redis_connection
import random


pc_geetest_id = "759d5436a6bfe1e0a94d222e9452097b"
pc_geetest_key = "2061a99f3c25e50989a0c04536132953"


class CaptchaAPIView(APIView):
    """极验验证码"""

    user_id = 1
    status = False

    def get(self, request):
        """获取验证码"""
        username = request.query_params.get("username")
        user = get_user_by_account(username)
        if user is None:
            return Response({"message": "该用户不存在"},
                            status=http_status.HTTP_400_BAD_REQUEST)

        self.user_id = user.id

        # 通过极验类生成验证码对象
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        self.status = gt.pre_process(self.user_id)
        response_str = gt.get_response_str()
        return Response(response_str)

    def post(self, request):
        """验证验证码"""

        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.data.get("geetest_challenge")
        validate = request.data.get("geetest_validate")
        seccode = request.data.get("geetest_seccode")

        # 判断用户是否存在
        if self.user_id:
            result = gt.success_validate(challenge, validate, seccode, self.user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        print(result)
        result = {"status": "success"} if result else {"status": "fail"}
        return Response(result)


# 用户注册
class UserAPIView(CreateAPIView):
    queryset = UserInfo.objects.all()
    serializer_class = UserModelSerializer


# 验证手机号是否被注册
class IsRegister(APIView):
    def get(self, request):
        phone = request.query_params.get("phone")
        # 使用get_user_by_account的方式验证
        result = get_user_by_account(phone)
        if result:
            return Response("手机号已被注册")
        else:
            return Response("手机号可用")


# 获取验证码 为手机号生成验证码
class SendMessageAPIView(APIView):
    # 发送短信
    def get(self, request):
        # 获取 redis 连接
        redis_connection = get_redis_connection('sms_code')

        # 判断手机号在60s内是否发送过短信 ?????
        phone = request.query_params.get('phone')
        print(123, phone)
        phone_code = redis_connection.get('sms_%s' % phone)
        if phone_code is not None:
            return Response({"message": "您已在60秒内发过短信，不能重复发送"},  status=http_status.HTTP_400_BAD_REQUEST)

        # 生成随机的短信验证码
        code = random.randint(100000, 999999)
        print('code', code)

        # 将验证码保存至  redis
        # 设置验证码的间隔时间
        redis_connection.setex("sms_%s" % phone, constants.SET_INTERVAL_TIME, code)
        # 设置验证码的有效期
        redis_connection.setex("code_%s" % phone, constants.SET_EXPIRE_TIME, code)

        # 调用方法 完成 短信的发送，手机接收验证码
        try:
            # TODO 解锁即可验证
            msg = Message(constants.API_KEY)
            msg.send_message(phone, code)
            print("手机接收验证码为", code)
        except:
            return Response({
                'message': "短信发送失败"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 将发送的结果响应回去
        return Response({
            'message': "短信发送成功",
            'code': code,
        }, status=http_status.HTTP_200_OK)


# 验证码验证成功后进行处理
class HandleMessageAPIView(ModelViewSet):

    # 检验验证码
    def check_code(self, request):
        code = request.data.get("code")
        phone = request.data.get("phone")
        print('输入的验证码和手机号：', code, phone)
        # 获取redis连接
        redis_connection = get_redis_connection("sms_code")
        phone_code = redis_connection.mget("mobile_%s" % phone)[0].decode('utf-8')

        print("手机发送的验证码：", phone_code)
        if code == phone_code:
            self.delete_code(request)
            #
            redis_connection.delete("mobile_%s" % phone)
            return Response({'message': '验证码正确', }, status=http_status.HTTP_200_OK)
        # redis_connection.delete("sms_%s" % phone)
        redis_connection.delete("mobile_%s" % phone)
        return Response({"message": '验证码不正确'}, status=http_status.HTTP_400_BAD_REQUEST)

    # 短信登录方式，验证手机号是否注册
    def login(self, request):
        _ = self
        phone = request.data.get("phone")
        print(111, phone)
        user = UserInfo.objects.filter(phone=phone).first()
        print(222, user)
        if user:
            from rest_framework_jwt.settings import api_settings
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # 根据用户生成载荷
            payload = jwt_payload_handler(user)
            # 根据载荷生成token,添加token属性
            user.token = jwt_encode_handler(payload)
            return Response({
                'message': '手机号注册成功',
                'data': UserModelSerializer(user).data
            }, status=http_status.HTTP_200_OK)
        return Response({'message': '提示密码至少包含两种字符且长度大于8位', 'name': user}, status=http_status.HTTP_400_BAD_REQUEST)

    # 验证码验证成功后删除
    def delete_code(self, request, *args, **kwargs):
        phone = request.data.get("phone")
        # 获取redis连接
        redis_connection = get_redis_connection("sms_code")
        # 删除redis数据库中的键值对
        redis_connection.delete("mobile_%s" % phone)
        # redis_connection.delete("sms_%s" % phone)
        return Response({"message": "验证码删除成功！"}, status=http_status.HTTP_200_OK)
