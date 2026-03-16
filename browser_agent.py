import os 
import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_cerebras import ChatCerebras
from playwright.async_api import async_playwright

load_dotenv()


class BrowserController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

browser = BrowserController()

llm = ChatCerebras(model="llama3.1-8b", api_key=os.getenv("CEREBRAS_API_KEY"))

@tool
async def open_url(url: str) -> str:
    """Open a webpage in the browser"""
    await browser.page.goto(url)
    return f"Opened {url}"

@tool
async def search_google(query: str) -> str:
    """Search Google and return the page title"""
    page = browser.page
    await page.goto("https://www.google.com")
    await page.fill("textarea[name='q']", query)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(2000)
    return await page.title()

@tool
async def get_page_text() -> str:
    """Extract visible text from the webpage"""
    content = await browser.page.inner_text("body")
    return content[:2000]

tools = [
    open_url,
    search_google,
    get_page_text
]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
    You are a helpful browser based AI Assistant with three tools : 
    """
)

async def main():
    await browser.init()
    print("Browser connected correctly!")
    while True:
        loop = asyncio.get_event_loop()
        query = await loop.run_in_executor(None, input, "User: ")
        
        if query.lower() == "exit":
            break

        response = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        
        if isinstance(response, dict) and "messages" in response:
            print("Agent:", response["messages"][-1].content)
        else:
            try:
                print("Agent:", response.content)
            except AttributeError:
                print("Agent:", response)

if __name__ == "__main__":
    asyncio.run(main())