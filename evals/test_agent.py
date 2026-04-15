import os 
import uuid 
import pytest
import asyncio
from langchain_mistralai import ChatMistralAI

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode 

from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams,ToolCall
from deepeval.metrics import ( 
    GEval,
    TaskCompletionMetric,
    ToolCorrectnessMetric,
    StepEfficiencyMetric
)
from deepeval.models import DeepEvalBaseLLM

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

from core.prompts import SYSTEM_PROMPT
from agent.graph import AgentState
from tools.file_tools import read_image,inspect_a_file,refactoring_code,write_code
from tools.shell_tools import run_shell_commands

from config.settings import settings

memory = MemorySaver()



mistral_small_4 = ChatMistralAI(
    model="mistral-small-latest",
    api_key=settings.MISTRAL_API_KEY
)

tools = [run_shell_commands,read_image,inspect_a_file,refactoring_code,write_code]
model = mistral_small_4
model_with_tools = model.bind_tools(tools)

class MistralLLM(DeepEvalBaseLLM):
    def __init__(self, model):
        self.model = model
        # deepeval expects name to be set
        self.name = "Mistral Small Latest"

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return self.name

mistral_llm = MistralLLM(model=mistral_small_4)

task_completion = TaskCompletionMetric(threshold=0.7, strict_mode=True, model=mistral_llm)
tool_correctness = ToolCorrectnessMetric(threshold=0.7, model=mistral_llm)
step_efficiency = StepEfficiencyMetric(threshold=0.7, model=mistral_llm)

async def call_model(state: AgentState):
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
                    
    response = await model_with_tools.ainvoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

builder = StateGraph(AgentState)
builder.add_node("llm", call_model)
builder.add_node("tools", tool_node)
builder.add_edge(START, "llm")

builder.add_conditional_edges(
    "llm",
    lambda state: "tools" if state["messages"][-1].tool_calls else END,
)

builder.add_edge("tools", "llm")


async def ask_agent_programmatically(query: str, thread_id: str = "test-session") -> str:

    agent_executor = builder.compile(checkpointer=memory)
    full_response = ""
    
    async for chunk in agent_executor.astream(
        {"messages": [{"role": "user", "content": query}]}, 
        config={"configurable": {"thread_id": thread_id}}, 
        stream_mode="messages"
    ):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            token, metadata = chunk
            if metadata.get("langgraph_node") == "llm" and hasattr(token, "content"):
                if isinstance(token.content, str) and token.content:
                    full_response += token.content
                    
    final_state = await agent_executor.aget_state(config={"configurable": {"thread_id": thread_id}})
    all_messages = final_state.values.get("messages", [])
    expected_tool_calls = []
    for msg in all_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for t_call in msg.tool_calls:
                    expected_tool_calls.append({
                        "name": t_call["name"],
                        "args": t_call["args"] 
                    })
    return full_response,expected_tool_calls




security_compliance_metric = GEval(
    name="Terraform Security Posture",
    model=mistral_llm,
    criteria=(
        "You are an expert AWS security auditor grading Terraform code. "
        "Review the actual_output and ensure it meets these security rules: "
        "1. NO AdministratorAccess: Look at the generated code. If it DOES NOT contain the string 'AdministratorAccess', it PASSES this check. Do not expect verbal confirmation. "
        "2. NO Wildcards: The IAM policies must NOT contain '*' for Actions or Resources. "
        "3. NO Open CIDRs: Security groups must NOT contain '0.0.0.0/0'. "
        "4. NO Hardcoded IDs: It must use data sources (e.g. data.aws_caller_identity) instead of 12-digit AWS account IDs. "
        "5. Proper Naming: IAM roles must be prefixed with 'ianl-agent-'. "
        "If the code follows these rules, output a perfect score. Do not penalize if the agent doesn't explicitly talk about these rules, only judge the code it wrote."
    ),
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    strict_mode=True, 
    threshold=1.0 
)
@pytest.mark.asyncio
async def test_3_static_site_cloudfront():
    input_query = "I want to host a fast static website. Create an S3 bucket for the files, then set up a CloudFront Distribution to serve that bucket. Ensure the bucket is private and only reachable via the CloudFront Origin Access Identity (OAI)."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-3-cloudfront")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    # Security compliance is critical here (Private S3 bucket)
    assert_test(test_case, [security_compliance_metric, task_completion])

@pytest.mark.asyncio
async def test_4_serverless_webhook_lambda_url():
    input_query = "Create a Python Lambda function that returns a JSON response with the current timestamp. Instead of API Gateway, use the new 'Lambda Function URL' feature (Auth Type: NONE) so I have a direct public endpoint to hit. Output the URL."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-4-lambda")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [task_completion, tool_correctness])

@pytest.mark.asyncio
async def test_5_database_and_secret_rds():
    input_query = "Deploy a micro MySQL RDS instance. Generate a secure 16-character password automatically, store it in AWS Secrets Manager under the name 'db-creds', and configure the RDS instance to use that secret for its master password."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-5-rds")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    # Highest security priority test
    assert_test(test_case, [security_compliance_metric, task_completion])

@pytest.mark.asyncio
async def test_6_scheduled_task_eventbridge():
    input_query = "I need a 'Cron' job in the cloud. Create a Lambda function that logs 'Heartbeat' to CloudWatch, and set up an EventBridge rule to trigger this Lambda every 5 minutes."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-6-cron")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [task_completion, step_efficiency])

@pytest.mark.asyncio
async def test_7_image_processor_s3_lambda():
    input_query = "Create two S3 buckets: 'source-images' and 'processed-images'. Write a Lambda function that is triggered whenever a file is uploaded to 'source-images'. The Lambda should simply copy the file to 'processed-images' and then delete it from the source."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-7-processor")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [task_completion])

@pytest.mark.asyncio
async def test_8_networking_expert_vpc():
    input_query = "Build a custom VPC from scratch with one Public Subnet and one Private Subnet. Launch an EC2 instance in the Private Subnet. Explain to me how I would be able to access this instance if there is no direct internet path."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-8-vpc")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [security_compliance_metric, task_completion])

@pytest.mark.asyncio
async def test_9_cost_monitor_budgets():
    input_query = "Set up an AWS Budget for my account. If my total monthly spend exceeds $5.00, send an email alert to courage9605@gmail.com. This tests if you can handle account-level management resources."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-9-budgets")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        expected_tools=[ToolCall(name="write_code"), ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [task_completion])

@pytest.mark.asyncio
async def test_10_resource_auditor_cli_only():
    input_query = "Don't create anything. Instead, use your shell tools to list all S3 buckets, all running EC2 instances, and all IAM users in my account. Summarize my current infrastructure in a clean Markdown table."
    actual_output, raw_tool_calls = await ask_agent_programmatically(input_query, thread_id="test-10-auditor")
    
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        tools_called=parse_tool_calls(raw_tool_calls),
        # Expecting ONLY shell commands, no code writing since it was told not to create anything
        expected_tools=[ToolCall(name="run_shell_commands")],
    )
    assert_test(test_case, [task_completion, tool_correctness])

@pytest.mark.asyncio
async def test_11_resources_clean_up():
    input_query = ""