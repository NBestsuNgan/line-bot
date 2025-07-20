# GCS Utility
from google.cloud import storage
import json
import os
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

from typing import Optional

GCS_BUCKET = "my-bucket"
GCS_PREFIX = "sessions"


class SessionState:
    def __init__(self, event: MessageEvent, user_id=None, session_count=0, cache_question_response = dict()):
        self.event = event
        self.user_id = user_id if user_id is not None else event.message.id
        self.session_count = session_count
        self.cache_question_response = dict()

    def get_gcs_client(self):
        return storage.Client()

    async def get_session_blob(self, user_id):
        client = self.get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"{GCS_PREFIX}/{user_id}.json")
        return blob

    async def load_session(self):
        blob = await self.get_session_blob(self.user_id)
        if blob.exists():
            data = json.loads(blob.download_as_text())
            self.user_id = data.get("user_id", self.user_id)
            self.session_count = data.get("session_count", 0)
        else:
            data = {
                "user_id": self.user_id,
                "session_count": 0
            }
            await self.save_session(self.user_id, data)
            self.session_count = 0
        return self

    async def save_session(self, user_id, session_dict) -> Optional[str]:
        blob = await self.get_session_blob(user_id)
        blob.upload_from_string(json.dumps(session_dict), content_type="application/json")
