import os
import uvicorn

from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Header

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, MessageContent
from aiohttp import web

from linebot.v3.messaging import (
    ApiClient, 
    MessagingApi, 
    Configuration, 
    ReplyMessageRequest, 
    TextMessage, 
    # FlexMessage, 
    # Emoji,
)
# start app
app = FastAPI()

# set configure
load_dotenv()
from .session_handler import SessionHandler 
get_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
get_channel_secret = os.getenv('CHANNEL_SECRET')


# def get_secret_value(secret_name, default=None):
#     """Try reading from a mounted file, fallback to env variable."""
#     secret_path = f"/secrets/{secret_name}"
#     if os.path.exists(secret_path):  # For Cloud Run with Secret Manager
#         with open(secret_path, "r") as f:
#             return f.read().strip()
#     return os.getenv(secret_name, default)  # Fallback to env variable

# get_access_token = get_secret_value('CHANNEL_ACCESS_TOKEN')
# get_channel_secret = get_secret_value('CHANNEL_SECRET')

# Initial configure
configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)

# passing requests to callbacl function and perform token validation
@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        print("Invalid Signature. Check secret or signature mismatch.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'

# Start sessiongandler class for context management
BOT = SessionHandler()

# passing requests to backend server for only TEXT message type
@handler.add(MessageEvent, message=MessageContent)
async def handle_message(event: MessageEvent):
    # BOT is act as sessionhandler + sessionstate
    await BOT.on_message_activity(event, configuration)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")