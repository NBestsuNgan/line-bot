# Need to perform only context recognition

import os
import json
import time
from datetime import datetime, timedelta
from session_state import SessionState
from vertexai import agent_engines
import logging
import asyncio
from abc import ABC, abstractmethod
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


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",  # <-- timestamp included here
    datefmt="%Y-%m-%d %H:%M:%S",  # Optional: custom date format
    handlers=[logging.StreamHandler()]
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger("Session_handler")


# session management class
class SessionHandler():
    def __init__(self):
        self._userState = None
        self._sessionState = None
        self._remote_agent_engine_id = os.environ.get("REMOTE_AGENT_ENGINE_ID", "")
                
    async def get_remote_app(self):
        if not self._remote_agent_engine_id:
            raise ValueError("REMOTE_AGENT_ENGINE_ID environment variable is not set.")
        
        engine_id = self._remote_agent_engine_id.split("/")[-1]
        self.remote_app = agent_engines.get(engine_id)  

 
    async def on_message_activity(self, lineEvent: MessageEvent, configuration: Configuration):
        logger.info("entering on_message_activity successfully")
        # turn on engine
        await self.get_remote_app()

        # fetch session meta data | 1..user_id 2.session_count
        self._sessionState = SessionState(lineEvent)
        self._userState = await self._sessionState.load_session()

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            # Agent engine management
            user_question = lineEvent.message.text
            if user_question:
                user_id = self._userState.user_id
                sessions = self.remote_app.list_sessions(user_id=user_id)

                # if not have sessions, create one
                if len(sessions["sessions"]) == 0:
                    # print("REASON: Session does not exist, creating a new session...")
                    self.remote_app.create_session(user_id=user_id)
                    sessions = self.remote_app.list_sessions(user_id=user_id)


                # get existsing session id
                session_id = sessions["sessions"][-1]["id"]

                # perform date check
                lastUpdateTime = sessions["sessions"][-1]["lastUpdateTime"]
                seconds_since_last_update = time.time() - lastUpdateTime
                days_since_last_update = seconds_since_last_update / (60 * 60 * 24)

                if days_since_last_update > 1:
                    # print("REASON: Session is older than 1 day, creating a new session...")
                    await self.restart_session(session_id=session_id, user_id=user_id, session_user_state=self._sessionState)
                    sessions = self.remote_app.list_sessions(user_id=user_id)
                    session_id = sessions["sessions"][-1]["id"]
                    
                if self._userState.session_count > 5:
                    await self.restart_session(session_id=session_id, user_id=user_id, session_user_state=self._sessionState)
                    sessions = self.remote_app.list_sessions(user_id=user_id)
                    session_id = sessions["sessions"][-1]["id"]

                else:
                    for engineEvent in self.remote_app.stream_query(
                        user_id=user_id,
                        session_id=session_id,
                        message=user_question,
                    ):
                        if engineEvent.get("content", None):
                            self._userState.session_count  += 1
                            await self._sessionState.save_session(user_id, {
                                "user_id": user_id,
                                "session_count": self._userState.session_count
                            })
                            # print(sessions)
                            # print(f"session_user_state.count_messages : {session_user_state.count_messages}")
                            line_bot_api.reply_message(
                                ReplyMessageRequest(
                                    reply_token=lineEvent.reply_token,
                                    messages=[TextMessage(text=f"{engineEvent['content']['parts'][-1]['text']}")]
                                )
                            )
                            logger.info(f"Question: '{user_question}', Answer: '{engineEvent['content']['parts'][-1]['text']}', from user_id: '{user_id}'")

                        else:
                            line_bot_api.reply_message(
                                ReplyMessageRequest(
                                    reply_token=lineEvent.reply_token,
                                    messages=[TextMessage(text='Agent Engine not responding, Please Contact IT Team')]
                                )
                            )
                            raise Exception(
                                f"Error: {engineEvent.get('error', 'Agent Engine not responding')}"
                            )
            

    async def restart_session(self, session_id: str, user_id: str, session_user_state: SessionState):
        """
        Restart the session by deleting and creating a new one.
        """
        # agent engine restart
        self.remote_app.delete_session(session_id=session_id, user_id=user_id)
        self.remote_app.create_session(user_id=user_id)

        # line bot session restart
        self._userState.session_count = 0
        session_user_state.cache_question_response = {}

        return None
