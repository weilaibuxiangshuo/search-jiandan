from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here
class Record(models.Model):
    """上传数据"""
    name = models.CharField('姓名', max_length=35)
    money = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='彩金')
    qq = models.CharField('QQ', max_length=15)
    tel = models.CharField('电话号码', max_length=15, db_index=True)
    email = models.CharField('邮箱', max_length=25)
    state = models.BooleanField('状态', default=False)
    tagname = models.CharField('数据标签', max_length=50)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    send_time = models.DateTimeField('派送时间', blank=True, null=True)
    operator = models.CharField('操作人', max_length=35, blank=True, null=True)
    lotteryclass = models.CharField('彩金类型', max_length=35, default='')


class LoginRecord(models.Model):
    """登录记录"""
    name = models.CharField('姓名', max_length=35)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='登录时间')
    state = models.BooleanField('操作类型')
    ip = models.GenericIPAddressField('IP地址')


class Upload(models.Model):
    """上传包上传批次记录"""
    dataname = models.CharField('数据包名', max_length=50, unique=True)
    create_time = models.DateTimeField('上传时间', auto_now_add=True)
    filename = models.CharField('文件名称', max_length=50, unique=True)
    number = models.IntegerField('导入数量', blank=True, null=True)
    is_delete = models.BooleanField('是否已删除', default=False)
    bywho = models.CharField('上传人', max_length=35)
    del_person = models.CharField('删除人', max_length=35, default='')


class LotteryClass(models.Model):
    """彩金分类"""
    name = models.CharField('彩金类型', max_length=35)
