import codecs
import csv
import datetime
import json
import logging
import os
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from payout.settings import UPLOAD_PATH
from utils.fenye import fenye
from utils.mixin import LoginRequiredMixin
from utils.required import group_required
from utils.script import import_data
from .models import *

logger = logging.getLogger('log')


# 首页
class IndexView(LoginRequiredMixin, View):
    """首页"""

    def get(self, request):
        not_sent = Record.objects.filter(state=False).count()
        sent = Record.objects.filter(state=True).count()
        send_total_money = Record.objects.filter(state=True).aggregate(Sum('money'))  # 总派送
        context = {
            "total": format(not_sent + sent, ','),
            "not_sent": format(not_sent, ','),
            "sent": format(sent, ','),
            "send_total_money": send_total_money['money__sum']
        }
        # context['pms'] = getpms(request)
        context['pms'] = request.session['munu_list']
        return render(request, 'index.html', context)


# 上传
class UploadDataView(LoginRequiredMixin, View):
    """上传"""

    @group_required('上传数据包')
    def get(self, request):
        context = {'pms': request.session['munu_list'],'errmsg':''}
        return render(request, 'uploadData.html', context)

    @transaction.atomic
    @group_required('上传数据包')
    def post(self, request):
        myFile = request.FILES.get("myfile", None)
        tagname = request.POST.get('msg')  # 数据包的名称
        pmslist = request.session['munu_list']
        if not myFile or not tagname:
            context = {'pms': pmslist, 'errmsg': '请输入：数据包名、选择文件'}
            return render(request, 'uploadData.html', context)
        filename = myFile.name
        # 校验文件的格式是否正确
        try:
            file_format = filename.split('.')  # 文件的格式
            if file_format[-1] != 'csv':
                context = {'errmsg': '只允许上传csv格式'}
                context['pms'] = pmslist
                return render(request, 'uploadData.html', context)
        except Exception as e:
            context = {'errmsg': '只允许上传csv格式'}
            context['pms'] = pmslist
            return render(request, 'uploadData.html', context)
        # 获取日期(根据月份创建文件夹)
        today = datetime.datetime.today()
        upload_path = UPLOAD_PATH + datetime.datetime.strftime(today, '%Y%m')  # 年月
        try:
            # 文件不存在，就创建文件夹
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            # 文件完整路径
            filepath = os.path.join(upload_path, filename)
            # 分块写入文件
            f = open(filepath, 'wb+')
            for chunk in myFile.chunks():
                f.write(chunk)
            f.close()
        except Exception as e:
            context = {'errmsg': '没有服务器写入的权限，联系开发人员'}
            context['pms'] = pmslist
            return render(request, 'uploadData.html', context)
        # 设置事务保存点
        sid = transaction.savepoint()
        try:
            upload_obj = Upload.objects.create(dataname=tagname, filename=myFile, bywho=request.user.username)
        except Exception as e:
            context = {'errmsg': '数据包名或文件名字已存在，不能重复上传'}
            context['pms'] = pmslist
            return render(request, 'uploadData.html', context)
        # 导入数据
        number = import_data(filepath, tagname)
        if number == 0:
            transaction.savepoint_rollback(sid)
            context = {'errmsg': '上传文件内容格式错误，请检查格式和编码'}
            context['pms'] = pmslist
            return render(request, 'uploadData.html', context)
            # 回滚事务到sid保存点
        if number == -1:
            # 回滚事务到sid保存点
            transaction.savepoint_rollback(sid)
            context = {'errmsg': '连接服务器数据库失败，联系开发人员'}
            context['pms'] = pmslist
            return render(request, 'uploadData.html', context)
        upload_obj.number = number
        upload_obj.save()
        context = {'errmsg': '上传成功！'}
        context['pms'] = pmslist
        return render(request, 'uploadData.html', context)


# 信息查询页展示
class SearchView(LoginRequiredMixin, View):
    """查询数据"""

    @group_required('信息查询')
    def get(self, request):
        context = {'pms': request.session['munu_list'], 'msg':'', 'typeobj':[],'pageobjs':[]}
        return render(request, 'msgSearch.html', context)


