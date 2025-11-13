import os
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy
from graphs.vanilla_graph.state import VanillaGraphState
from graphs.vanilla_graph.nodes.vanilla_node_adapter import VanillaNodeAdapter
from graphs.vanilla_graph.nodes.browser_node_adapter import BrowserNodeAdapter
import asyncio

chat_llm = ChatOllama(model="llama3.1:8b", temperature=0)
chat_llm_with_agent = create_agent(
    model=chat_llm,
    tools=[],
)
memory_saver = None
if not os.getenv("LANGGRAPH_API"):
    memory_saver = MemorySaver()
#retry_policy = RetryPolicy(max_retries=3, backoff_factor=2)

workflow = StateGraph(VanillaGraphState)
browser_workflow_graph = StateGraph(VanillaGraphState)
node_adapter = VanillaNodeAdapter(chat_llm)
browser_node_adapter = BrowserNodeAdapter(chat_llm)

node_methods = [attr for attr in dir(node_adapter) if callable(getattr(node_adapter, attr)) and not attr.startswith('_')]
for method_name in node_methods:
    workflow.add_node(method_name, getattr(node_adapter, method_name))

browser_node_methods = [attr for attr in dir(browser_node_adapter) if callable(getattr(browser_node_adapter, attr)) and not attr.startswith('_')]
for method_name in browser_node_methods:
    browser_workflow_graph.add_node(method_name, getattr(browser_node_adapter, method_name))

# Define edge configurations
workflow_edges = [
    (START, "check_for_browser_actions"),
    ("human_get_instructions", "check_for_browser_actions"),
    ("extract_browser_actions", "human_check_for_additional_instructions"),
    ("break_browser_actions_into_granular_steps", "browser_workflow"),
    ("browser_workflow", "finalize_actions_report"),
    ("finalize_actions_report", END)
]

browser_workflow_edges = [
    (START, "create_browser_session"),
    ("create_browser_session", "execute_browser_actions"),
    ("execute_browser_actions", "close_browser_session"),
    ("close_browser_session", END)
]

# Add edges using loops
for from_node, to_node in workflow_edges:
    workflow.add_edge(from_node, to_node)

for from_node, to_node in browser_workflow_edges:
    browser_workflow_graph.add_edge(from_node, to_node)

# workflow.add_conditional_edges("check_for_browser_actions", {True: "extract_browser_actions", False: "ask_for_instructions_again"})

browser_workflow = browser_workflow_graph.compile()
workflow.add_node("browser_workflow", browser_workflow)

app = workflow.compile(checkpointer=memory_saver)
