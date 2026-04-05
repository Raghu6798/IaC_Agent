import asyncio
import click
from utils.logger import log
from utils.ui import print_welcome_banner
from config import settings
from agent.graph import run_IaNL_agent

@click.command()
@click.option("--session-id", default=None, help="The session ID to use for the conversation.")
def main(session_id: str):
    """Entry point for IaNL (Infrastructure as Natural Language)."""
    
    # Credentials are automatically handled by settings if .env is present
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
