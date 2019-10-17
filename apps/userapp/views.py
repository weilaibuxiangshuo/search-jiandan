from apps.userapp.models import User,AdminGroup,AdminPermission
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from utils.mixin import LoginRequiredMixin
from apps.major.models import LoginRecord,Record
from utils.required import group_required
from django.core.paginator import Paginator
from utils.checkcode import checkcode
from django.views.generic import View
from django.urls import reverse
from utils.fenye import fenye
from utils.getpms import getpms
import datetime,logging
import json

logger = logging.getLogger('log')

# 登录
class LoginView(View):
    """登录"""

    def get(self, request):
        return render(request, 'login.html')

    def post(self,request):
        # 获取ip信息
        if 'HTTP_X_FORWARDED_FOR' in request.META.values():
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        yzm = request.POST.get('chkcode')
        # 2.参数完整性校验
        if not all([username, password, yzm]):
            return render(request, 'login.html', {'errmsg': '参数不完整'})
        # 3.验证码校验
        verifycode = request.session.get('verifycode','')
        if yzm.lower() != verifycode.lower():
            return render(request, 'login.html', {'errmsg': '验证码错误'})
        # 3.业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活
                # 记住用户的登录状态
                login(request, user)
                LoginRecord.objects.create(name=username, state=True, ip=ip)
                # 获取用户登录之前访问的url地址，默认跳转到首页
                next_url = request.GET.get('next', reverse('major:index')) # None
                # 跳转到next_url
                response = redirect(next_url)  # HttpResponseRedirect
                # 设置session（后期可以做成中间件）
                request.session['munu_list'] = getpms(request)
                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            LoginRecord.objects.create(name=username, state=False, ip=ip)
            return render(request, 'login.html', {'errmsg': '用户名或密码错误，请重新输入！'})


# 验证码
class VerifyCodeView(View):
    """验证码"""
    def get(self, request):
        rand_str, buf = checkcode()
        # 存入session，用于做进一步验证
        request.session['verifycode'] = rand_str
        return HttpResponse(buf.getvalue(), 'image/png')


# 退出
class LogoutView(LoginRequiredMixin,View):

    def get(self, request):
        logout(request)
        return redirect(reverse('userapp:login'))


# 展示用户修改页，post修改用户密码和组
class MdfUserView(LoginRequiredMixin, View):

    @group_required('管理员模块')
    def get(self, request, page):
        group_objs = AdminGroup.objects.all()  # 展示管理员和下拉组
        users = User.objects.all().order_by('id')
        context = fenye(users, page, 5)
        for user_obj in context['pageobjs']:
            login_last = LoginRecord.objects.filter(name=user_obj.username).last()  # 最后的登录记录
            group = AdminGroup.objects.filter(group_user=user_obj).last()  # 用户所在组
            user_obj.last_time = login_last.create_time if login_last else ''  # 最后登陆的时间
            user_obj.last_ip = login_last.ip if login_last else ''  # 最后登陆ip
            user_obj.group = group.name if group else ''  # 所属管理组
            user_obj.group_id = group.id if group else ''  # 管理组id
        context["group_data"] = group_objs
        context['pms'] = request.session['munu_list']
        return render(request, 'mdfuser.html', context)

    @group_required('管理员模块')
    def post(self, request, page):
        rename = request.POST.get('username')
        repwd = request.POST.get('newpwd')
        group_id = request.POST.get('groupid')
        # 判断用户名是否存在
        try:
            use_obj = User.objects.get(username=rename)
        except Exception as e:
            return JsonResponse({"stat": 0, "msg": '用户不存在'})
        try:
            group_obj = AdminGroup.objects.get(id=group_id)
        except Exception as e:
            return JsonResponse({"stat": 0, "msg": '请选择组'})
        # 如果用户提交了密码，则修改密码（没有提交表示只修改组）
        if repwd:
            use_obj.set_password('%s' % repwd)
        # 修改组（获取用户所在的组，让这些组删除掉这个用户，重新给组加入该用户）
        try:
            AdminGroup.objects.filter(group_user=use_obj).last().group_user.remove(use_obj)
        except Exception as e:
            pass
        finally:
            group_obj.group_user.add(use_obj)
            use_obj.save()
            return JsonResponse({'stat': 1, "msg": '修改成功'})


