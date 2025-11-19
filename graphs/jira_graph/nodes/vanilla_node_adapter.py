# Define following functions in this file
# 1. get_user_instructions() -> str
# 2. determine_if_there_are_browser_actions(instructions: str) -> bool
# 3. ask_for_instructions_again() -> str
# 4. extract_browser_actions_and_determine_sequence(instructions: str) -> List[str]
# 5. create_browser_session() -> BrowserSession
# 6. perform_browser_actions(session: BrowserSession, actions: List[str]) -> None
# 7. invoke_llm_to_invoke_appropriate_browser_action(intent: str, state: dict) -> str
# 8. determine_if_browser_action_is_successful(response: str) -> bool
# 9. handle_browser_action_failure(session: BrowserSession, action: str) -> None
# 10. log_browser_action_details(action: str, response: str) -> None
# 11. close_browser_session(session: BrowserSession) -> None
# 12. finalize_actions_report(actions: List[str], results: List[str]) -> str

from typing import List, Literal
from graphs.vanilla_graph.state import VanillaGraphState
from langgraph.types import Command, interrupt
from playwright.sync_api import Playwright, Browser, sync_playwright

class VanillaNodeAdapter:
    def __init__(self, chat_llm):
        self.chat_llm = chat_llm
        self.browser_instance: Browser = None
        self.browser_page = None

    def human_get_instructions(self, state: VanillaGraphState) -> VanillaGraphState:
        message = """
        Please provide the instructions for the browser actions to be performed.
        """
        human_response = interrupt(message)
        state.messages.append(human_response)
        return state
    
    def human_get_additional_instructions(self, state: VanillaGraphState) -> VanillaGraphState:
        message = """
        Please provide any additional instructions for the browser actions to be performed.
        """
        human_response = interrupt(message)
        state.messages.append(human_response)
        return state

    def check_for_browser_actions(self, state: VanillaGraphState) -> Command[Literal["extract_browser_actions", "human_get_instructions"]]:
        # Single-shot prompt to determine if instructions contain browser actions
        prompt = f"""
        Analyze the following instructions and determine if user is asking any tasks that require browser actions. 
        Some requests might be continuation to earlier browser actions so consider the context as well.

        Instructions: "{state.messages[-1]}"
                
        Respond with only "true" if browser actions are present, or "false" if not.
        """
        
        response = self.chat_llm.invoke([("human", prompt)])
        if response.content.strip().lower() == "false":
            state.messages = []
            return Command(goto="human_get_instructions", update={"messages": []})
        else:
            return Command(goto="extract_browser_actions")

    # def _ask_for_instructions_again(self, state: VanillaGraphState) -> VanillaGraphState:
    #     prompt = """
    #     The provided instructions do not contain any browser-related actions. 
    #     Please provide new instructions that include specific browser actions to be performed.
    #     """
        
    #     response = self.chat_llm.invoke([("human", prompt)])
    #     state.message = response.content.strip()
    #     return state
    
    def extract_browser_actions(self, state: VanillaGraphState) -> VanillaGraphState:
        prompt = f"""
        Infer what are the actions that need browser to be invoked in given instructions. 
        The new instructions may be continuations of earlier browser actions so consider the context {state.browser_actions} and share only the new inferred browser actions.
        
        For example: if user says "Go to the next page" and earlier action was "Navigate to example.com", then infer the new action as "Navigate to example.com/nextpage".

        Instructions: "{state.messages[-1]}"
        
        Output should be list of browser actions to be performed, one action per line. Dont include any explanations or other additional text.
        """
        
        response = self.chat_llm.invoke([("human", prompt)])
        actions = response.content.strip().splitlines()
        state.browser_actions.extend([action.strip() for action in actions if action.strip()])
        return state
    
    def human_check_for_additional_instructions(self, state: VanillaGraphState) -> Command[Literal["human_get_additional_instructions","human_get_instructions", "human_review_browser_actions"]]:
        human_response = interrupt(
            {
                "question": "Do you have any additional instructions? or do you want to start from beginning?",
                "options": ["yes", "no", "reset"],
            })

        if str(human_response).upper() == "YES":
            return Command(goto="human_get_additional_instructions")
        elif str(human_response).upper() == "RESET":
            state.browser_actions = []  # Reset actions
            state.messages = []  # Reset messages
            return Command(goto="human_get_instructions", update={"messages": [], "browser_actions": []})
        else:
            return Command(goto="human_review_browser_actions")

    def human_review_browser_actions(self, state: VanillaGraphState) -> Command[Literal["break_browser_actions_into_granular_steps", "human_get_instructions"]]:
        actions_list = "\n".join(state.browser_actions)
        message = f"""
        The following browser actions have been extracted:\n{actions_list}\n
        Please review and confirm if these actions are correct or provide modifications.
        Respond only with Yes or No.
        """
        human_response = interrupt({
            "question": message,
            "options": ["yes", "no"],
        })
        if str(human_response).upper() == "YES":
            return Command(goto="break_browser_actions_into_granular_steps")
        else:
            state.browser_actions = []  # Reset actions
            state.messages = []  # Reset messages
            return Command(goto="human_get_instructions", update={"messages": [], "browser_actions": []})
        
    def break_browser_actions_into_granular_steps(self, state: VanillaGraphState) -> VanillaGraphState:
        prompt = f"""
        The following browser actions have been extracted:\n{state.browser_actions}\n
        Please break down each action into more granular steps if possible. 
        For example, "Log into account" can be broken down into "Navigate to login page", "Enter username", "Enter password", "Click login button".
        Provide the updated list of granular steps, one step per line. Dont include any explanations or other additional text. 
        Also dont include original browser actions in the list.
        """
        response = self.chat_llm.invoke([("human", prompt)])
        steps = response.content.strip().splitlines()
        state.browser_granular_steps = [step.strip() for step in steps if step.strip()]
        return state
    
    def finalize_actions_report(self, state: VanillaGraphState) -> VanillaGraphState:
        # report = "Actions Report:\n"
        # for action, result in zip(state.browser_actions, state.action_results):
        #     report += f"Action: {action}\nResult: {result}\n"

        # state.final_report = report
        return state

    def human_start_new_task(self, state: VanillaGraphState) -> Command[Literal["final_task", "human_get_instructions"]]:
        message = """
        Do you want to start a new task? If yes, please provide the new instructions.
        """
        human_response = interrupt({
            "question": message,
            "options": ["yes", "no"],
        })
        if str(human_response).upper() == "YES":
            state.messages = [human_response]
            state.browser_actions = []
            state.browser_granular_steps = []
            state.action_results = []
            state.final_report = None
            return Command(goto="human_get_instructions", update={"messages": state.messages, "browser_actions": [], "browser_granular_steps": [], "action_results": [], "final_report": None})
        else:
            return Command(goto="final_task")
        
    def final_task(self, state: VanillaGraphState) -> VanillaGraphState:
        message = "All tasks completed. Thank you!"
        interrupt(message)
        return state
    # def human_wait_for_next_task(self, state: VanillaGraphState) -> VanillaGraphState:
    #     message = """
    #     Waiting for the next task. Please provide instructions when ready.
    #     """
    #     human_response = interrupt(message)
    #     state.messages = [human_response]
    #     state.browser_actions = []
    #     state.browser_granular_steps = []
    #     state.action_results = []
    #     state.final_report = None
    #     return Command(goto="human_get_instructions", update={"messages": state.messages, "browser_actions": [], "browser_granular_steps": [], "action_results": [], "final_report": None})

    