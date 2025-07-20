import os
import asyncio
from dotenv import load_dotenv
from flask import Request, Response
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    ApiClient, 
    MessagingApi, 
    Configuration, 
    ReplyMessageRequest, 
    TextMessage,
)
from session_handler import SessionHandler

load_dotenv()
get_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
get_channel_secret = os.getenv('CHANNEL_SECRET')

configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)
BOT = SessionHandler()

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    print("Handler called!")
    try:
        asyncio.create_task(BOT.on_message_activity(event, configuration))
    except Exception as e:
        print("Exception in handle_message:", e)

def bot_webhook(request: Request) -> Response:
    if request.method == 'GET':
        return Response("Bot server is running.", status=200, mimetype="text/plain")
    elif request.method == 'POST':
        x_line_signature = request.headers.get('X-Line-Signature', None)
        body_str = request.get_data(as_text=True)
        try:
            handler.handle(body_str, x_line_signature)
        except InvalidSignatureError:
            print("Invalid Signature. Check secret or signature mismatch.")
            return Response("Invalid signature.", status=400)
        return Response('OK', status=200)
    else:
        return Response("Method not allowed", status=405, mimetype="text/plain")
    


