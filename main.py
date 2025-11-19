
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
client = get_client(url="http://localhost:2024")

# async def main():
#     thread_id = uuid.uuid4()
#     config = {"configurable": {"thread_id": thread_id}}
#     async for chunk in client.runs.stream(
#         thread_id=None,  # Threadless run
#         assistant_id="vanilla_graph", # Name of assistant. Defined in langgraph.json.
#         input={
#             "message": "hello, please open langchain docs and search for playwright integration."
#         },
#         config=config
#     ):
#         print(f"CHUNK: {chunk}")
#         if "__interrupt__" in chunk.data.keys():
#             print("Interrupt message:")
#             print(chunk.data["__interrupt__"])
#             human_response = input("Enter your response: ")
#             await client.runs.wait(
#                 thread_id=thread_id,
#                 assistant_id="vanilla_graph",
#                 command=Command(resume=[human_response])
#             )
#         print("\n\n")

async def main():
    config = {"configurable": {"thread_id": str(uuid.uuid4())}, "run_name": "vanilla_graph_run"}
    current_input = {"messages": ["hello, Navigate to langchain docs and search for playwright integration."]}
    graph_builder = VanillaGraphBuilder()
    app = graph_builder.build()
    while True:
        async for chunk in app.astream(current_input, config=config):
            logger.info(f"CHUNK: {chunk}")
            
            if "__interrupt__" in chunk:
                logger.info("Interrupt message:")
                logger.info(chunk["__interrupt__"])
                human_response = input("Enter your response: ")
                current_input = Command(resume=human_response)
                break
        else:
            # No interrupt occurred, exit the loop
            break
        
asyncio.run(main())