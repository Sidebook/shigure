import requests
import json
import settings
import datetime

class Forecast:

    # Forecast Status
    OK = 0
    BAD_REQUEST = 1
    UNAUTHORIZED = 2
    API_LIMIT_EXCEEDED = 3
    NOT_FOUND = 4
    INTERNAL_SERVER_ERROR = 5
    READY = 6

    # probabirity level of rain
    RAIN_UNKOWN = -1
    RAIN_NEVER = 0
    RAIN_HARDLY = 1
    RAIN_MAYBE = 2
    RAIN_LIKELY = 3
    RAIN_ALMOST = 4
    RAIN_THRESHOLDS = [
        settings.POP_THRESHOLD_HARDLY,
        settings.POP_THRESHOLD_MAYBE,
        settings.POP_THRESHOLD_LIKELY,
        settings.POP_THRESHOLD_ALMOST
    ]

    def __init__(self,
        status=READY,
        pop=None,
        time_start=None,
        time_end=None,
        latitude=0,
        longitude=0
        ):
        self.status = status
        self.pop = pop
        if pop is None:
            self.pop = []
        self.time_start = time_start
        self.time_end = time_end
        self.latitude = latitude
        self.longitude = longitude
        self.rain_level = Forecast.RAIN_UNKOWN
        self.rain_begin_time = None
        
    def __str__(self):
        status = [
            'OK',
            'Bad Request',
            'Unauthorized',
            'API Limit Exceeded',
            'Not Found',
            'Internal Server Error',
            'Ready']
        
        levels = [
            'Never',
            'Hardly',
            'Maybe',
            'Likely',
            'Almost',
            'Unknown'
        ]

        s = 'request status: {}\n' \
            'location: {}, {}\n' \
            'time(start): {}\n' \
            'time(end): {}\n' \
            'PoP: {}\n' \
            'rain level: {}\n' \
            'rain begin time: {}\n'.format(
                status[self.status],
                self.latitude,
                self.longitude,
                self.time_start,
                self.time_end,
                self.pop,
                levels[self.rain_level],
                self.rain_begin_time
            )

        return s

    def get(self, latitude, longitude, length=settings.FORECAST_LENGTH):
        self.latitude = latitude
        self.longitude = longitude
        url = settings.WEATHER_ENDPOINT.format(
            username=settings.WEATHER_USERNAME,
            password=settings.WEATHER_PASSWORD,
            latitude=latitude,
            longitude=longitude)
        payload = {
            'language': 'en-US',
            'units': 'm'
        }
        responce = requests.get(url, params=payload)
        status = responce.status_code

        if (status == 400):
            # HTTP 400 Bad Request
            self.status = Forecast.BAD_REQUEST
        elif (status == 401):
            # HTTP 401 Unauthorized
            self.status = Forecast.UNAUTHORIZED
        elif (status == 403):
            # HTTP 403 Forbidden Request
            self.status = Forecast.API_LIMIT_EXCEEDED
        elif (status == 404):
            # HTTP 404 Not Found
            self.status = Forecast.NOT_FOUND
        elif (status == 500):
            # HTTP 500 Internal Server Error
            self.status = Forecast.INTERNAL_SERVER_ERROR
        elif (status == 200):
            # HTTP 200 OK
            self.status = Forecast.OK

            # get json from responce
            js = responce.json()
            forecasts = js['forecasts']

            # set time
            length = max(min(len(forecasts), length), 2)
            self.time_start = forecasts[0]['fcst_valid_local']
            self.time_end = forecasts[length - 1]['fcst_valid_local']

            # set PoP
            pop = []
            for f in forecasts[0:length]:
                pop.append(f['pop'])
            self.pop = pop

            # set rain level
            max_pop = max(pop)
            level = 0
            for t in Forecast.RAIN_THRESHOLDS:
                if(max_pop < t):
                    break
                level += 1
            self.rain_level = level
            
            # set rain begin time
            level = min(Forecast.RAIN_LIKELY, self.rain_level)
            if level >= Forecast.RAIN_HARDLY:
                threshold = Forecast.RAIN_THRESHOLDS[level - 1]
                hour = 0
                for pop in self.pop:
                    if (pop > threshold):
                        break
                    hour += 1
                self.rain_begin_time = hour
            

class Responce:

    GREETING = 0
    HELP = 1
    UNKOWN_LOCATION = 2
    NEED_UMBRELLA = 3
    NOT_NEED_UMBRELLA = 4
    INTERNAL_ERROR = 5

    def __init__(self, message='',status=GREETING):
        self.message = message
        self.staus = status
    
    def __str__(self):
        return self.message

def responce(message, latitude=None, longitude=None):
    r = Responce()
    if '傘いる' in message:
        print('responce mode: forecast')
        if latitude is None or longitude is None:
            return Responce(
                message='まずあなたの居る場所を教えてください',
                status=Responce.UNKOWN_LOCATION
            )
        if '明日' in message:
            return Responce(
                message='明日の天気はわかりません',
                status=Responce.NOT_NEED_UMBRELLA
            )
        else:
            f = Forecast()
            f.get(latitude, longitude)
            print(f)
            
            if (f.status != Forecast.OK):
                return Responce(
                    message='すいません...\nなにか問題が発生していてお答えできません...',
                    status=Responce.INTERNAL_ERROR
                )
            
            s = ''
            status = Responce.NEED_UMBRELLA
            if f.rain_level == Forecast.RAIN_NEVER:
                s = '今日は傘は必要ありません'
                status = Responce.NOT_NEED_UMBRELLA
            elif f.rain_level == Forecast.RAIN_HARDLY:
                s = '今日はおそらく傘は必要ありません'
                status = Responce.NOT_NEED_UMBRELLA
            elif f.rain_level == Forecast.RAIN_MAYBE:
                s = '{}時間後に雨が降るかもしれませんので、傘が必要かもしれません。'.format(
                    f.rain_begin_time
                )
            elif f.rain_level == Forecast.RAIN_LIKELY:
                s = '{}時間後に雨が降る可能性が高いので、傘が必要です。'.format(
                    f.rain_begin_time
                )
            elif f.rain_level == Forecast.RAIN_ALMOST:
                s = '{}時間後に雨が高確率で降るので、傘が必要です。'.format(
                    f.rain_begin_time
                )
            
            return Responce(
                message=s,
                status=status
            )
    elif 'ヘルプ' in message:
        return Responce(
            message='今、傘がいるかどうか知りたい場合「傘いる？」'\
            '特定の時刻で傘が必要な場合に通知させたい場合「通知 7:00」'\
            '位置情報を設定または設定し直したい場合、位置情報を送信してください',
            status=Responce.HELP
        )
    else:
        return Responce(
            message='今日、傘がいるかどうか教えます！\n「傘いる？」と聞いてください。\n' \
            '最初に使う時は、あなたの住んでいる場所を送ってください！\n' \
            'また、特定の時間に傘がいるかどうか通知するよう設定することも可能です。\n' \
            '詳細を知りたい場合は「ヘルプ」と入力してください。',
            status=Responce.GREETING
            )

if __name__ == '__main__':
    while True:
        r = responce(input('>> '),latitude=38.27, longitude=140.85)
        print(r)
