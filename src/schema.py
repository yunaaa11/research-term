from typing import List, TypedDict


class AgentState(TypedDict):
    task: str
    route: str
    web_context: str
    pdf_context: str
    report: str
    steps: List[str]
