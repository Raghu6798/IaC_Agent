import asyncio
import click


from config.settings import settings
from agent.graph import run_IaNL_agent

from utils.logger import log
from utils.ui import print_welcome_banner

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

    if not settings.MISTRAL_API_KEY:
        mistral_key = click.prompt(
            "Enter Mistral API Key (get yours at https://console.mistral.ai/)",
            hide_input=True,
        )
        settings.MISTRAL_API_KEY = mistral_key

    if not settings.AWS_ACCESS_KEY_ID:
        aws_access = click.prompt("Enter AWS Access Key ID", hide_input=True)
        settings.AWS_ACCESS_KEY_ID = aws_access

    if not settings.AWS_SECRET_ACCESS_KEY:
        aws_secret = click.prompt("Enter AWS Secret Access Key", hide_input=True)
        settings.AWS_SECRET_ACCESS_KEY = aws_secret

    print_welcome_banner()

    asyncio.run(run_IaNL_agent(thread_id=session_id))


if __name__ == "__main__":
    main()
