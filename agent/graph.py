import uuid
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

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

async def run_IAC_agent():
    tools = [run_shell_commands,read_image,inspect_a_file,write_file]
    model = ChatQwen()
    model_with_tools = model.bind_tools(tools)

    def call_model(state: AgentState):
        messages = state["messages"]
        if not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
                    
        response = model_with_tools.invoke(messages)
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
    thread_id = str(uuid.uuid4())   
    async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:
        agent_executor = builder.compile(checkpointer=memory)    
        while True:
            query = input("Enter your query: ")

            try:
                result = await agent_executor.ainvoke({"messages":[{"role":"user","content":query}]}, config={"configurable": {"thread_id": thread_id}})
                final_resp = result["messages"][-1].content
                print_agent_response(final_resp)
                    
            except Exception as e:
                log.exception(f"Error while processing {thread_id}: {e}")

