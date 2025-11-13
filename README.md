# Gamma Agent Controlled Browser
A project exploring automated browser control using AI agents, built with LangGraph. This system enables intelligent web automation through agent-based decision making and browser interaction capabilities. Rather than relying on visual capabilities of model and finding the input elements, the agent will be serving various apps using their locators

## Technology Stack
- **Python 3.8+** - Core programming language
- **LangGraph** - Agent orchestration and workflow management
- **Playwright** - Browser automation and web scraping
- **LangChain** - LLM integration and prompt management
- **OpenAI GPT** - Large language model for decision making
- **Llama Models** - LLM during dev phase
- **LangSmith** - Monitoring and debugging agent workflows
- **Asyncio** - Asynchronous programming for concurrent operations

## How to use it?
### Prerequisites
- Python 3.11 or higher installed
- OpenAI API key or Llama model access
- Git for cloning the repository

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/anupmanekar/agent-controlled-browser-actions.git
    cd agent-controlled-browser-actions
    ```

2. Install dependencies:
    ```bash
    uv sync
    ```

3. Install Playwright browsers:
    ```bash
    playwright install
    ```

4. Set up environment variables:
    ```bash
    cp .env.example .env
    # Edit .env with your API keys and configuration
    ```

### Running the Agent
1. Start the agent system:
    ```bash
    uv run main.py
    ```

2. Configure your target website and automation tasks in the configuration file

3. Monitor agent workflows through LangSmith dashboard

## Learnings
1. Studio works only for sync API calls.
2. For async api calls, we need to test outside Langgraph Studio
3. For Deployment, there is only langsmith option as of now. But will try deploying to cloud.
4. Cannot delete the traces from langsmith
5. Langgraph SDK - get_client is not very useful for async runs