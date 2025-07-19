import sys
import traceback
import asyncio
import json
from datetime import datetime

import functions_framework
from flask import Request, Response
from botbuilder.core import (
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes
import os
from dotenv import load_dotenv

load_dotenv()
from session_handler import SessionHandler 

class DefaultConfig:
    PORT = 3978
    APP_ID = os.environ.get("APP_ID", "")
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
    APP_TYPE = "SingleTenant"
    APP_TENANTID = os.environ.get("APP_TENANTID", "")

CONFIG = DefaultConfig()

# Create adapter with proper authentication
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

# Create MemoryStorage, UserState
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)

# Create the Bot
BOT = SessionHandler(USER_STATE)


# Error handler
async def on_error(context: TurnContext, error: Exception):
    """Error handler for the bot adapter."""
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    
    if context.activity.channel_id == "emulator":
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error


class MockAiohttpRequest:
    """Mock aiohttp request object for Flask compatibility."""
    
    def __init__(self, flask_request: Request):
        self.flask_request = flask_request
        self._body = None
        self._headers = None
        
    @property
    def headers(self):
        if self._headers is None:
            self._headers = dict(self.flask_request.headers)
            
            # Use X-Forwarded-Authorization as Authorization for Bot Framework
            if 'X-Forwarded-Authorization' in self._headers:
                self._headers['Authorization'] = self._headers['X-Forwarded-Authorization']
            
        return self._headers
    
    @property
    def method(self):
        return self.flask_request.method
    
    @property 
    def url(self):
        return self.flask_request.url
        
    async def json(self):
        if self._body is None:
            self._body = self.flask_request.get_json()
        return self._body
    
    async def text(self):
        return self.flask_request.get_data(as_text=True)


async def process_bot_activity(flask_request: Request):
    try:
        mock_request = MockAiohttpRequest(flask_request)

        await ADAPTER.process(mock_request, BOT)

        return json.dumps({"status": "ok"}), 200

    except Exception as e:
        print(f"Error processing bot activity: {e}", file=sys.stderr)
        traceback.print_exc()
        return json.dumps({"error": str(e)}), 500


@functions_framework.http
def bot_webhook(request: Request) -> Response:
    """
    Main Cloud Function entry point for bot messages.
    """

    if request.method == 'GET':
        # Health check endpoint
        return Response(
            response="Bot server is running.",
            status=200,
            mimetype="text/plain"
        )
    
    elif request.method == 'POST':
        try:
            # Process the bot request asynchronously using the proper adapter
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                body, status_code = loop.run_until_complete(
                    process_bot_activity(request)
                )
                
                return Response(
                    response=body,
                    status=status_code,
                    mimetype="application/json"
                )
            finally:
                loop.close()
                
        except Exception as e:
            print(f"Error in bot_webhook: {e}", file=sys.stderr)
            traceback.print_exc()
            return Response(
                response=json.dumps({"error": "Internal server error"}),
                status=500,
                mimetype="application/json"
            )
    
    else:
        return Response(
            response=json.dumps({"error": "Method not allowed"}),
            status=405,
            mimetype="application/json"
        )