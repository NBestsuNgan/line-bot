import os
from typing import Dict, Any
from datetime import date
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import VertexAiSearchTool
import base64
from google.adk.tools.tool_context import ToolContext
from .prompts import return_instructions_root
import requests
import google.genai.types as types
from dotenv import load_dotenv
import google
import vertexai

load_dotenv()

credentials, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

vertexai.init(project=project_id, location=os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1"))
  
vertexAiSearchTool = VertexAiSearchTool(
    search_engine_id = f"projects/{project_id}/locations/us/collections/default_collection/engines/linebot-search-engine"
)

root_agent = Agent(
    name="linebot_agent",
    model="gemini-2.5-flash",
    description="Agent which responsible for answer the question from employee",
    instruction=return_instructions_root(),
    tools=[vertexAiSearchTool]
)