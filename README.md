
<div align="center">
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7ALx1D4iKXGAT3l2sO-y7HPVXJlnvE3w9ew&s" alt="AWS Logo" width="100"/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6fIAQrvvOMk4txAF4zGzX0Uyoq_NstnExSw&s" alt="Terraform Logo" width="100"/>

  <h1>IaNL: Infrastructure as Natural Language ☁️🤖</h1>
  <p><b>Why write HCL when you can just talk to your Cloud?</b></p>
</div>

---

## 📖 Overview

**IaNL (Infrastructure as Natural Language)** is an AI-powered cloud architecture agent that bridges the gap between high-level architectural thoughts and fully deployed, secure AWS environments. 

Instead of manually clicking through the AWS Console or meticulously writing HashiCorp Configuration Language (HCL) syntax, you simply describe your desired infrastructure in plain English. The IaNL Agent autonomously plans, provisions, self-heals, and manages the state lifecycle of your cloud resources using **OpenTofu/Terraform** under the hood.

## ✨ Core Capabilities

*   **🧠 Natural Language to IaC:** Converts plain English prompts into complete, multi-file Terraform modules (`main.tf`, `variables.tf`, `outputs.tf`).
*   **🔐 Strategic Self-Permissioning:** Runs pre-flight IAM checks. If it lacks necessary permissions (and is authorized to do so), it can self-bootstrap the required policies before touching infrastructure.
*   **🛠️ Autonomous Self-Healing:** If an AWS API error occurs during deployment (e.g., mismatched subnets, missing dependencies), the agent reads the `stderr`, refactors the HCL code on the fly, and seamlessly re-applies.
*   **🛡️ Secure-by-Default:** Automatically enforces AWS best practices. Routes credentials through AWS Secrets Manager, enforces KMS encryption, blocks S3 public access, and ensures least-privilege Security Groups.
*   **💾 Full State Lifecycle Management:** Powered by OpenTofu and an SQLite memory backend, the agent remembers previous sessions. You can ask it to tear down specific environments gracefully without leaving orphaned resources.

## 🏗️ Tech Stack

*   **Orchestration:** Python & LangGraph
*   **LLM Brain:** Mistral Small (via `ChatMistralAI`)
*   **IaC Engine:** OpenTofu / Terraform
*   **State Persistence:** SQLite & Local Filesystem
*   **Cloud Provider:** Amazon Web Services (AWS)

## 🚀 Example Usage

You don't write code; you start a conversation:

> **User:** *"Deploy a micro MySQL RDS instance. Generate a secure 16-character password automatically, store it in AWS Secrets Manager under the name 'db-creds', and configure the RDS instance to use that secret for its master password. "*

**What the Agent does autonomously:**
1.  Verifies AWS credentials and Region availability.
2.  Generates a 10-resource Terraform module (VPC, Subnet, IGW, Route Table, Security Group, Keys, EC2).
3.  Executes `tofu init`, `plan`, and `apply`.
4.  Intercepts and fixes any dependency or network mapping errors automatically.
5.  Saves the `.pem` file locally with secure `0400` permissions.
6.  Outputs the exact `ssh` command for you to connect.

## ⚙️ Getting Started

### Prerequisites
*   Python 3.10+
*   [OpenTofu](https://opentofu.org/) installed and added to PATH.
*   AWS CLI installed and configured.

### Installation

Install the package from PyPI:

```bash
pip install ianl-agent
```

### Configuration

Create a `.env` file in your working directory (or export variables in your shell):

```bash
MISTRAL_API_KEY="your_mistral_api_key"      # https://console.mistral.ai/
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
```

> If any of the above are missing, the CLI will prompt you securely at startup.

### Run

```bash
ianl-agent
```

To resume a previous session:

```bash
ianl-agent --session-id <your-session-id>
```

For a full list of options:

```bash
ianl-agent --help
```
