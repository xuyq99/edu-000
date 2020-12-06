from django.db import models
from django.contrib.auth.models import AbstractUser


class UserInfo(AbstractUser):
    phone = models.CharField(max_length=11, unique=True)
    user_head = models.ImageField(upload_to='user', verbose_name="用户头像")

    class Meta:
        db_table = 'bz_user'
        verbose_name = "用户"
        verbose_name_plural = verbose_name

