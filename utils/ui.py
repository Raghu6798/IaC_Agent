from rich.console import Console, Group
from rich.tree import Tree
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text

console = Console()

def show_code(code: str, lang: str = "python"):
    syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
    console.print(syntax)

def print_welcome_banner():
    banner_text = Text(
"""██╗ █████╗  ██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗
██║██╔══██╗██╔════╝     ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██║███████║██║          ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║██╔══██║██║          ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║██║  ██║╚██████╗     ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝╚═╝  ╚═╝ ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝""",
style="#93C572"
)
    welcome_message = Markdown(
"""
### Welcome to IaC Agent
This tool combines AI-powered cloud architecture analysis with secure, production-grade 
Infrastructure-as-Code generation — right from your terminal.

---
### Key Capabilities:

*   **Architecture Analysis:** Feed in an AWS architecture diagram and get fully structured 
    Terraform code generated automatically — covering compute, storage, networking, streaming, 
    and observability layers.
*   **Security-First Code Generation:** Every provisioned resource follows hardened defaults — 
    KMS encryption, S3 public access blocks, restricted Security Groups, and zero hardcoded secrets.
*   **Secrets Manager Integration:** Passwords for RDS, Redshift, MSK, ElastiCache, and any 
    credential-bearing service are auto-generated via the `random` provider and stored securely 
    in AWS Secrets Manager — never in plaintext.
*   **IAM Pre-flight Checks:** Before touching your cloud, the agent discovers existing roles, 
    simulates IAM permissions, and surfaces any `AccessDeniedException` gaps with a ready-to-attach 
    remediation policy — before `tofu apply` ever runs.
*   **OpenTofu Lifecycle Management:** Runs the full `init -> plan -> show -> apply` pipeline, 
    parses errors intelligently, and halts with a clear diagnosis instead of retrying blindly.
*   **Post-Apply Validation:** Automatically verifies that Secrets Manager secrets, KMS keys, 
    CloudWatch log groups, and provisioned services are live and correctly configured after apply.
*   **Filesystem & File Operations:** Reads architecture images, writes `.tf` files, and 
    inspects your codebase directly.

---
### How to Use:
Simply describe your architecture or paste a path to your diagram. Examples:

- `generate terraform for this architecture -> /path/to/aws_diagram.png`
- `check if my IAM identity has permissions to provision Kinesis and Redshift`
- `what secrets were created after the last apply?`
- `show me the plan for the current IaC directory`
- `validate the KMS keys and log groups from the last deployment`

---
### Security Checklist (auto-enforced on every run):
  [x]  No hardcoded passwords, tokens, or Account IDs  
  [x]  All secrets routed through AWS Secrets Manager  
  [x]  KMS encryption on S3, RDS, Redshift, CloudWatch Logs  
  [x]  IAM roles discovered before creation — least-privilege enforced  
  [x]  Permission gaps surfaced before `tofu apply` — never after  
  [x]  Security Groups default to deny — no `0.0.0.0/0` ingress  
"""
)
    panel_content = Group(banner_text, welcome_message)
    panel = Panel(
        panel_content,
        title="[bold orange1] IAC Agent  [/bold orange1]  [dim]v0.1.0[/dim] ",
        subtitle="[orange1]AI-Powered Dev Assistant[/orange1]",
        border_style="orange1",
        width=140,
        expand=True,
        padding=(2, 2),
    )
    console.print(panel)

def show_success(msg):
    console.print(Panel(f"[green]✅ {msg}", title="Success", style="green"))


def show_error(msg):
    console.print(Panel(f"[red]❌ {msg}", title="Error", style="red"))


def show_info(msg):
    console.print(f"[cyan]{msg}[/cyan]")

def print_agent_response(text, title: str = "Iac Agent"):
    """Display agent output inside a Rich panel box with orange color"""
    if isinstance(text, list):
        text_parts = []
        for part in text:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        text = "\\n".join(text_parts)
    elif not isinstance(text, str):
        text = str(text)

    console.print(
        Panel.fit(
            Markdown(text),
            title=f"[bold orange1]{title}[/bold orange1]",
            border_style="orange1",
        )
    )
