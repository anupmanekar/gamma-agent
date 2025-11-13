import json
import logging
from playwright.async_api import Playwright, Browser, async_playwright, Page
from langgraph.types import Command, interrupt
from langchain.agents import create_agent
from graphs.vanilla_graph.state import VanillaGraphState
from langchain.tools import tool, ToolRuntime

logger = logging.getLogger(__name__)

class BrowserNodeAdapter:
    def __init__(self, chat_llm):
        self.chat_llm_with_agent = chat_llm
        self.browser_instance: Browser = None
        self.browser_page = None
        self._command_registry = {
            "open_browser": self._open_browser,
            "search_in_browser": self._search_in_browser,
            "click_search_button": self._click_search_button,
        }

    async def create_browser_session(self, state: VanillaGraphState) -> VanillaGraphState:
        # Placeholder for creating a browser session
        playwright = await async_playwright().start()
        chromium = playwright.chromium # or "firefox" or "webkit".
        self.browser_instance = await chromium.connect_over_cdp('http://localhost:9222')
        self.browser_page = await self.browser_instance.new_page()
        return state
    
    async def execute_browser_actions(self, state: VanillaGraphState) -> None:
        # Placeholder for executing a browser granular steps
        logger.info(f"Executing browser steps: {state.browser_granular_steps}")
        for step in state.browser_granular_steps:
            logger.info(f"Executing browser step: {step}")
            prompt = f"""
                Think about the step : {step}.
                Which command among open_browser, search_in_browser, close_browser_session you would use to perform this step?
                Return the command name with necessary arguments in JSON format only.
                For example, {{"command": "open_browser", "url": "https://example.com"}}.
                Do not include any explanations, only return the JSON.
                """
            response = self.chat_llm_with_agent.invoke([("human", prompt)])
            logger.info(f"Received command response: {response}")
            command_data = json.loads(response.content.strip())
            logger.info(f"Parsed command data: {command_data}")
            await self._command_receiver(**command_data)
            logger.info(f"Browser step executed with response: {response}")

    async def _command_receiver(self, command: str, **kwargs):
        if command not in self._command_registry:
            raise ValueError(f"Unknown command: {command}. Available commands: {list(self._command_registry.keys())}")
        
        handler = self._command_registry[command]
        return await handler(**kwargs)

    async def _open_browser(self, url: str, **kwargs) -> None:
        if self.browser_instance is None:
            raise Exception("Browser session not created.")
        if self.browser_page is None:
            self.browser_page = await self.browser_instance.new_page()
        await self.browser_page.goto(url)
        await self.browser_page.wait_for_load_state("load")
        await self.browser_page.wait_for_timeout(2000)
    
    async def _search_in_browser(self, query: str, **kwargs) -> None:
        if self.browser_instance is None:
            raise Exception("Browser session not created.")
        locator = "input[name='q']"
        search_box = self.browser_page.locator(locator).nth(0)
        await search_box.fill(query)
        await search_box.press("Enter")

    async def _click_search_button(self, **kwargs) -> None:
        if self.browser_instance is None:
            raise Exception("Browser session not created.")
        selector = "input[type='submit']"
        element = self.browser_page.locator(selector).nth(0)
        await element.click()
    
    async def close_browser_session(self, state: VanillaGraphState) -> VanillaGraphState:
        if self.browser_instance:
            await self.browser_instance.close()
            self.browser_instance = None
            self.browser_page = None
        return state