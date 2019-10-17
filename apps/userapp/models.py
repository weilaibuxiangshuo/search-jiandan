from django.contrib.auth.models import AbstractUser
from django.db import models

from payout import settings

usermodels = settings.AUTH_USER_MODEL


class User(AbstractUser):
    """管理员表"""

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AdminPermission(models.Model):
    """权限表"""
    name = models.CharField('权限', max_length=15)


class AdminGroup(models.Model):
    """管理员分组表（权限组）"""
    name = models.CharField('组名', max_length=15)
    permission = models.ManyToManyField(AdminPermission, verbose_name='权限')
    group_user = models.ManyToManyField(usermodels, '用户')

