import re
import base64
import json
import os
import time
import click
import asyncio
import threading
from functools import lru_cache, cached_property, partial
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from typing_extensions import override, AsyncContextManager, Self

from openshell.sandbox import SandboxClient, SandboxError
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.layout import Layout
from rich.live import Live

from mistralai.client import Mistral
from memvid_sdk import use

from deepagents import create_deep_agent
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.backends.sandbox import BaseSandbox
from deepagents.backends.protocol import ExecuteResponse, FileUploadResponse, FileDownloadResponse
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.store import StoreBackend

from langchain_core.tools import tool

from core.llm import ChatQwen
from utils.ui import print_welcome_banner, show_info, print_agent_response
from tools.shell_tools import run_shell_commands
from tools.file_tools import inspect_a_file,write_code,refactoring_code
from config.settings import settings
from langchain_mistralai import ChatMistralAI
from langchain_cerebras import ChatCerebras
from dotenv import load_dotenv

load_dotenv()

# Thread pool for blocking I/O operations
io_executor = ThreadPoolExecutor(max_workers=4)

# Thread-safe pixtral client singleton
_pixtral_lock = threading.Lock()
pixtral = None

@lru_cache(maxsize=1)
def _get_pixtral():
    global pixtral
    if pixtral is None:
        with _pixtral_lock:
            # Double check inside the lock
            if pixtral is None:
                pixtral = Mistral(
                    api_key=settings.MISTRAL_API_KEY,
                )
    return pixtral

@tool 
async def encode_image(image_path: str) -> str:
    """Encode an image to base64."""
    loop = asyncio.get_running_loop()
    
    def _read_and_encode():
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
            
    # Run blocking file read in ThreadPoolExecutor
    image_strings = await loop.run_in_executor(io_executor, _read_and_encode)

    vision_language_input =  [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_strings}"
                }
            ]
        }
    ]
    
    def _call_api():
        client = _get_pixtral()
        return client.chat.completions.create(
            model="mistral-small-latest",
            messages=vision_language_input,
        )
        
    # Run blocking API call in ThreadPoolExecutor
    vision_resp = await loop.run_in_executor(io_executor, _call_api)
    return vision_resp.choices[0].message.content

SYSTEM_PROMPT = """You are an expert Infrastructure-as-Natural-Language (IaNL) Architect and DevOps Engineer. Your primary role is to assist users in creating, managing, updating, and documenting AWS infrastructure using Terraform.



### CAPABILITIES & TOOLS
You have the following tools at your disposal. Use them strategically to accomplish your tasks:
1. `run_shell_commands(commands: list[str]) -> str`: Execute AWS CLI commands, Terraform commands (`terraform init`, `plan`, `apply`), and standard Unix shell commands.
2. `read_file(path: str) -> str`: Read the complete contents of configuration files (like `.tf`, JSON, or YAML files).
3. `inspect_a_file(path: str) -> str`: Inspect file structures or specific sections of a file.
4. `write_file(code: str, file_path: str) -> str`: Write Terraform (`.tf`), scripts, or state files to disk.
5. `encode_image(image_path: str) -> str`: Transcribe visual AWS Architecture diagrams into text using a Vision-Language Model.

### STANDARD WORKFLOW
When given a user request, you MUST strictly adhere to the following workflow:

**Phase 1: Verification & Context**
- Always begin by verifying your AWS access and identity using `run_shell_commands` with commands like `aws sts get-caller-identity`. 
- If the user provides a path to an AWS architecture diagram, use `encode_image` to parse the visual components into a textual specification before writing any code.
- Ensure you understand the current state of the infrastructure natively by checking if `.tf` files exist using `run_shell_commands` or `read_file`.

**Phase 2: Execution & Provisioning**
- Write clean, modern, and production-ready Terraform code using `write_file`. Follow best practices (use variables, outputs, and modular structure where appropriate).
- Run `terraform init` and `terraform plan` via `run_shell_commands` to validate the code.
- Report the results of the plan to the user clearly. You should wait for their confirmation unless they explicitly provide an -auto-approve instruction.

### RULES & CONSTRAINTS
- NEVER guess resource names, regions, or IDs. Use the AWS CLI to query resources to find exact identifiers (`aws ec2 describe-vpcs`, `aws ec2 describe-subnets`, etc.).
- Handle problems gracefully. If a Terraform plan fails, read the exact error message from the shell output, correct the `.tf` file using `write_file`, and retry the plan.
- Ensure IAM policies follow the principle of least privilege. 

You are rigorous, precise, and highly capable of independent problem solving.
"""

