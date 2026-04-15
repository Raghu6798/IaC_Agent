import asyncio
import click
import os

from config.settings import settings

from utils.logger import log
from utils.ui import print_welcome_banner, console, show_success, show_error
from rich.panel import Panel
from rich.prompt import Prompt

def setup_api_keys():
    """
    Handles the setup for Mistral API keys and AWS credentials.
    Checks environment variables first, then prompts the user if a key is missing.
    """
    # Sync settings to os environ if loaded from .env
    if settings.MISTRAL_API_KEY and not os.getenv("MISTRAL_API_KEY"):
        os.environ["MISTRAL_API_KEY"] = settings.MISTRAL_API_KEY
    if settings.AWS_ACCESS_KEY_ID and not os.getenv("AWS_ACCESS_KEY_ID"):
        os.environ["AWS_ACCESS_KEY_ID"] = settings.AWS_ACCESS_KEY_ID
    if settings.AWS_SECRET_ACCESS_KEY and not os.getenv("AWS_SECRET_ACCESS_KEY"):
        os.environ["AWS_SECRET_ACCESS_KEY"] = settings.AWS_SECRET_ACCESS_KEY

    # --- Handle Mistral API Key ---
    if not os.getenv("MISTRAL_API_KEY"):
        console.print(
            Panel.fit(
                "[bold]🔑 Mistral API Key Required[/bold]\n\n"
                "IaNL uses Mistral AI for intelligence. Please provide your API key.\n"
                "(get yours at https://console.mistral.ai/)",
                border_style="cyan"
            )
        )
        mistral_api_key = Prompt.ask(
            "🔑 [bold green]Paste your Mistral API key[/bold green]", password=True
        )
        os.environ["MISTRAL_API_KEY"] = mistral_api_key
        settings.MISTRAL_API_KEY = mistral_api_key
        show_success("Mistral API key validated and set for this session.")
    else:
        show_success("Mistral API key found in environment variables.")

    # --- Handle AWS Credentials ---
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        console.print(
            Panel.fit(
                "[bold]☁️ AWS Credentials Required[/bold]\n\n"
                "IaNL needs AWS credentials to provision your infrastructure.",
                border_style="orange1"
            )
        )
        if not os.getenv("AWS_ACCESS_KEY_ID"):
            aws_access_key = Prompt.ask(
                "☁️ [bold yellow]Paste your AWS Access Key ID[/bold yellow]", password=True
            )
            os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
            settings.AWS_ACCESS_KEY_ID = aws_access_key
            
        if not os.getenv("AWS_SECRET_ACCESS_KEY"):
            aws_secret_key = Prompt.ask(
                "☁️ [bold yellow]Paste your AWS Secret Access Key[/bold yellow]", password=True
            )
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
            settings.AWS_SECRET_ACCESS_KEY = aws_secret_key
            
        show_success("AWS credentials set for this session.")
    else:
        show_success("AWS credentials found in environment variables.")


EPILOG = """
\b
ENVIRONMENT VARIABLES

  The following variables can be set in a .env file or exported in your shell
  to avoid being prompted on every run:

  MISTRAL_API_KEY          API key for the Mistral LLM backend (required)
  AWS_ACCESS_KEY_ID        AWS credentials used to provision resources (required)
  AWS_SECRET_ACCESS_KEY    AWS credentials used to provision resources (required)

\b
EXAMPLES

  # Start a new interactive session (credentials read from .env)
  $ ianl-agent

  # Resume a previous conversation by its session ID
  $ ianl-agent --session-id abc123

  # Pass credentials inline via env vars (CI / scripted use)
  $ MISTRAL_API_KEY=sk-... AWS_ACCESS_KEY_ID=AKI... AWS_SECRET_ACCESS_KEY=... ianl-agent

\b
DOCS & SOURCE

  PyPI   https://pypi.org/project/ianl-agent/
"""


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=EPILOG,
)
@click.option(
    "--session-id",
    default=None,
    metavar="ID",
    show_default=True,
    help=(
        "Resume an existing conversation checkpoint. "
        "When omitted a new session is created automatically. "
        "Session IDs are printed at the start of each run."
    ),
)
def main(session_id: str):
    """IaNL — Infrastructure as Natural Language (v0.1.8)

    \b
    Provision and manage AWS infrastructure using plain English.
    The agent translates your instructions into OpenTofu / Terraform
    plans, reviews them with you, and applies them — no HCL required.

    \b
    On first run you will be prompted for any credentials not already
    present in your environment or .env file. Subsequent runs skip
    the prompts automatically.
    """

    setup_api_keys()

    print_welcome_banner()

    from agent.graph import run_IaNL_agent
    asyncio.run(run_IaNL_agent(thread_id=session_id))


if __name__ == "__main__":
    main()
