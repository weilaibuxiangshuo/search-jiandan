# -*- coding: utf-8 -*-
# 18-11-5 下午7:02
# AUTHOR:June
import pymysql
import time

from payout.settings import DATABASES


def import_data(file, tagname):
    starttime = time.time()
    try:
        cnn = pymysql.connect(
            DATABASES["default"]["HOST"],
            DATABASES["default"]["USER"],
            DATABASES["default"]["PASSWORD"],
            DATABASES["default"]["NAME"],
            local_infile=1)
        cursor = cnn.cursor()
    except Exception as e:
        number = -1
    else:
        try:
            sql = "load data local infile '%s' " \
                  "into table major_record character set utf8mb4 " \
                  "fields terminated by ',' " \
                  "lines terminated by '\r\n' " \
                  "ignore 1 " \
                  "lines (email,tel,qq,money,name,tagname,create_time)" \
                  "set tagname='%s ', create_time=CURRENT_TIMESTAMP;" %(file,tagname,)
            number = cursor.execute(sql)
            cnn.commit()
        except Exception as e:
            print(e)
            number = 0
    alltime = time.time()-starttime
    print('==========本次耗时%s秒' %alltime)
    return number

# excel上传数据后保证send_time空值准确存入数据库
# "lines (email,tel,qq,money,name,create_time,state,@send_time,operator,lotteryclass,tagname)" \
# "set tagname='%s', lotteryclass='无', send_time= NULLif(@send_time,'');" %(file,tagname)

