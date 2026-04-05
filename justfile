


# 1. Start the OpenShell Gateway
gateway:
	@echo "🟢 Starting OpenShell Gateway..."
	openshell gateway start

# 2. Configure the Provider and Inference Routing
# The '-' before the provider command tells Just to ignore the error if the provider already exists
setup-llm:
	@echo "⚙️  Configuring local inference provider..."
	-openshell provider create --name {{PROVIDER_NAME}} --type openai --credential OPENAI_API_KEY=dummy --config OPENAI_BASE_URL={{BASE_URL}}
	@echo "🔀 Setting inference route..."
	openshell inference set --provider {{PROVIDER_NAME}} --model "{{MODEL_PATH}}" --no-verify

# 3. Start a fresh interactive sandbox
interact: gateway setup-llm
	@echo "🛡️  Dropping into a fresh OpenShell sandbox..."
	openshell sandbox create

# 4. (Alternative) Upload your current directory and launch an AI Agent (e.g., OpenCode)
agent: gateway setup-llm
	@echo "🤖 Syncing files and launching OpenCode agent..."
	openshell sandbox create --upload -- opencode

# 5. Clean up / Tear down everything
destroy:
	@echo "💥 Destroying OpenShell gateway and all data..."
	openshell gateway destroy

# 6. Activate the virtual environment
activate:
	source /mnt/c/Users/Raghu/Downloads/IAC_Agent/iac_agent/.venv/bin/activate