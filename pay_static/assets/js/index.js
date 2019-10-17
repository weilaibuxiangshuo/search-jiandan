


// 增加管理组
$(document).on('click','.add-adgroup-btn',function () {
    $(this).hide();
    $('.addgroup').show();
});

// 增加管理组 提交
$(document).on('click','.addgroup .subBtnstl',function () {
    $('.addgroup').hide();
    $('.add-adgroup-btn').show();
});

// 时间input
$(function(){
    var DATAPICKERAPI = {
        // 默认input显示当前月,自己获取后填充
        activeMonthRange: function () {
            return {
                begin: moment().set({ 'date': 1, 'hour': 0, 'minute': 0, 'second': 0 }).format('YYYY-MM-DD HH:mm:ss'),
                end: moment().set({ 'hour': 23, 'minute': 59, 'second': 59 }).format('YYYY-MM-DD HH:mm:ss')
            }
        },
        shortcutMonth: function () {
            // 当月
            var nowDay = moment().get('date');
            var prevMonthFirstDay = moment().subtract(1, 'months').set({ 'date': 1 });
            var prevMonthDay = moment().diff(prevMonthFirstDay, 'days');
            return {
                now: '-' + nowDay + ',0',
                prev: '-' + prevMonthDay + ',-' + nowDay
            }
        },
        // 注意为函数：快捷选项option:只能同一个月份内的
        rangeMonthShortcutOption1: function () {
            var result = DATAPICKERAPI.shortcutMonth();
            return [{
                name: '昨天',
                day: '-1,-1',
                time: '00:00:00,23:59:59'
            }, {
                name: '这一月',
                day: result.now,
                time: '00:00:00,'
            }, {
                name: '上一月',
                day: result.prev,
                time: '00:00:00,23:59:59'
            }];
        },
        // 快捷选项option
        rangeShortcutOption1: [{
            name: '最近一周',
            day: '-7,0'
        }, {
            name: '最近一个月',
            day: '-30,0'
        }, {
            name: '最近三个月',
            day: '-90, 0'
        }],
        singleShortcutOptions1: [{
            name: '今天',
            day: '0'
        }, {
            name: '昨天',
            day: '-1',
            time: '00:00:00'
        }, {
            name: '一周前',
            day: '-7'
        }]
    };
    //年月日单个
    $('.J-datepicker-day').datePicker({
        hasShortcut: true,
        format:'YYYY-MM-DD',
        shortcutOptions: [{
            name: '今天',
            day: '0'
        }, {
            name: '昨天',
            day: '-1'
        }, {
            name: '一周前',
            day: '-7'
        }]
    });
});

// $(document).on('click','.first-nav>li',function () {
//     $(this).siblings().find('[data-toggle="in"]').length;
//     console.log($('.first-nav').siblings().find('div[data-toggle="collapse in"]').length)
//     console.log($(this).siblings().find('div[data-toggle="collapse in"]').length)
// })