# 显示和添加管理员
class AddUserView(LoginRequiredMixin, View):
    """显示和添加管理员"""

    @group_required('管理员模块')
    def get(self, request, page):
        group_objs = AdminGroup.objects.all()  # 展示管理员和下拉组
        users = User.objects.all().order_by('id')
        context = fenye(users, page, 5)
        for user_obj in context['pageobjs']:
            login_last = LoginRecord.objects.filter(name=user_obj.username).last()  # 最后的登录记录
            group = AdminGroup.objects.filter(group_user=user_obj).last()  # 用户所在组
            user_obj.last_time = login_last.create_time if login_last else ''  # 最后登陆的时间
            user_obj.last_ip = login_last.ip if login_last else ''  # 最后登陆ip
            user_obj.group = group.name if group else ''  # 所属管理组
            user_obj.group_id = group.id if group else ''  # 管理组id
        context["group_data"] = group_objs
        context['pms'] = request.session['munu_list']
        return render(request, 'addUser.html', context)


    @group_required('管理员模块')
    def post(self, request, page):
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        group_id = request.POST.get('groupid')
        # 判断用户名是否存在
        try:
            use_obj = User.objects.get(username=username)
        except Exception as e:
            try:
                group_obj = AdminGroup.objects.get(id=group_id)
            except Exception as e:
                return JsonResponse({"stat": 0, 'msg':'该组不存在'})
            if not pwd:
                return JsonResponse({"stat": 0, 'msg':'请输入密码'})
            # 创建用户加入职员 和 加入组
            user = User.objects.create_user(
                username=username,
                password=pwd,
                is_staff=True,
            )
            group_obj.group_user.add(user)
            return JsonResponse({"stat": 1, 'msg':'添加成功'})
        return JsonResponse({"stat": 0, 'msg':'该用户已存在'})


# 搜索管理员
class SearchAdminView(LoginRequiredMixin, View):
    """管理员搜索"""

    @group_required('管理员模块')
    def post(self, request):
        search_word = request.POST.get('search_word')
        try:
            user = User.objects.get(username=search_word)
        except Exception as e:
            return JsonResponse({"stat": 0, 'msg':'用户不存在'})
        group = AdminGroup.objects.filter(group_user=user).first()
        login_rec = LoginRecord.objects.filter(name=user.username).order_by('-id').first()
        data = {
            "stat": 1,
            "id": user.id,
            "name": user.username,
            "group": group.name if group else '',
            "last_ip": login_rec.ip if login_rec else '',
            "last_time": (login_rec.create_time + datetime.timedelta(hours=8)).strftime(
                "%Y-%m-%d %H:%M:%S") if login_rec else '',
            'group_id': group.id if group else '',
        }

        return JsonResponse(data)


# 删除用户
class DelUserView(LoginRequiredMixin, View):
    @group_required('管理员模块')
    def post(self, request):
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            return JsonResponse({"stat": 0, 'msg':'用户不存在'})
        user.delete()
        return JsonResponse({"stat": 1, 'msg':'删除成功'})


# 显示管理组
class GroupView(LoginRequiredMixin, View):
    """显示管理组"""

    @group_required('管理员模块')
    def get(self, request, page):
        groups = AdminGroup.objects.all().order_by('id')
        context = fenye(groups, page, 8)
        for i in context['pageobjs']:
            i.pmsions = [i.name for i in i.permission.all()]  # 该组的所有权限
            i.count = i.group_user.count()
        context['pms'] = request.session['munu_list']
        return render(request, 'group.html', context)


