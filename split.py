import os
import re

with open("main.py.bak", "r", encoding="utf-8") as f:
    text = f.read()

def extract_block(text, pattern_start, pattern_end=None):
    if pattern_end:
        pattern = f"(?s)({pattern_start}.*?{pattern_end})"
    else:
        pattern = f"(?s)({pattern_start}.*?\n\n)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""

# 1. Config
os.makedirs("config", exist_ok=True)
with open("config/__init__.py", "w", encoding="utf-8") as f:
    f.write("from .settings import settings\n")

with open("config/settings.py", "w", encoding="utf-8") as f:
    f.write("""from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # AWS configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Gemini
    GOOGLE_API_KEY: Optional[str] = None
    
    # Local LLM config
    LLM_BASE_URL: str = "http://127.0.0.1:8080"
    LLM_MODEL_NAME: str = "Qwen3.5-4B"
    LLM_TEMPERATURE: float = 0.1

    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.prod'), 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

settings = Settings()
""")

# 2. Extract logger
os.makedirs("utils", exist_ok=True)
with open("utils/__init__.py", "w", encoding="utf-8") as f:
    f.write("")

with open("utils/logger.py", "w", encoding="utf-8") as f:
    f.write("""import sys
from loguru import logger

def setup_logger():
    logger.remove()

    FORMAT = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<blue>{process}</blue>:<blue>{thread}</blue> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
        format=FORMAT
    )
    return logger

log = setup_logger()
""")

# Extract prompt
prompt_match = re.search(r'(SYSTEM_PROMPT\s*=\s*\"\"\"[\s\S]*?\"\"\")', text)
prompt = prompt_match.group(1) if prompt_match else "SYSTEM_PROMPT = ''"

os.makedirs("core", exist_ok=True)
with open("core/__init__.py", "w", encoding="utf-8") as f:
    f.write("")
with open("core/prompts.py", "w", encoding="utf-8") as f:
    f.write(prompt + "\n")

# Extract ChatQwen
qwen_match = re.search(r'(class ChatQwen\(BaseChatModel\):[\s\S]*?)gemini =', text)
qwen_class = qwen_match.group(1) if qwen_match else ""

with open("core/llm.py", "w", encoding="utf-8") as f:
    f.write("""import json
import requests
from typing import List, Optional, Any, Sequence, Union, Callable, Type, Dict
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.output_parsers.openai_tools import parse_tool_calls
from config import settings

""" + qwen_class.replace("self.base_url", "settings.LLM_BASE_URL").replace("self.model_name", "settings.LLM_MODEL_NAME").replace("self.temperature", "settings.LLM_TEMPERATURE") + "\n")

# Extract UI
ui_match = re.search(r'(def show_code[\s\S]*?def print_agent_response[^:]*:[\s\S]*?\)[\n\s]+)\nSYSTEM_PROMPT', text)
ui_funcs = ui_match.group(1) if ui_match else ""

with open("utils/ui.py", "w", encoding="utf-8") as f:
    f.write("""from rich.console import Console, Group
from rich.tree import Tree
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text

console = Console()

""" + ui_funcs)

# Extract Tools
img_tools = re.search(r'(@tool \ndef read_image[\s\S]*?)def print_welcome_banner', text)
file_tools = re.search(r'(@tool\ndef inspect_a_file[\s\S]*?return f"File .*?written successfully.")', text)
shell_tools = re.search(r'(@tool\ndef run_shell_commands[\s\S]*?command\D*: \{e\}")', text)

os.makedirs("tools", exist_ok=True)
with open("tools/__init__.py", "w", encoding="utf-8") as f:
    f.write("")

with open("tools/file_tools.py", "w", encoding="utf-8") as f:
    f.write("""import base64
import os
from pathlib import Path
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

gemini = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, api_key=settings.GOOGLE_API_KEY)

""" + (img_tools.group(1) if img_tools else "") + "\n")
    f.write((file_tools.group(1) if file_tools else "") + "\n")

with open("tools/shell_tools.py", "w", encoding="utf-8") as f:
    f.write("""import subprocess
import threading
import os
from langchain_core.tools import tool
from utils.ui import show_info, show_error

""" + (shell_tools.group(1) if shell_tools else "") + "\n")
    
# Persistent powershell
shell_match = re.search(r'(class PersistentPowerShell:[\s\S]*?ps = PersistentPowerShell\(\)\n)', text)
with open("utils/shell.py", "w", encoding="utf-8") as f:
    f.write("""import subprocess
import threading

""" + (shell_match.group(1) if shell_match else "") + "\n")
    
# Agent
agent_match = re.search(r'(class AgentState[\s\S]*?logger\.exception.*?\n)', text)
os.makedirs("agent", exist_ok=True)
with open("agent/__init__.py", "w", encoding="utf-8") as f:
    f.write("")

with open("agent/graph.py", "w", encoding="utf-8") as f:
    f.write("""import uuid
import input
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode
from utils.logger import log
from utils.ui import print_agent_response
from core.prompts import SYSTEM_PROMPT
from core.llm import ChatQwen
from tools.file_tools import read_image, inspect_a_file, write_file
from tools.shell_tools import run_shell_commands

""" + (agent_match.group(1) if agent_match else "").replace("logger.exception", "log.exception") + "\n")

# New main.py
with open("main.py", "w", encoding="utf-8") as f:
    f.write("""import asyncio
import click
from utils.logger import log
from utils.ui import print_welcome_banner
from config import settings
from agent.graph import run_IAC_agent

@click.command()
def main():
    \"\"\"Entry point for the IAC Agent.\"\"\"
    
    # Credentials are automatically handled by settings if .env is present
    if not settings.AWS_ACCESS_KEY_ID:
        aws_access = click.prompt("Enter AWS Access Key ID", hide_input=True)
        settings.AWS_ACCESS_KEY_ID = aws_access

    if not settings.AWS_SECRET_ACCESS_KEY:
        aws_secret = click.prompt("Enter AWS Secret Access Key", hide_input=True)
        settings.AWS_SECRET_ACCESS_KEY = aws_secret

    print_welcome_banner()
    
    asyncio.run(run_IAC_agent())

if __name__ == "__main__":
    main()
""")

print("Successfully modularized.")
