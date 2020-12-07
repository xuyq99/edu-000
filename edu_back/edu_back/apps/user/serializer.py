import re

from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from user.models import UserInfo
from user.service import get_user_by_account


class UserModelSerializer(ModelSerializer):
    """
    1. 对前端传递的数据进安全校验
    2. 对相关字段进行处理  用户名 密码加密 邮箱 手机号
    3. 对注册成功的用户生成 token
    """

    # 定义model不存在的字段（新增字段）
    token = serializers.CharField(max_length=1024, read_only=True, help_text="用户token")
    sms_code = serializers.CharField(max_length=1024, write_only=True, help_text="用户token")


    class Meta:
        model = UserInfo
        fields = ('phone', 'password', 'username', 'id', 'token', 'sms_code')

        extra_kwargs = {
            'phone': {
                'write_only': True
            },
            'password': {
                'write_only': True
            },
            'username': {
                'read_only': True
            },
            'id': {
                'read_only': True
            }

        }

    # 前端参数校验
    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        # 获取用户输入的验证码
        sms_code = attrs.get('sms_code')
        print(123, phone, sms_code)

        # 验证手机号
        if not re.match(r'^1[[3-9]\d{9}$', phone):
            raise serializers.ValidationError("手机号格式不正确")

        # 验证手机号是否存在
        try:
            user = get_user_by_account(phone)
        except UserInfo.DoesNotExist:
            user = None

        if user:
            raise serializers.ValidationError("手机号已被注册")

        # TODO  1.验证手机号对应的密码是否正确
        # 限制总共可以验证多少次 3次

        # 成功验证后，需要及时删除验证码


        # TODO  2.验证密码 最少6位，最少包含两种字符

        return attrs



    # 用户信息设置
    def create(self, validated_data):
        # 对密码加密
        password = validated_data.get('password')
        hash_pwd = make_password(password)
        print(hash_pwd)

        # 处理用户名 设置默认名为phone
        phone = validated_data.get('phone')
        # 添加数据
        user = UserInfo.objects.create(phone=phone, password=hash_pwd, username=phone)

        # 为注册成功的用户生成 token
        # 根据用户生成载荷
        from rest_framework_jwt.settings import api_settings
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        # 给用户增加 token属性
        user.token = jwt_encode_handler(payload)

        return user


