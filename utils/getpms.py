from apps.userapp.models import *
def getpms(request):
    pms_name_list = []  # 查询集
    if request.user.is_superuser:
        pms_name_list = [i.name for i in AdminPermission.objects.all()]
    group_objs = AdminGroup.objects.filter(group_user=request.user)  # 用户所在的组
    for i in group_objs:
        for p in i.permission.all():
            pms_name_list.append(p.name)
    pms_list = list(set(pms_name_list))
    return pms_list