class OpenShellBackend(BaseSandbox, AsyncContextManager):
    def __init__(self, sandbox_name: str):
        self.sandbox_name = sandbox_name
        self.client = None
        self.session = None

    def _init_sandbox(self):
        self.client = SandboxClient.from_active_cluster()
        try:
            self.session = self.client.get_session(self.sandbox_name)
        except Exception:
            self.session = self.client.create_session()
            self.client.wait_ready(self.session.sandbox.name)

    # Async Context Manager implementation
    async def __aenter__(self) -> Self:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(io_executor, self._init_sandbox)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await asyncio.get_running_loop().run_in_executor(io_executor, self.client.close)

    @property
    def id(self) -> str:
        return self.session.sandbox.name if self.session else ""

    @override
    def execute(self, command: str) -> ExecuteResponse:
        """
        Required by BaseSandbox. 
        All file operations in BaseSandbox will now route through this!
        """
        try:
            # We use /bin/bash -c for compatibility
            cmd_list = ["/bin/bash", "-c", command]
            result = self.session.exec(cmd_list)

            return ExecuteResponse(
                output=result.stdout + result.stderr,
                exit_code=result.exit_code
            )
        except SandboxError as e:
            return ExecuteResponse(output=str(e), exit_code=-1)

    @override
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Native OpenShell upload implementation."""
        return [self.client.upload_file(self.id, path, content) for path, content in files]

    @override
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Native OpenShell download implementation."""
        return [self.client.download_file(self.id, path) for path in paths]

    @property
    def status(self):
        return self.client.get_session(self.id).sandbox.phase if self.client else "unknown"

    @cached_property
    def base_os(self):
        """Cache the base OS call properly to an instance-property instead of a method"""
        return self.execute("cat /etc/os-release").stdout
        
    def close(self):
        if self.client:
            self.client.close()

def create_hybrid_backend(runtime, sandbox_backend):
    # The StoreBackend uses Postgres to persist memories
    memory_backend = StoreBackend(
        runtime=runtime, 
        namespace=lambda ctx: ("ianl_agent_memory",)
    )

    return CompositeBackend(
        default=sandbox_backend,
        routes={
            "/memories/": memory_backend
        }
    )

async def async_main():
    if not settings.AWS_ACCESS_KEY_ID:
        aws_access = click.prompt("Enter AWS Access Key ID", hide_input=True)
        settings.AWS_ACCESS_KEY_ID = aws_access

    if not settings.AWS_SECRET_ACCESS_KEY:
        aws_secret = click.prompt("Enter AWS Secret Access Key", hide_input=True)
        settings.AWS_SECRET_ACCESS_KEY = aws_secret

    print_welcome_banner()
    query_history = deque(maxlen=10)
    
    console = Console()
    
    loop = asyncio.get_running_loop()
  
    # Use Async Context Manager for OpenShellBackend setup
    async with OpenShellBackend(sandbox_name="sterling-hake") as sandbox_backend:
        mistral_small_4 = ChatMistralAI(
            model="mistral-small-latest",
            api_key=settings.MISTRAL_API_KEY,
        )
        
        agent = create_deep_agent(
            model=mistral_small_4,
            backend=partial(create_hybrid_backend, sandbox_backend=sandbox_backend),
            tools = [encode_image,inspect_a_file,write_code,refactoring_code] + mem_tools,
            system_prompt=SYSTEM_PROMPT
        )
        
        while True:
            # use thread executor so user input doesn't block other tasks
            query = await loop.run_in_executor(io_executor, lambda: console.input("\n[bold green]➜[/bold green] [bold white]Enter your query:[/bold white] "))
            if query.lower() in ["exit", "quit"]:
                break
                
            query_history.append(query)
            
            full_content = ""

            def get_renderable(content: str, generating: bool = True):
                status = " [bold pulse yellow]● Generating...[/]" if generating else " [bold green]● Done[/]"
                return Panel(
                    Markdown(content) if content else "...",
                    title=f"[bold cyan]IaNL[/bold cyan]{status}",
                    border_style="cyan",
                    expand=True,
                    padding=(1, 2)
                )
            
            with Live(get_renderable(full_content), console=console, refresh_per_second=12, transient=False) as live:
                live.update(get_renderable(full_content))
                
            
                async for chunk in agent.astream({"messages": [{"role": "user", "content": query}]}, stream_mode="messages", version="v2"):
                    if chunk["type"] == "messages":
                        token, metadata = chunk["data"]
                        if token.content:
                            full_content += token.content
                            live.update(get_renderable(full_content))
                
                live.update(get_renderable(full_content, generating=False))

@click.command()
def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
