import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

# Apply nest_asyncio to allow nested event loops (needed for Jupyter/IPython)
nest_asyncio.apply()

# Load environment variables
load_dotenv(".env")

# Global variables to store session state
session = None
exit_stack = AsyncExitStack()
openai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
)

# price
# model = "google/gemini-2.0-flash-001"
# model = "qwen/qwen3-32b"
# model = "qwen/qwen-turbo"
# model = "deepseek/deepseek-chat-v3-0324"
# model = "deepseek/deepseek-chat"
# model = "meta-llama/llama-3.3-70b-instruct"
# model = "nvidia/llama-3.1-nemotron-70b-instruct"
# model = "qwen/qwen-2.5-72b-instruct"
# model = "openai/gpt-4o-mini"

# free
model = "mistralai/mistral-7b-instruct:free"

stdio = None
write = None


async def connect_to_server(server_script_path: str = "server.py"):
    """Connect to an MCP server.

    Args:
        server_script_path: Path to the server script.
    """
    global session, stdio, write, exit_stack

    # Server configuration
    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
    )

    # Connect to the server
    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))

    # Initialize the connection
    await session.initialize()

    # List available tools
    tools_result = await session.list_tools()
    print("\nConnected to server with tools:")
    for tool in tools_result.tools:
        print(f"  - {tool.name}: {tool.description}")


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Get available tools from the MCP server in OpenAI format.

    Returns:
        A list of tools in OpenAI format.
    """
    global session

    tools_result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools_result.tools
    ]


async def process_query(query: str) -> str:
    global session, openai_client, model

    # Get available tools
    tools = await get_mcp_tools()
    print(f"Tools sent to model: {json.dumps(tools, indent=2)}")

    # Initial OpenAI API call
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )
        print(f"API Response: {response}")
    except Exception as e:
        print(f"API Error: {e}")
        return "Error occurred while calling API"

    # Get assistant's response
    assistant_message = response.choices[0].message
    print(f"\nAssistant message: {assistant_message}")

    # Initialize conversation
    messages = [
        {"role": "user", "content": query},
        assistant_message,
    ]

    # Handle tool calls if present
    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            print(f"\nCalling function: {tool_call.function.name}")
            result = await session.call_tool(
                tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments),
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result.content[0].text,
                }
            )

        print(f"\nfinal_message: {messages}")
        final_response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="none",
        )
        print(f"\nfinal_response: {final_response}")
        return final_response.choices[0].message.content

    return assistant_message.content


async def cleanup():
    """Clean up resources."""
    global exit_stack
    await exit_stack.aclose()


async def main():
    """Main entry point for the client."""
    await connect_to_server("server.py")

    query = "Generate a welcome message for Chorn in login context"
    # query = "นโยบายวันหยุดพักร้อนของบริษัทเราคืออะไร?"
    # query = "What is our company's vacation policy"
    print(f"\nQuery: {query}")

    response = await process_query(query)
    print(f"\nResponse: {response}")

    await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
