import os
import json
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(
    name="Knowledge Base",
    host="0.0.0.0",  # only used for SSE transport (localhost)
    port=8050,  # only used for SSE transport (set this to any port)
)


@mcp.tool()
def get_knowledge_base() -> str:
    """
    Answers questions about company policies and procedures such as vacation, 
    remote work, expenses, software, and security protocols by querying the knowledge base.

    Returns:
        A formatted string containing all Q&A pairs from the knowledge base.
    """
    try:
        kb_path = os.path.join(os.path.dirname(__file__), "data", "kb.json")
        with open(kb_path, "r") as f:
            kb_data = json.load(f)

        # Format the knowledge base as a string
        kb_text = "Here is the retrieved knowledge base:\n\n"

        if isinstance(kb_data, list):
            for i, item in enumerate(kb_data, 1):
                if isinstance(item, dict):
                    question = item.get("question", "Unknown question")
                    answer = item.get("answer", "Unknown answer")
                else:
                    question = f"Item {i}"
                    answer = str(item)

                kb_text += f"Q{i}: {question}\n"
                kb_text += f"A{i}: {answer}\n\n"
        else:
            kb_text += f"Knowledge base content: {json.dumps(kb_data, indent=2)}\n\n"

        return kb_text
    except FileNotFoundError:
        return "Error: Knowledge base file not found"
    except json.JSONDecodeError:
        return "Error: Invalid JSON in knowledge base file"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def generate_welcome_message(user_name: str, context: str = "general") -> str:
    """
    Generate a personalized welcome message based on user name and context.

    Args:
        user_name (str): The name of the user to include in the message.
        context (str): The context of the greeting, e.g., 'login', 'event', or 'general'.

    Returns:
        str: A customized welcome message tailored to the user and context.

    Examples:
        >>> generate_welcome_message("Alice", "login")
        'Welcome back, Alice! Ready to dive into your MCP dashboard?'
        >>> generate_welcome_message("Bob", "event")
        'Hello Bob! Excited to see you at the MCP event today!'
    """
    if not user_name:
        return "Hello! Please provide a name for a personalized greeting."

    context = context.lower()
    if context == "login":
        return f"Welcome back, {user_name}! Ready to dive into your MCP dashboard?"
    elif context == "event":
        return f"Hello {user_name}! Excited to see you at the MCP event today!"
    elif context == "support":
        return f"Hi {user_name}, the MCP support team is here to assist you!"
    else:
        return f"Greetings, {user_name}! Welcome to the MCP server!"


# Run the server
if __name__ == "__main__":
    print("Server is running.")
    mcp.run(transport="stdio")

