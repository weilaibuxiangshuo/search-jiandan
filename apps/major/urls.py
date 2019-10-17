# -*- coding: utf-8 -*-
# 18-11-3 下午1:21
# AUTHOR:June
from django.conf.urls import url

from .views import *


urlpatterns = [

    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^uploadData$', UploadDataView.as_view(), name='uploadData'),  # end june
    url(r'^search$', SearchView.as_view(), name='search'),
    url(r'^searchiofo/(?P<page>\d+)$', SearchIofoView.as_view(), name='searchinfo'),
    url(r'^send$', SendView.as_view(), name='send'),
    url(r'^deletedata$', DeleteDataView.as_view(), name='deletedata'),
    url(r'^downloadinfo$', DownloadInfoView.as_view(), name='downloadinfo'),
    url(r'^uploadrecord/(?P<page>\d+)$', UploadRecord.as_view(), name='uploadrecord'),  # end li
    url(r'^typemanage/(?P<page>\d+)$', LotteryTypeManage.as_view(), name='typemanage'),
    url(r'^deletetype$', DeleteTypeView.as_view(), name='deletetype'),
    url(r'^addsend$', AddSendView.as_view(), name='addsend'),
    url(r'^searchupload/(?P<page>\d+)$', SearchUploadView.as_view(), name='searchupload'),
    url(r'^batchHandle$', BatchHandleView.as_view(), name='batchHandle'),  # 批量处理页面
    url(r'^batchSearch$', BatchSearchView.as_view(), name='batchSearch'),  # 批量处理
    url(r'^batchSend$', BatchSendView.as_view(), name='batchSend')  # 批量处理

]