# 信息查询搜索接口
class SearchIofoView(LoginRequiredMixin, View):
    @group_required('信息查询')
    def get(self, request, page):
        code = request.GET.get('searchCode')  # 搜索类型
        search_word = request.GET.get('searchWord')
        if code == '1101':
            recs = Record.objects.filter(name=search_word)
        elif code == '1102':
            recs = Record.objects.filter(tel=search_word)
        elif code == '1103':
            recs = Record.objects.filter(qq=search_word)
        elif code == '1104':
            recs = Record.objects.filter(email=search_word)
        else:
            return render(request, 'msgSearch.html', {'msg': '必须根据条件查询'})
        #money_sum = recs.filter(state=True).aggregate(Sum('money'))
        money_sum = 0
        for i in recs:
            if i.state:
                money_sum+=i.money
        typeobj = LotteryClass.objects.all()
        context = fenye(recs, page)
        context['money_sum'] = money_sum
        context['typeobj'] = typeobj
        context['searchCode'] = code
        context['searchWord'] = search_word
        context['pms'] = request.session['munu_list']
        if not recs:
            context['pms'] = request.session['munu_list']
            context['msg'] = '没有数据'
        return render(request, 'msgSearch.html', context)


# 派送
class SendView(LoginRequiredMixin, View):
    """派送"""

    @group_required('信息查询')
    def post(self, request):
        send_id = request.POST.get('pid')
        amount = request.POST.get('amount')
        lotterytypes = request.POST.get('lotterytypes')
        # 校验发送金额
        try:
            amount = float(amount)
        except Exception as e:
            return JsonResponse({"stat": 0, "msg": "发送失败，请输入合理的彩金"})
        if amount < 0:
            return JsonResponse({"stat": 0, "msg": "发送失败，请输入合理的彩金"})
        # 校验发送类型
        try:
            typeobj = LotteryClass.objects.get(id=int(lotterytypes))
        except Exception as e:
            return JsonResponse({"stat": 0, "msg": "发送失败, 类型错误"})
        try:
            send_rec = Record.objects.get(id=int(send_id))
        except Exception as e:
            return JsonResponse({"stat": 0, "msg": "发送失败，该记录不存在"})
        else:
            time_now = datetime.datetime.now()
            send_rec.money = amount
            send_rec.state = True
            send_rec.send_time = time_now
            send_rec.operator = request.user.username
            send_rec.lotteryclass = typeobj.name
            send_rec.save()
            return JsonResponse({
                "msg": "发送成功",
                "sendTime": time_now.strftime("%Y年%m月%d日 %H:%M"),
                "stat": 1,
                "bywho": request.user.username
            })


# 删除数据
class DeleteDataView(LoginRequiredMixin, View):
    @group_required('信息管理')
    def post(self, request):
        pk = request.POST.get('pk')
        try:
            upload_obj = Upload.objects.get(id=pk)
        except Exception as e:
            return JsonResponse({'msg': '数据不存在'})

        record_objs = Record.objects.filter(tagname=upload_obj.dataname)
        if record_objs.exists():
            record_objs.delete()
            upload_obj.is_delete = True
            upload_obj.del_person = request.user.username
            upload_obj.save()
            return JsonResponse({'msg': '删除成功'})
        return JsonResponse({'msg': '数据不存在'})


