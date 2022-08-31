from datetime import datetime, timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d")  # 今天的日期

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
birthday = os.getenv('BIRTHDAY')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')
period = os.getenv('TEST_F')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')

if app_id is None or app_secret is None:
    print('请设置 APP_ID 和 APP_SECRET')
    exit(422)

if not user_ids:
    print('请设置 USER_ID，若存在多个 ID 用回车分开')
    exit(422)

if template_id is None:
    print('请设置 TEMPLATE_ID')
    exit(422)


# weather 直接返回对象，在使用的地方用字段进行调用。
def get_weather():
    if city is None:
        print('请设置城市')
        return None
    url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    result = requests.get(url).json()
    if result is None:
        return None
    weather_info = result['data']['list'][0]
    return weather_info


# 纪念日正数
def get_memorial_days_count():
    if start_date is None:
        print('没有设置 START_DATE')
        return 0
    delta = today - datetime.strptime(start_date, "%Y-%m-%d")
    return delta.days


# 生日倒计时
def get_birthday_left():
    if birthday is None:
        print('没有设置 BIRTHDAY')
        return 0
    next_time = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
    if next_time < nowtime:
        next_time = next_time.replace(year=next_time.year + 1)
    return (next_time - today).days


# 生理期倒计时
def get_period_left():
    print(period)
    if period is None:
        print('没有设置 PERIOD')
        return 0
    next_time = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d")
    next_time_period = (datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d") + timedelta(days=7))
    if next_time < nowtime < next_time_period:
        words_reply = "今天是小馋猫例假来的第{0}天".format((today - next_time).days + 1)
        return words_reply
    else:
        next_time = next_time.replace(year=next_time.year + 1)
        words_reply = "距离小馋猫的例假来临还有{0}天".format((next_time - today).days + 1)
        return words_reply


# 获取今日的星期
def get_today_week():
    week_list = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六', '7':'天'}
    today_week = datetime.today().weekday()
    today_week = str(today_week)
    week_day = '星期' + week_list[today_week]
    return week_day


# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    return words.json()['data']['text']


def format_temperature(temperature):
    return math.floor(temperature)


# 随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

wm = WeChatMessage(client)
weather = get_weather()
if weather is None:
    print('获取天气失败')
    exit(422)
data = {
    "city": {
        "value": city,
        "color": get_random_color()
    },
    "date": {
        "value": today.strftime('%Y年%m月%d日'),
        "color": get_random_color()
    },
    "week_day": {
        "value": get_today_week(),
        "color": get_random_color()
    },
    "weather": {
        "value": weather['weather'],
        "color": get_random_color()
    },
    "temperature": {
        "value": math.floor(weather['temp']),
        "color": get_random_color()
    },
    'humidity': {
        "value": weather['humidity'],
        "color": get_random_color()
    },
    "highest": {
        "value": math.floor(weather['high']),
        "color": get_random_color()
    },
    "lowest": {
        "value": math.floor(weather['low']),
        "color": get_random_color()
    },
    "air_quality": {
        "value": weather['airQuality'],
        "color": get_random_color()
    },
    "air_data": {
        "value": weather['airData'],
        "color": get_random_color()
    },
    "wind": {
        "value": weather['wind'],
        "color": get_random_color()
    },
    "love_days": {
        "value": get_memorial_days_count(),
        "color": get_random_color()
    },
    "birthday_left": {
        "value": get_birthday_left(),
        "color": get_random_color()
    },
    "period":{
        "value": get_period_left(),
        "color": get_random_color()
    },
    "words": {
        "value": get_words(),
        "color": get_random_color()
    },
}

if __name__ == '__main__':
    count = 0
    try:
        for user_id in user_ids:
            res = wm.send_template(user_id, template_id, data)
            count += 1
    except WeChatClientException as e:
        print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
        exit(502)

    print("发送了" + str(count) + "条消息")
