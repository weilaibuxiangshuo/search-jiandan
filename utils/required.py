# -*- coding: utf-8 -*-
# 18-11-10 下午3:17
# AUTHOR:June
import functools

from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse
from apps.userapp.models import AdminGroup, AdminPermission


def group_required(module):
    def _group_required(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # 获取接口需要的权限，根据权限获取拥有该权限的组，再判断用户所在的组是否是其中的一个组，是则通过校验
            login_user = request.user
            # 如果是超级用户可以访问所有的接口
            if login_user.is_superuser:
                return func(self, request, *args, **kwargs)
            try:
                #　如果该接口是传入需要的权限是列表，则只需要满足其中一个的组，就可以访问
                if isinstance(module, list):
                    one = AdminPermission.objects.get(name=module[0])
                    two = AdminPermission.objects.get(name=module[1])
                    group_objs = AdminGroup.objects.filter(Q(permission=one)|Q(permission=two)).all()
                else:
                    # 根据权限名获取权限对象
                    pmsion = AdminPermission.objects.get(name=module)
                    # 根据权限对象获取 拥有该权限的所有的组
                    group_objs = AdminGroup.objects.filter(permission=pmsion).all()
                #　获取用户所在的组
                user_group = AdminGroup.objects.get(group_user=login_user)
            except Exception as e:
                # return HttpResponseForbidden()
                return HttpResponse('没有权限')
            # 如果用户的组不在　有权限的组里，禁止访问接口
            if user_group not in group_objs:
                return HttpResponse('没有权限')
            # user_list = []
            # for i in group_objs:
            #    for p in i.group_user.all():
            #        user_list.append(p.username)
            # if login_user.username not in user_list:
            #     return HttpResponseForbidden()
            return func(self, request, *args, **kwargs)
        return wrapper
    return _group_required