# 添加额外的派彩
class AddSendView(LoginRequiredMixin, View):
    """添加额外的派彩"""

    @group_required('信息查询')
    def post(self, request):
        userid = request.POST.get('pid')
        dataname = request.POST.get('dataname')
        username = request.POST.get('username')
        qqnum = request.POST.get('qqnum')
        telnum = request.POST.get('telnum')
        emailname = request.POST.get('emailname')
        amount = request.POST.get('amount')
        lotterytypes = request.POST.get('sendtype')

        # 校验发送金额
        try:
            amount = float(amount)
        except Exception as e:
            return JsonResponse({"status": 1, "msg": "发送失败，请输入合理的彩金"})
        if amount < 0:
            return JsonResponse({"status": 1, "msg": "发送失败，请输入合理的彩金"})
        # 校验发送类型
        try:
            typeobj = LotteryClass.objects.get(id=int(lotterytypes))
        except Exception as e:
            return JsonResponse({"status": 1, "msg": "发送失败, 类型错误"})
        try:
            send_rec = Record.objects.get(id=int(userid))
        except Exception as e:
            return JsonResponse({"status": 1, "msg": "发送失败，该用户不存在"})
        else:
            time_now = datetime.datetime.now()
            Record.objects.create(
                name=username,
                money=amount,
                qq=qqnum,
                tel=telnum,
                email=emailname,
                state=True,
                tagname=dataname,
                create_time=time_now,
                send_time=time_now,
                operator=request.user.username,
                lotteryclass=typeobj.name
            )
            return JsonResponse({
                "msg": "发送成功",
                "sendTime": time_now.strftime("%Y年%m月%d日 %H:%M"),
                "status": 0,
                "bywho": request.user.username
            })


# 数据下载
class DownloadInfoView(LoginRequiredMixin, View):
    @group_required('信息管理')
    def get(self, request):
        class_objs = LotteryClass.objects.all().order_by('id')
        context = {'class_data': class_objs}
        context['pms'] = request.session['munu_list']
        context['errmsg']=''
        return render(request, 'downloadInfo.html', context)

    @group_required('信息管理')
    def post(self, request):
        startTime = request.POST.get('startTime')  # 开始时间
        endTime = request.POST.get('endTime')  # 结束时间
        send_status = request.POST.get('send_status')  # 派发状态
        class_id = request.POST.get('type')  # 彩金类型
        if not all([startTime, endTime]):
            context = {"errmsg": "请选择时间段"}
            context['pms'] = request.session['munu_list']
            return render(request, 'downloadInfo.html', context)
        response = HttpResponse(content_type='text/csv')  # 设置响应类型
        # 根据用户选择筛选数据　开始结束日期和派发状态　派彩的类型
        records = Record.objects.filter(create_time__range=(startTime, endTime + ' 23:59:59'))  # 字符串拼接截止日期的最后一秒
        if send_status == '1':
            records = records.filter(state=True)
            # 如果没有全部
            if class_id != '0':
                lottery_obj = LotteryClass.objects.get(id=int(class_id))
                records = records.filter(lotteryclass=lottery_obj.name)
        elif send_status == '0':
            records = records.filter(state=False)
        # 声明一个csv的响应
        response['Content-Disposition'] = 'attachment; filename="%s-%s-%s.csv"' % (
            request.user.username, startTime, endTime)
        # csv的响应的编码格式声明
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        if records:
            writer.writerow(['id', '姓名', '金额', 'QQ', '号码', '邮箱', '是否派彩', '创建时间', '发送时间', '发送人', '彩金类型'])
            for record in records:
                writer.writerow([
                    record.id,
                    record.name,
                    record.money,
                    record.qq,
                    record.tel,
                    record.email,
                    '已发送' if record.state else '未发送',
                    record.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    record.send_time.strftime('%Y-%m-%d %H:%M:%S') if record.send_time else None,
                    record.operator,
                    record.lotteryclass
                ])
            return response
        else:
            class_objs = LotteryClass.objects.all().order_by('id')
            context = {'class_data': class_objs, 'errmsg': '没有符合条件的数据'}
            context['pms'] = request.session['munu_list']
            return render(request, 'downloadInfo.html', context)


# 上传数据的记录
class UploadRecord(LoginRequiredMixin, View):
    @group_required('信息管理')
    def get(self, request, page):
        uploads = Upload.objects.all().order_by('-id')
        context = fenye(uploads, page)
        context['pms'] = request.session['munu_list']
        context['msg']=''
        return render(request, 'uploadRecord.html', context)


