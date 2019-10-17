from django.core.paginator import Paginator

from payout.settings import PAGE_NUMBERS


def fenye(objs, page, page_numbeers = PAGE_NUMBERS):
    # 分为PAGE_NUMBERS页
    paginator = Paginator(objs, page_numbeers)
    # 判断page类型
    try:
        page = int(page)
    except Exception as e:
        page = 1
    # 总页数
    num_pages = paginator.num_pages
    if page > num_pages or page < 1:
        page = 1
    # 获取第page页的内容
    pageobjs = paginator.page(page)
    # 处理页码列表
    if num_pages < 5:  # 总页数小于5显示全部
        pages = range(1, num_pages + 1)
    elif page <= 3:  # 总页数大于5,当前页小于等于3
        pages = range(1, 6)
    elif num_pages - page <= 2:  # 当前页码是最后3个页码的情况
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)
    # 组织上下文
    context = {
        'pageobjs': pageobjs,
        'pages': pages,
    }
    return context