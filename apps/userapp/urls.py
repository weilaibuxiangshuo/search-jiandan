# -*- coding: utf-8 -*-
# 18-11-3 下午1:21
# AUTHOR:June
from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^loginrecs/(?P<page>\d+)$', LoginRecView.as_view(), name='loginrec'),  #登录的记录

    url(r'^mdfuser/(?P<page>\d+)$', MdfUserView.as_view(), name='mdfuser'),  # 修改管理员
    url(r'^deluser$', DelUserView.as_view(), name='deluser'),  # 删除管理员

    url(r'^adduser/(?P<page>\d+)$', AddUserView.as_view(), name='adduser'),
    url(r'^group/(?P<page>\d+)$', GroupView.as_view(), name='group'),

    url(r'^delgroup$', DelGroupView.as_view(), name='delgroup'),  # 删除组
    url(r'^addgroup$', AddGroupView.as_view(), name='addgroup'),  # 添加组
    url(r'^search/group$', SearchGroupView.as_view(), name='searchgroup'),  # 搜索组
    url(r'^search/user$', SearchAdminView.as_view(), name='searchuser'),  # 搜索管理员

    url(r'^login/search/(?P<page>\d+)$', LoginRecSearchView.as_view(), name='loginrecsearch'),  # 登录记录搜索
    url(r'^verifycode$', VerifyCodeView.as_view(), name='verifycode'),  # 验证码
    url(r'^adulog$', AduLogView.as_view(), name='adulog'),  # 管理员操作记录
    url(r'^adulogsearch/(?P<page>\d+)$', AduLogSearchView.as_view(), name='adulogsearch'),  # 管理员操作记录搜索接口
]