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

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

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

# 获取今日的星期
def get_today_week():
    week_list = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六', '7':'天'}
    today_week = datetime.today().weekday()
    today_week = str(today_week)
    week_day = '星期' + week_list[today_week]
    return week_day


# 朋友圈文案 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
    words = requests.get("https://api.shadiao.pro/pyq")
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
