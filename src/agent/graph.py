import uuid, asyncio
import os 
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, SystemMessage,ToolMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode
from utils.logger import log
from rich.panel import Panel
from rich.markdown import Markdown
from utils.ui import console
from rich.live import Live
from core.prompts import SYSTEM_PROMPT
from config.settings import settings
from tools.file_tools import read_image, inspect_a_file,refactoring_code,write_code
from tools.shell_tools import run_shell_commands

load_dotenv()

mistral_small_4 = ChatMistralAI(
            model="mistral-small-latest",
            api_key=os.getenv("MISTRAL_API_KEY"),
)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

async def run_IaNL_agent(thread_id: str = None):
    tools = [run_shell_commands,read_image,inspect_a_file,refactoring_code,write_code]
    model = mistral_small_4
    model_with_tools = model.bind_tools(tools)

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
    if not thread_id:
        thread_id = str(uuid.uuid4())
        
    console.print(f"\n[dim]Session ID: {thread_id}[/dim]")
    
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
        agent_executor = builder.compile(checkpointer=memory)    
        while True:
            query = await asyncio.to_thread(console.input, "\n[bold green]➜[/bold green] [bold white]Enter your query:[/bold white] ")
            if query.lower() in ["exit", "quit"]:
                console.print(f"\n[dim]Stopping session... Session ID: {thread_id} , inorder to continue with same session id use --session-id {thread_id}[/dim]")
                break

            try:
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
                    
                    async for chunk in agent_executor.astream(
                        {"messages": [{"role": "user", "content": query}]}, 
                        config={"configurable": {"thread_id": thread_id}}, 
                        stream_mode="messages"
                    ):
                        if isinstance(chunk, tuple) and len(chunk) == 2:
                            token, metadata = chunk
                        else:
                            continue
                            
                        # Capture chunks from the LLM node
                        if metadata.get("langgraph_node") == "llm" and hasattr(token, "content"):
                            if isinstance(token.content, str) and token.content:
                                full_content += token.content
                                live.update(get_renderable(full_content))
                
                    live.update(get_renderable(full_content, generating=False))

                    
                    
            except Exception as e:
                log.exception(f"Error while processing {thread_id}: {e}")

                

if __name__ == "__main__":
    asyncio.run(run_IaNL_agent())