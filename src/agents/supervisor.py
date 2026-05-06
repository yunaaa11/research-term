from langgraph.graph import StateGraph, END
from typing import Dict
from schema import AgentState
from agents.researcher import web_researcher_node
from agents.analyst import pdf_analyst_node
from agents.writer import writer_node

def create_research_graph():
    workflow=StateGraph(AgentState)
    #添加节点
    workflow.add_node("web_researcher",web_researcher_node)
    workflow.add_node("pdf_analyst", pdf_analyst_node)
    workflow.add_node("writer", writer_node)
    # 设置入口：这里我们演示并行触发（通过一个虚拟节点或同时指向两个节点）
    # 跑通顺序流：Web -> PDF -> Writer
    workflow.set_entry_point("web_researcher")
    workflow.add_edge("web_researcher", "pdf_analyst")
    workflow.add_edge("pdf_analyst", "writer")
    workflow.add_edge("writer", END)
    return workflow.compile()