# 添加组
class AddGroupView(LoginRequiredMixin, View):
    """添加组"""
    @group_required('管理员模块')
    def post(self, request):
        groupname = request.POST.get('groupname')  # 组名
        checkbox_list = request.POST.get('checkdata')  # 多选框内容
        checkbox_data = json.loads(checkbox_list)  # 转为列表对象
        # 根据权限id获取权限对象放入列表
        pmsion_set = []
        for i in checkbox_data:
            try:
                pmsion_set.append(AdminPermission.objects.get(name=i))
            except Exception as e:
                return JsonResponse({'stat': 0, 'msg': '创建失败,权限不存在'})
        # 先判断要创建的组是否已存在
        try:
            group_obj = AdminGroup.objects.get(name=groupname)
        except Exception as e:
            # 不存在则创建组
            group = AdminGroup.objects.create(name=groupname)
            # 给该组设置权限
            group.permission.set(pmsion_set)
            return JsonResponse({"stat": 1, 'msg':'创建成功'})
        # 如果该组已经存在,则表示修改该组的权限
        group_obj.permission.set(pmsion_set)
        return JsonResponse({'stat': 1, 'msg':'修改成功'})


# 删除组
class DelGroupView(LoginRequiredMixin, View):
    """删除组"""

    @group_required('管理员模块')
    def post(self, request):
        groupname = request.POST.get('groupname')
        try:
            group_obj = AdminGroup.objects.get(name=groupname)
        except Exception as e:
            return JsonResponse({"stat": 0, 'msg':'该组不存在'})
        group_obj.delete()
        return JsonResponse({"stat": 1, 'msg':'删除成功'})


# 搜索组
class SearchGroupView(LoginRequiredMixin, View):
    """组搜索"""

    @group_required('管理员模块')
    def post(self, request):
        group_name = request.POST.get('search_word')
        try:
            group_obj = AdminGroup.objects.get(name=group_name)
        except Exception as e:
            return JsonResponse({"stat": 0, 'msg': '不存在该组'})
        pmsions = [i.name for i in group_obj.permission.all()]
        data = {
            "stat": 1,
            "id": group_obj.id,
            "name": group_obj.name,
            "count": group_obj.group_user.count(),
            "pmsions": pmsions
        }
        return JsonResponse(data)


# 管理员的派发记录搜索展示
class AduLogView(LoginRequiredMixin, View):
    @group_required('信息管理')
    def get(self, request):
        userobjs = User.objects.all()  # 下拉列表
        context= {'userobjs': userobjs}
        context['pms'] = request.session['munu_list']
        context['msg'] = ''
        context['status']=0
        return render(request, 'managelog.html',context)


# 管理员的操作记录搜索接口
class AduLogSearchView(LoginRequiredMixin, View):
    @group_required('信息管理')
    def get(self, request, page):
        startTime = request.GET.get('startTime')
        endTime = request.GET.get('endTime')
        username = request.GET.get('username')
        if username != '0':
            # 选择某个用户的记录
            records = Record.objects.filter(send_time__range=(startTime, endTime + ' 23:59:59'), operator=username)
        else:
            records = Record.objects.filter(send_time__range=(startTime, endTime + ' 23:59:59'))
        userobjs = User.objects.all()
        context = fenye(records, page, 5)
        context['status'] = 1
        context['userobjs'] = userobjs
        context['startTime'] = startTime
        context['endTime'] = endTime
        context['username'] = username
        context['pms'] = request.session['munu_list']
        return render(request, 'managelog.html', context)


# 登录记录展示页
class LoginRecView(LoginRequiredMixin, View):
    """登录记录"""

    @group_required('管理员模块')
    def get(self, request, page):
        login_recs = LoginRecord.objects.all().order_by('-create_time')
        context = fenye(login_recs, page)
        context['pms'] = request.session['munu_list']
        return render(request, 'loginRecord.html', context)


# 用户管理模块登陆记录搜索接口
class LoginRecSearchView(LoginRequiredMixin, View):
    """用户管理模块登陆记录搜索接口"""
    @group_required('管理员模块')
    def get(self, request, page):
        search_word = request.GET.get('search')
        login_recs = LoginRecord.objects.filter(name=search_word).order_by('-create_time')
        if login_recs.exists():
            context = fenye(login_recs, page)
            context['search_word'] = search_word
            context['pms'] = request.session['munu_list']
        else:
            context = {
                "msg": "没有该用户记录"
            }
            context['pms'] = request.session['munu_list']
            return render(request, 'LoginRecordSearch.html', context)
        context['pms'] = request.session['munu_list']
        return render(request, 'LoginRecordSearch.html', context)









