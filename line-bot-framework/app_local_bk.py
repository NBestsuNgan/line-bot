# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
 
import sys
import os
import traceback
from datetime import datetime
from http import HTTPStatus
 
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes
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
 
# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to line
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
 
    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)
 
 
ADAPTER.on_turn_error = on_error
 
# Create MemoryStorage, UserState
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
 
# Create the Bot
BOT = SessionHandler(USER_STATE)
 
 
# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:
    # print(req.headers)
    # print(await req.text())
    return await ADAPTER.process(req, BOT)
 
 
APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)
 
async def index(req: Request) -> Response:
    return web.Response(text="Bot server is running.", content_type="text/plain")
 
APP.router.add_get("/", index)
 
 
if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error