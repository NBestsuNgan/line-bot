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
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",  # <-- timestamp included here
    datefmt="%Y-%m-%d %H:%M:%S",  # Optional: custom date format
    handlers=[logging.StreamHandler()]
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger("Session_handler")


def get_secret_value(secret_name, default=None):
    """Try reading from a mounted file, fallback to env variable."""
    secret_path = f"/secrets/{secret_name}"
    if os.path.exists(secret_path):  # For Cloud Run with Secret Manager
        with open(secret_path, "r") as f:
            return f.read().strip()
    return os.getenv(secret_name, default)  # Fallback to env variable

get_access_token = get_secret_value('CHANNEL_ACCESS_TOKEN')
get_channel_secret = get_secret_value('CHANNEL_SECRET')

configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)
BOT = SessionHandler()

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    print("Handler called!")
    logger.info("Handler called!")
    try:
        asyncio.run(BOT.on_message_activity(event, configuration))
    except Exception as e:
        print("Exception in handle_message:", e)

def bot_webhook(request: Request) -> Response:
    if request.method == 'GET':
        return Response("Bot server is running.", status=200, mimetype="text/plain")
    elif request.method == 'POST':
        logger.info("reach post call")
        x_line_signature = request.headers.get('X-Line-Signature', None)
        body_str = request.get_data(as_text=True)
        try:
            handler.handle(body_str, x_line_signature)
            logger.info("reach Handler called!")
        except InvalidSignatureError:
            print("Invalid Signature. Check secret or signature mismatch.")
            return Response("Invalid signature.", status=400)
        return Response('OK', status=200)
    else:
        return Response("Method not allowed", status=405, mimetype="text/plain")
    


