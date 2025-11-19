from typing import List, Literal, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel
from langgraph.graph import MessagesState
from playwright.sync_api import Browser

class BrowserIntents(BaseModel):
    intent: Literal['navigate_url', 'search', 'navigate', 'click', 'fill_form', 'scroll', 'extract_data']

class VanillaGraphState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    session_id: str | None = None
    browser_session_ids: List[str] = []
    messages: List[str] = []
    browser_actions: List[str] = []
    browser_granular_steps: List[str] = []
    action_results: List[str] = []
    final_report: str | None = None
