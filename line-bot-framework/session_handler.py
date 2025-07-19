# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    UserState,
    CardFactory,
    MessageFactory,
)
from botbuilder.schema import (
    ChannelAccount,
    HeroCard,
    Attachment,
    Activity,
    ActivityTypes,
    CardImage,
    CardAction,
    ActionTypes,
)
import os
import json
import time
from datetime import datetime, timedelta
from session_state import SessionState
from vertexai import agent_engines
import logging
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",  # <-- timestamp included here
    datefmt="%Y-%m-%d %H:%M:%S",  # Optional: custom date format
    handlers=[logging.StreamHandler()]
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger("Session_handler")


class SessionHandler(ActivityHandler):
    def __init__(self, user_state: UserState):
        if user_state is None:
            raise TypeError("[SessionHandler]: user_state is required.")

        self._user_state = user_state
        self.user_state_accessor = self._user_state.create_property("SessionState")

        self.remote_agent_engine_id = os.environ.get("REMOTE_AGENT_ENGINE_ID", "")
        

    async def get_remote_app(self):
        if not self.remote_agent_engine_id:
            raise ValueError("REMOTE_AGENT_ENGINE_ID environment variable is not set.")
        
        engine_id = self.remote_agent_engine_id.split("/")[-1]
        self.remote_app = agent_engines.get(engine_id)  

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self._user_state.save_changes(turn_context)     

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Respond to messages sent from the user.
        """
        # pretty = json.dumps(turn_context.activity.as_dict(), indent=2, ensure_ascii=False)
        # print(pretty)

        # tuen on engine
        await self.get_remote_app()

        # Get the state properties from the turn context.
        session_user_state = await self.user_state_accessor.get(
            turn_context, SessionState
        )

        # handle feedback from the user
        if turn_context.activity.reply_to_id:
            await self.recieve_feedback(turn_context, session_user_state)
        
        
        user_question = turn_context.activity.text
        if user_question:
            user_id = str(turn_context.activity.from_property.id)
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
                await self.restart_session(session_id=session_id, user_id=user_id, session_user_state=session_user_state)
                sessions = self.remote_app.list_sessions(user_id=user_id)
                session_id = sessions["sessions"][-1]["id"]
                
            if session_user_state.count_messages > 10:
                await self.restart_session(session_id=session_id, user_id=user_id, session_user_state=session_user_state)
                sessions = self.remote_app.list_sessions(user_id=user_id)
                session_id = sessions["sessions"][-1]["id"]

            else:
                for event in self.remote_app.stream_query(
                    user_id=user_id,
                    session_id=session_id,
                    message=user_question,
                ):
                    if event.get("content", None):
                        session_user_state.count_messages  += 1
                        # print(sessions)
                        # print(f"session_user_state.count_messages : {session_user_state.count_messages}")

                        await turn_context.send_activity(f"{event['content']['parts'][-1]['text']}")
                        await self._send_hero_card_feedback_options(turn_context, session_user_state, user_question, event)

                    else:
                        await turn_context.send_activity(f"Agent Engine not responding, Please Contact IT Team")
                        raise Exception(
                            f"Error: {event.get('error', 'Agent Engine not responding')}"
                        )
            
            

    async def recieve_feedback(self, turn_context: TurnContext, session_user_state: SessionState):
        """
        Handle feedback from the user.
        """
        feedback_value = turn_context.activity.value
        if isinstance(feedback_value, dict):
            feedback_type = feedback_value.get("feedback", None)
        else:
            feedback_type = None # not case feedback button

        print(f"reply_to_id: {turn_context.activity.reply_to_id}")
        strip_cache_lastest_question = session_user_state.cache_question_response.get(turn_context.activity.reply_to_id, {}).get("question", "")
        strip_cache_lastest_response = session_user_state.cache_question_response.get(turn_context.activity.reply_to_id, {}).get("response", "").replace("\n", " ").replace("\r", " ")

        if feedback_type == "Like" or feedback_type == "Dis-Like":
            logger.info(f"Question: '{strip_cache_lastest_question}', Message: '{strip_cache_lastest_response}', Got Feedback: '{feedback_type}', from user_id: '{turn_context.activity.from_property.id}'")

            # one time set feedback
            bot_session_state = await self.user_state_accessor.get(turn_context, SessionState) #session state id used for update activity later
            feedback_text = "👍 Feedback received: You liked this." if feedback_type == "Like" else "👎 Feedback received: You disliked this."
            # Replace old card with disabled one (no buttons)
            card = HeroCard(
                text=feedback_text,
                buttons=[
                    CardAction(
                    type=ActionTypes.message_back,
                    title="🔄 Restart Session",
                    value={"feedback": "Restart-session"},
                    )
                ]  # remove buttons to simulate disabled
            )

            updated_activity = Activity(
                type=ActivityTypes.message,
                id=turn_context.activity.reply_to_id,
                conversation=turn_context.activity.conversation,
                attachments=[Attachment(
                    content_type="application/vnd.microsoft.card.hero",
                    content=card
                )]
            )

            # await turn_context.update_activity(updated_activity)
            feedback_activity = await turn_context.update_activity(updated_activity) #
            bot_session_state.last_feedback_activity_id = feedback_activity.id #
        
        elif feedback_type == "Restart-session":
            # Restart session by deleting and creating a new one
            user_id = str(turn_context.activity.from_property.id)
            sessions = self.remote_app.list_sessions(user_id=user_id)
            session_id = sessions["sessions"][-1]["id"]
            await self.restart_session(session_id=session_id, user_id=user_id, session_user_state=session_user_state)


            bot_session_state = await self.user_state_accessor.get(turn_context, SessionState) #session state id used for update activity later

            empty_card = HeroCard(
                text="Session has been restarted.",
                buttons=[]
            )

            card = HeroCard(
                buttons=[
                    CardAction(
                        type=ActionTypes.message_back,
                        title="👍",
                        value={"feedback": "Like"},
                    ),
                    CardAction(
                        type=ActionTypes.message_back,
                        title="👎",
                        value={"feedback": "Dis-Like"},
                    ),
                    CardAction(
                        type=ActionTypes.message_back,
                        title="🔄 Restart Session",
                        value={"feedback": "Restart-session"},
                    )
                ]
            )

            updated_activity = Activity(
                type=ActivityTypes.message,
                id=bot_session_state.last_feedback_activity_id,
                conversation=turn_context.activity.conversation,
                attachments=[Attachment(
                    content_type="application/vnd.microsoft.card.hero",
                    content=empty_card
                )]
            )

            new_attachment = Attachment(
                content_type="application/vnd.microsoft.card.hero",
                content=card
            )

            # update last card
            # turn_context.update_activity(updated_activity)
            await turn_context.update_activity(updated_activity)
            await asyncio.sleep(0.3)

            # send new card
            await turn_context.send_activity("Session has been restarted. what would you like to ask next?." )
            new_message = MessageFactory.attachment(new_attachment)
            new_send_activity = await turn_context.send_activity(new_message) 
            bot_session_state.last_feedback_activity_id = new_send_activity.id 
            session_user_state.cache_question_response[new_send_activity.id] = {
                            "question": "",
                            "response": "Session has been restarted. what would you like to ask next?."
                        }


    async def _send_hero_card_feedback_options(self, turn_context: TurnContext, session_user_state: SessionState, user_question: str, event: dict):
        card = HeroCard(
            buttons=[
                CardAction(
                    type=ActionTypes.message_back,
                    title="👍",
                    value={"feedback": "Like"},
                ),
                CardAction(
                    type=ActionTypes.message_back,
                    title="👎",
                    value={"feedback": "Dis-Like"},
                ),
                CardAction(
                    type=ActionTypes.message_back,
                    title="🔄 Restart Session",
                    value={"feedback": "Restart-session"},
                )
            ]
        )

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.hero",
            content=card
        )

        # Send card and keep reference to update later
        message = MessageFactory.attachment(attachment)
        sent_activity = await turn_context.send_activity(message)
        session_user_state.cache_question_response[sent_activity.id] = {
            "question": user_question,
            "response": event['content']['parts'][-1]['text']
        }
        print(f"reply_to_id: {sent_activity.id}")
        print(f"question: {user_question}")
        print(f"response: {event['content']['parts'][-1]['text']}")


        # Store lastest activity ID to update later
        bot_session_state = await self.user_state_accessor.get(turn_context, SessionState)
        bot_session_state.last_feedback_activity_id = sent_activity.id
        # print(sent_activity.id)    
        # bot_session_state.sent_activity.id = sent_activity.id



    async def restart_session(self, session_id: str, user_id: str, session_user_state: SessionState):
        """
        Restart the session by deleting and creating a new one.
        """
        self.remote_app.delete_session(session_id=session_id, user_id=user_id)
        self.remote_app.create_session(user_id=user_id)
        session_user_state.count_messages = 0
        session_user_state.cache_question_response = {}

        return None
