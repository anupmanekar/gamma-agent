
from langgraph_sdk import get_client
from langgraph.types import Command
import asyncio
import uuid
from graphs.vanilla_graph.graph import VanillaGraphBuilder
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def main():
    thread_id = uuid.uuid4()
    print(f"Generated thread ID: {thread_id}")
    config = {"configurable": {"thread_id": str(thread_id)}, "run_name": "vanilla_graph_run"}
    current_input = {"messages": ["hello, Navigate to langchain docs and search for playwright integration."]}
    graph_builder = VanillaGraphBuilder()
    app = graph_builder.build()
    while True:
        async for chunk in app.astream(current_input, config=config):            
            if "__interrupt__" in chunk:
                logger.info(chunk["__interrupt__"])
                human_response = input("Enter your response: ")
                current_input = Command(resume=human_response)
                break
        else:
            # No interrupt occurred, exit the loop
            break

asyncio.run(main())