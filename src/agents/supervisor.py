from langgraph.graph import END, StateGraph

from agents.analyst import pdf_analyst_node
from agents.researcher import web_researcher_node
from agents.writer import writer_node
from schema import AgentState


def router_node(state: AgentState):
    """根据任务内容选择检索路径：web / pdf / both。"""
    task = state["task"].lower()

    web_keywords = [
        "最新", "实时", "新闻", "政策", "today", "latest", "web",
        "2024", "2025", "2026", "2027",
    ]
    pdf_keywords = [
        "研报", "pdf", "本地", "文档", "报告", "资料", "知识库",
        "低空", "低空经济", "无人机", "evtol",
        "新能源", "汽车", "出海", "ev", "export",
        "ai医疗", "医疗", "医学", "医院",
        "具身", "机器人", "robot", "robotics", "embodied",
    ]

    needs_web = any(keyword in task for keyword in web_keywords)
    needs_pdf = any(keyword in task for keyword in pdf_keywords)

    if needs_web and not needs_pdf:
        route = "web"
    elif needs_pdf and not needs_web:
        route = "pdf"
    else:
        route = "both"

    return {
        "route": route,
        "steps": state.get("steps", []) + [f"Router 选择路径: {route}"],
    }


def route_from_router(state: AgentState):
    """根据路由结果，决定从 router 节点之后先去哪个检索节点"""
    if state["route"] == "pdf":
        return "pdf_analyst"
    #"both" 情况下先走 Web，之后通过第二个条件边决定是否再去 PDF
    return "web_researcher"


def route_after_web(state: AgentState):
    """在 web_researcher 执行完之后，决定下一步"""
    #如果路由是 "both"（需要两个源）→ 接着去 pdf_analyst 节点
    if state["route"] == "both":
        return "pdf_analyst"
    #否则只需 Web 或只需 PDF→ 直接去 writer 节点
    return "writer"


def create_research_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("web_researcher", web_researcher_node)
    workflow.add_node("pdf_analyst", pdf_analyst_node)
    workflow.add_node("writer", writer_node)

    workflow.set_entry_point("router")
    workflow.add_conditional_edges(
        "router",
        route_from_router,
        {
            "web_researcher": "web_researcher",
            "pdf_analyst": "pdf_analyst",
        },
    )
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
