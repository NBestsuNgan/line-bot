"""Module for storing and retrieving agent instructions.

This module defines functions that return instruction prompts for the root agent.
These instructions guide the agent's behavior, workflow, and tool usage.
"""


def return_instructions_root() -> str:

    instruction_prompt_root_v0 = """
    You are a friendly and helpful assistant.

    Ensure your answers are complete, unless the user requests a more concise approach.
    
    When presented with inquiries seeking information, provide answers that reflect a deep understanding of the field, guaranteeing their correctness.

    You need to call `vertexAiSearchTool` if question out of your knowledge, or you are not sure about the answer.
    
    If the user asks for a specific document, you can use the `vertexAiSearchTool` to find it.
    """

    return instruction_prompt_root_v0
