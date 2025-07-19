import json
import logging
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.api_core.exceptions import NotFound
import pandas

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)




def list_engines(resource_id: str) -> None:
    remote_session = agent_engines.get(resource_id)

    print("Created session:")
    print(f"  Session ID: {remote_session}")
    print(f"  Session ID: {remote_session['id']}")
    print(f"  User ID: {remote_session['user_id']}")
    print(f"  App name: {remote_session['app_name']}")
    print(f"  Last update time: {remote_session['last_update_time']}")
    print("\nUse this session ID with --session_id when sending messages.")

def list_deployments() -> None:
    """Lists all deployments."""
    deployments = agent_engines.list()
    if not deployments:
        print("No deployments found.")
        return
    print("Deployments:")
    for deployment in deployments:
        print(f"- {deployment.resource_name}")

def create_session(resource_id: str, user_id: str) -> None:
    """Creates a new session for the specified user."""
    remote_app = agent_engines.get(resource_id)
    remote_session = remote_app.create_session(user_id=user_id)
    # remote_session = asyncio.run(remote_app.create_session(user_id="test_user"))

    print("Created session:")
    print(f"  Session ID: {remote_session['id']}")
    print(f"  User ID: {remote_session['user_id']}")
    print(f"  App name: {remote_session['app_name']}")
    print(f"  Last update time: {remote_session['last_update_time']}")
    print("\nUse this session ID with --session_id when sending messages.")

def list_sessions(resource_id: str, user_id: str) -> None:
    """Lists all sessions for the specified user."""
    remote_app = agent_engines.get(resource_id)
    sessions = remote_app.list_sessions(user_id=user_id)
    print(f"Sessions for user '{user_id}':")
    for session in sessions:
        print(f"- Session ID: {session['id']}")


def communication(resource_id: str, user_id: str, session_id: str) -> None:
    remote_app = agent_engines.get(resource_id)
    # session = remote_app.create_session(user_id=user_id)
    # for event in remote_app.stream_query(
    #     user_id=user_id,
    #     session_id=session_id,
    #     message="how can i requests for a pay splip?",
    # ):
    #     if event.get("content", None):
    #         print(
    #             f"Agent deployed successfully under resource name: {remote_app.resource_name}"
    #         )
    #         print(f"event : {event}")

    print("Sending query...")

    for event in remote_app.stream_query( #stream_query
        user_id=user_id,
        message="hi?",
        session_id=session_id,
    ):
        print("Received event:", event)

    print("Query complete")


if __name__ == "__main__":
    config_file = "deployment_metadata.json"

    with open(config_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    remote_agent_engine_id = metadata.get("remote_agent_engine_id")
    deployment_timestamp = metadata.get("deployment_timestamp")

    create_session(remote_agent_engine_id, "test_user")
    # communication(remote_agent_engine_id, "test_user", "7674552129213693952")
  

  
   
    