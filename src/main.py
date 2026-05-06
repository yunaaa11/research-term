from src.agents.supervisor import create_research_graph

def run_research(task: str):
    app = create_research_graph()
    initial_state = {
        "task": task,
        "route": "both",
        "web_context": "",
        "pdf_context": "",
        "report": "",
        "steps": []
    }
    result = app.invoke(initial_state)
    return result
