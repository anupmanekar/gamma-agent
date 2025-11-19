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


class VanillaGraphBuilder:
    def __init__(self):
        self.chat_llm = ChatOllama(model="llama3.1:8b", temperature=0)
        self.chat_llm_with_agent = create_agent(
            model=self.chat_llm,
            tools=[],
        )
        self.memory_saver = None
        if (not os.getenv("LANGGRAPH_API")) or os.getenv("LANGGRAPH_API").lower() == "false":
            self.memory_saver = MemorySaver()
        
        self.workflow = StateGraph(VanillaGraphState)
        self.browser_workflow_graph = StateGraph(VanillaGraphState)
        self.node_adapter = VanillaNodeAdapter(self.chat_llm)
        self.browser_node_adapter = BrowserNodeAdapter(self.chat_llm)
        
    def _add_nodes(self):
        # Add vanilla nodes
        node_methods = [attr for attr in dir(self.node_adapter) if callable(getattr(self.node_adapter, attr)) and not attr.startswith('_')]
        for method_name in node_methods:
            self.workflow.add_node(method_name, getattr(self.node_adapter, method_name))

        # Add browser nodes
        browser_node_methods = [attr for attr in dir(self.browser_node_adapter) if callable(getattr(self.browser_node_adapter, attr)) and not attr.startswith('_')]
        for method_name in browser_node_methods:
            self.browser_workflow_graph.add_node(method_name, getattr(self.browser_node_adapter, method_name))

    def _add_edges(self):
        # Define edge configurations
        workflow_edges = [
            (START, "check_for_browser_actions"),
            ("human_get_instructions", "check_for_browser_actions"),
            ("extract_browser_actions", "human_check_for_additional_instructions"),
            ("human_get_additional_instructions", "check_for_browser_actions"),
            ("break_browser_actions_into_granular_steps", "browser_workflow"),
            ("browser_workflow", "finalize_actions_report"),
            ("finalize_actions_report", "human_start_new_task"),
            ("final_task", END)
        ]

        browser_workflow_edges = [
            (START, "create_browser_session"),
            ("create_browser_session", "execute_browser_actions"),
            ("execute_browser_actions", "close_browser_session"),
            ("close_browser_session", END)
        ]

        # Add edges
        for from_node, to_node in workflow_edges:
            self.workflow.add_edge(from_node, to_node)

        for from_node, to_node in browser_workflow_edges:
            self.browser_workflow_graph.add_edge(from_node, to_node)

    def build(self):
        self._add_nodes()
        self._add_edges()
        
        # Compile browser workflow and add as node
        browser_workflow = self.browser_workflow_graph.compile(checkpointer=self.memory_saver)
        self.workflow.add_node("browser_workflow", browser_workflow)
        
        # Compile main workflow
        app = self.workflow.compile(checkpointer=self.memory_saver)
        return app


# Usage
graph_builder = VanillaGraphBuilder()
app = graph_builder.build()
