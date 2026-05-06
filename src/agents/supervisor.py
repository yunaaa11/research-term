from langgraph.graph import END, StateGraph

from agents.analyst import pdf_analyst_node
from agents.researcher import web_researcher_node
from agents.writer import writer_node
from schema import AgentState


def router_node(state: AgentState):
    """在生成报告之前选择检索路径"""
    task = state["task"].lower()
    web_keywords = ["最新", "实时", "新闻", "政策", "2024", "2025", "2026", "today", "latest", "web"]
    pdf_keywords = ["研报", "pdf", "本地", "文档", "报告", "资料库", "知识库"]

    needs_web = any(keyword in task for keyword in web_keywords)
    needs_pdf = any(keyword in task for keyword in pdf_keywords)

    if needs_web and not needs_pdf:
        route = "web"
    elif needs_pdf and not needs_web:
        route = "pdf"
    else:#两者都需要 或 都不需要（默认）
        route = "both"

    return {
        "route": route,
        "steps": state.get("steps", []) + [f"Router 选择的路径: {route}"],
    }


def route_from_router(state: AgentState):
    if state["route"] == "pdf":
        return "pdf_analyst"
#否则（包括 "web" 或 "both"）→ 返回 "web_researcher"（先走网络检索，后续再决定是否走 PDF）
    return "web_researcher"


def route_after_web(state: AgentState):
    if state["route"] == "both":
        return "pdf_analyst"
    #否则（route == "web"）  已经完成所需检索，直接进入 writer 生成报告
    return "writer"


def create_research_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("web_researcher", web_researcher_node)
    workflow.add_node("pdf_analyst", pdf_analyst_node)
    workflow.add_node("writer", writer_node)

    workflow.set_entry_point("router")
    #router → 检索节点
    workflow.add_conditional_edges(
        "router",
        route_from_router,
        {
            "web_researcher": "web_researcher",
            "pdf_analyst": "pdf_analyst",
        },
    )
    #web_researcher → 下一个节点
    workflow.add_conditional_edges(
        "web_researcher",
        route_after_web,
        {
            "pdf_analyst": "pdf_analyst",
            "writer": "writer",
        },
    )
    workflow.add_edge("pdf_analyst", "writer")
    workflow.add_edge("writer", END)
    return workflow.compile()