# 上传数据的记录搜索
class SearchUploadView(LoginRequiredMixin, View):
    @group_required(['信息管理'])
    def get(self, request, page):
        searchword = request.GET.get('searchword')
        if not searchword:
            return render(request, 'uploadRecord.html', {'msg': '请输入搜索词'})
        search_data = Upload.objects.filter(
            Q(dataname__icontains=searchword) | Q(filename__icontains=searchword) | Q(Q(bywho__icontains=searchword)))
        context = fenye(search_data, page)
        context['searchword'] = searchword
        context['pms'] = request.session['munu_list']
        return render(request, 'uploadRecordSearch.html', context)


# 彩金类型管理
class LotteryTypeManage(LoginRequiredMixin, View):
    """彩金类型管理"""

    @group_required('信息管理')
    def get(self, request, page):
        classobj = LotteryClass.objects.all().order_by('id')
        context = fenye(classobj, page, 8)
        context['pms'] = request.session['munu_list']
        return render(request, 'typeManage.html', context)

    @group_required('信息管理')
    def post(self, request, page):
        typename = request.POST.get("typename")
        if not typename:
            return JsonResponse({"msg": "请输入类型"})
        try:
            LotteryClass.objects.get(name=typename)
        except Exception as e:
            LotteryClass.objects.create(name=typename)
            return JsonResponse({"msg": "添加成功"})
        return JsonResponse({"msg": "添加失败，该类型已存在"})


# 删除彩金类型
class DeleteTypeView(LoginRequiredMixin, View):
    """删除彩金类型"""

    @group_required('信息管理')
    def post(self, request):
        typeid = request.POST.get('typeid')
        try:
            typeobj = LotteryClass.objects.get(id=typeid)
        except Exception as e:
            return JsonResponse({"msg", "该类型不存在"})
        typeobj.delete()
        return JsonResponse({"msg": "删除成功"})


class BatchHandleView(LoginRequiredMixin, View):
    """批量搜索页面展示"""

    def get(self, request):
        context = {}
        context['pms'] = request.session['munu_list']
        context['msg'] = ''
        context['typeobj']=[]
        context['pageobjs']=[]
        return render(request, 'batchHandler.html',context)


class BatchSearchView(LoginRequiredMixin, View):
    """批量搜索"""

    def post(self, request):
        code = request.POST.get('searchCode')  # 搜索类型searchCode
        search_word = request.POST.get('searchWord')#searchWord
        word_list = search_word.split(' ')
        query_obj_list = []
        error_list = []
        for i in word_list:
            if code == '1101':
                objs = Record.objects.filter(name=i)
            elif code == '1102':
                objs = Record.objects.filter(tel=i)
            elif code == '1103':
                objs = Record.objects.filter(qq=i)
            elif code == '1104':
                objs = Record.objects.filter(email=i)
            else:
                objs = Record.objects.filter(tel=i)
            if not objs.exists():
                error_list.append(i)
            else:
                for obj in objs:
                    query_obj_list.append(obj)
        typeobj = LotteryClass.objects.all()  # 彩金类型
        context = {}
        context['typeobj'] = typeobj
        context['pms'] = request.session['munu_list']
        context['query_obj_list'] = query_obj_list  # 查到的结果
        context['error_list'] = error_list  # 未查到的结果
        return render(request, 'batchHandler.html', context)


class BatchSendView(LoginRequiredMixin, View):
    """批量派彩"""

    def post(self, request):
        selected_data = request.POST.get('selected_data')
        selected_obj = json.loads(selected_data)
        time_now = datetime.datetime.now()
        if not selected_obj:
            return JsonResponse({'code': 400, 'msg': '请选择派彩对象'})
        for i in selected_obj:
            typename = LotteryClass.objects.get(id=i['typeid']).name
            obj = Record.objects.get(id=i['pid'])
            obj.money = i['money']
            obj.state = True
            obj.operator = request.user.username
            obj.lotteryclass = typename
            obj.send_time = time_now
            obj.save()
        return JsonResponse({'code':200, 'msg':'派送成功'})