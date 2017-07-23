from __future__ import unicode_literals

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage,
)

import shigurecore
import json
import atexit

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

user_settings = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:

        ## recieved message event
        if not isinstance(event, MessageEvent):
            continue

        user_id = event.source.user_id
        message = event.message
        print('recieved message from {}'.format(user_id))

        ## recieved text message
        if isinstance(message, TextMessage):
            latitude = None
            longitude = None
            if user_id in user_settings:
                latitude = user_settings[user_id]['latitude']
                longitude = user_settings[user_id]['longitude']
            r = shigurecore.responce(message.text, latitude=latitude, longitude=longitude)
            text = r.message
            if r.staus == shigurecore.Responce.UNKOWN_LOCATION:
                text += '\n+マークから「位置情報」を選択して位置情報を設定してください！'

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=text)
            )

        ## recieved location message
        if isinstance(message, LocationMessage):
            add_user_setting(user_id, latitude=message.latitude, longitude=message.longitude)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='位置情報を設定しました！')
            )

    return 'OK'

def add_user_setting(user_id, latitude=None, longitude=None, schedule=None):
    setting = {}
    if not user_id:
        return

    already_exists = user_id in user_settings
    overwrite_latitude = False
    overwrite_longitude = False
    overwrite_schedule = False

    if latitude is not None:
        if already_exists:
            overwrite_latitude = 'latitude' in user_settings[user_id]
        setting['latitude'] = latitude
    
    if longitude is not None:
        if already_exists:
            overwrite_longitude = 'longitude' in user_settings[user_id]
        setting['longitude'] = longitude
    
    if schedule is not None:
        if already_exists:
            overwrite_schedule = 'schedule' in user_settings[user_id]
        setting['schedule'] = schedule
    
    user_settings[user_id] = setting

    if already_exists:
        print ('overwrited user setting [{}]: latitude: {}{} longitude: {}{} schedule: {}{}'.format(
            user_id,
            latitude,
            '(overwrite)' if overwrite_latitude else '',
            longitude,
            '(overwrite)' if overwrite_longitude else '',
            schedule,
            '(overwrite)' if overwrite_schedule else '',
        ))
    else:
        print ('added user setting [{}]: latitude: {} longitude: {} schedule: {}'.format(
            user_id,
            latitude,
            longitude,
            schedule
        ))
    
    print(json.dumps(user_settings, indent=2))

def load_user_settings():
    with open('usersettings.json') as f:
        user_settings = json.load(f)
    print('loaded user settings.')

def save_user_settings():
    with open('usersettings.json', 'w') as f:
        json.dump(user_settings, f, indent=4)
    print('saved user settings.')

load_user_settings()
atexit.register(save_user_settings)

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()


    app.run(debug=options.debug, port=options.port)