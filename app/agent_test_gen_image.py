import os
from typing import Dict, Any
from datetime import date
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import VertexAiSearchTool
import base64
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.agent_tool import AgentTool # <-- Import AgentTool
import requests
import google.genai.types as types
from dotenv import load_dotenv
import google
import vertexai
import re
import aiohttp

load_dotenv()

credentials, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

vertexai.init(project=project_id, location=os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1"))
  
# Define the Vertex AI Search Tool
vertexAiSearchTool = VertexAiSearchTool(
    search_engine_id = f"projects/{project_id}/locations/us/collections/default_collection/engines/aaa_1753711758756"
)

async def download_gcs_file(gcs_uri: str) -> bytes:
    """
    Downloads a file from a public GCS URI using HTTPS access via storage.googleapis.com.
    Assumes the GCS file is publicly accessible.
    """
    match = re.match(r"gs://([^/]+)/(.+)", gcs_uri)
    if not match:
        raise ValueError("Invalid GCS URI format")

    bucket, object_path = match.groups()
    url = f"https://storage.googleapis.com/{bucket}/{object_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to download file: {response.status}")
            return await response.read()

async def gen_image_tool_function(tool_context: ToolContext, URI: str) -> Dict[str, Any]:
    """
    Extracts a GCS image URI (gs://...) from the agent response, downloads the image, 
    saves it as an artifact in the tool context, and makes it available for downstream use.
    
    This tool supports AI agents by automating the retrieval and registration of image artifacts
    from public Google Cloud Storage links.
    Arguments:
        URI (str): The input text containing the GCS image URI to download.
    """

    uri_match = re.search(r"(gs://[^\s)]+)", URI)
    if not uri_match:
        return {"status": "error", "message": "No valid GCS URI found in input"}

    gcs_uri = uri_match.group(1)
    file_name = gcs_uri.split("/")[-1]

    try:
        image_bytes = await download_gcs_file(gcs_uri)
    except Exception as e:
        return {"status": "error", "message": f"Failed to download image: {str(e)}"}

    image_artifact = types.Part(
        inline_data=types.Blob(data=image_bytes, mime_type="image/jpeg")
    )

    artifact_version = await tool_context.save_artifact(
        filename=file_name, artifact=image_artifact
    )

    await tool_context.load_artifact(filename=file_name)

    tool_context.state["file_name"] = file_name
    tool_context.state["file_version"] = artifact_version

    return {"status": "success", "file_name": file_name, "gcs_uri": gcs_uri}


# --- Prompts (adjusted for AgentTool usage) ---

def return_instructions_root_new():
    return """
    You are a helpful assistant for employees. Your main goal is to answer their questions.

    You have two tools available:
    1. **'vertex_ai_search_sub_agent'**: Use this tool to **search for information**, like company policies, product details, or general knowledge.
       * **Important**: This tool provides text-based information only and **cannot find or generate image URLs or GCS URIs.**
    2. **'gen_image_sub_agent'**: Use this tool to **retrieve an image** from a Google Cloud Storage (GCS) URI.
       * **Important**: This tool *requires* a direct GCS URI (e.g., "gs://bucket/path/image.jpg") as input. It **cannot search for, find, or generate image URIs on its own.**

    Here's how to decide which tool to use:
    * If the user asks for **information or a general question**, use the 'vertex_ai_search_sub_agent'.
    * If the user asks for an **image AND provides a specific GCS URI**, use the 'gen_image_sub_agent' with that URI.
    * **If the user asks for an image but DOES NOT provide a GCS URI**, politely explain that you cannot find or generate images and need them to provide a GCS URI directly. **Do NOT attempt to use the search tool to find image URIs.**
    * If you cannot help, say so politely.
    """

def return_instructions_vertex_ai_search_agent():
    return """
    You are a specialized agent for searching information using Vertex AI Search.
    Your task is to answer questions by querying the configured Vertex AI Search engine and give URI link back as answer.
    """

def return_instructions_gen_image_agent():
    return """
    You are a specialized agent for retrieving images from Google Cloud Storage (GCS).
    Your task is to process GCS URIs provided as input and use the `gen_image_tool_function` to download and make the image available.
    Confirm successful image handling and provide relevant details (e.g., file name).
    If a GCS URI is not valid or processing fails, inform the calling agent.
    """

# --- Create Separate Agents for their specific tools ---

vertex_ai_search_sub_agent = Agent(
    name="vertex_ai_search_sub_agent",
    model="gemini-2.5-flash",
    description="Agent for searching information using Vertex AI Search.",
    instruction=return_instructions_vertex_ai_search_agent(),
    tools=[vertexAiSearchTool], # This agent uses the direct VertexAiSearchTool
)

gen_image_sub_agent = Agent(
    name="gen_image_sub_agent",
    model="gemini-2.5-flash",
    description="Agent for generating or retrieving images from GCS.",
    instruction=return_instructions_gen_image_agent(),
    tools=[gen_image_tool_function], # This agent uses the direct gen_image_tool_function
)

# --- Wrap sub-agents as AgentTools for the root agent (removed 'description' argument) ---

vertex_ai_search_agent_tool = AgentTool(
    agent=vertex_ai_search_sub_agent,
)

gen_image_agent_tool = AgentTool(
    agent=gen_image_sub_agent,
)


# --- Root agent now uses AgentTools ---
root_agent = Agent(
    name="linebot_agent",
    model="gemini-2.5-flash",
    description="Agent which responsible for answer the question from employee",
    instruction=return_instructions_root_new(),
    tools=[vertex_ai_search_agent_tool, gen_image_agent_tool], # Root agent uses AgentTool instances
)