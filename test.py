import os
import subprocess
import threading
from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated, Dict, Any, Optional, Union, Sequence, Callable, Type, Tuple
import requests
import json
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool, tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.output_parsers.openai_tools import parse_tool_calls

from rich.console import Console,Group
from rich.tree import Tree
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt

console = Console()

def show_success(msg):
    console.print(Panel(f"[green]✅ {msg}", title="Success", style="green"))


def show_error(msg):
    console.print(Panel(f"[red]❌ {msg}", title="Error", style="red"))


def show_info(msg):
    console.print(f"[cyan]{msg}[/cyan]")


@tool 
def run_shell_commands(command: str, cwd: str = None, timeout: int = 60) -> str:
    """
    Executes a shell command, streams and logs output/errors, and returns the combined logs as a string.
    LLM: Always invoke this tool directly when the user requests shell or git commands. Do NOT ask for permission or confirmation from the user.
    Args:
        command (str): The shell command to execute.
        cwd (str, optional): The working directory to run the command in.
        timeout (int, optional): Maximum time to wait for the command (seconds).
    Returns:
        str: Combined output and error logs.
    """
    try:
        show_info(f"Running shell command: {command} in {cwd or os.getcwd()}")
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        logs = []

        def read_logs():
            for line in process.stdout:
                if "ERROR" in line or "Traceback" in line:
                    show_error(line.rstrip())
                elif "CRITICAL" in line:
                    show_error(line.rstrip())
                elif "WARNING" in line:
                    show_info(line.rstrip())
                elif "DEBUG" in line:
                    show_info(line.rstrip())
                else:
                    show_info(line.rstrip())
                logs.append(line)

        t = threading.Thread(target=read_logs)
        t.start()
        t.join(timeout=timeout)
        process.terminate()
        process.wait()
        show_info(f"Shell command execution completed: {command}")
        return "".join(logs)
    except Exception as e:
        show_error(f"Exception occurred while running shell command '{command}': {e}")
        return f"Exception occurred while running shell command '{command}': {e}"

class ChatQwen(BaseChatModel):
    """LangChain wrapper for a local OpenAI-compatible server with full tool support."""
    base_url: str = "http://127.0.0.1:8080"
    model_name: str = "Qwen3.5-4B"
    temperature: float = 0.1

    @property
    def _llm_type(self) -> str: return "Qwen3.5-4B"
    def _send_request(self, messages: List[BaseMessage], **kwargs: Any) -> Dict[str, Any]:
        processed_messages = []
        for m in messages:
            if isinstance(m, SystemMessage): processed_messages.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage): processed_messages.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                msg_dict = {"role": "assistant", "content": m.content or ""}
                if m.tool_calls:
                    msg_dict["tool_calls"] = [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])}} for tc in m.tool_calls]
                processed_messages.append(msg_dict)
            elif isinstance(m, ToolMessage): processed_messages.append({"role": "tool", "content": m.content, "tool_call_id": m.tool_call_id})
            else: raise TypeError(f"Unsupported message type: {type(m)}")
        payload = {"model": self.model_name, "messages": processed_messages, "temperature": self.temperature, **kwargs}
        if "tools" in payload and payload["tools"] is None: del payload["tools"]
        response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        resp_json = self._send_request(messages, **kwargs)
        message_data = resp_json["choices"][0]["message"]
        content = message_data.get("content", "") or ""
        tool_calls = parse_tool_calls(message_data["tool_calls"]) if message_data.get("tool_calls") else []
        ai_message = AIMessage(content=content, tool_calls=tool_calls)
        return ChatResult(generations=[ChatGeneration(message=ai_message)])
    def bind_tools(self, tools: Sequence[Union[Dict, Type[BaseModel], Callable, BaseTool]], **kwargs: Any) -> Runnable:
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        return self.bind(tools=formatted_tools, **kwargs)
    def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any):
        raise NotImplementedError("Async generation not implemented for local model.")

if __name__ == "__main__":
    model = ChatQwen()
    agent = create_agent(
        model=model,
        tools=[run_shell_commands],
        system_prompt="You are a helpful assistant who can run shell commands",
    )
    resp = agent.invoke({"messages": [HumanMessage(content="run a series of 5 bash commands , can be anything general basic commands")]})
    print(resp["messages"][-1].content)
