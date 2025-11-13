# Open a playwright browser and perform actions based on user input interpreted by a langgraph agent.

from playwright.sync_api import sync_playwright
import logging
import pickle
# Configure logging to print to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APP_NAME = "agent-controlled-browser-actions"

def main():
    logger.info("Starting browser actions...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp('http://localhost:9222');
        context = browser.new_context()
        page = context.new_page()
        logger.info("Browser launched. You can now perform actions based on user input.")
        page.goto("https://docs.langchain.com/")
        # get the dom content under the body tag
        content = page.content()
        logger.info(content)
        logger.info(f"Page content length: {len(content)} characters")
        # Keep the browser open for a while to allow user interaction
        browser.close()
        logger.info("Browser closed.")
    
if __name__ == "__main__":
    main()