from config import Config
from src.schema import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
def writer_node(state:AgentState):
    llm = ChatOpenAI(
        model=Config.LLM_MODEL,
        openai_api_key=Config.OPENAI_API_KEY,
        openai_api_base=Config.OPENAI_BASE_URL,
        temperature=Config.TEMPERATURE
    )
    prompt=ChatPromptTemplate.from_template(
        """
        你是一位资深的行业分析师。请根据以下提供的两类信息源，撰写一份结构严谨、客观深度的调研报告。
        ### 信息源 A (互联网实时资讯):
        {web_context}
    
        ### 信息源 B (本地深度研报库):
        {pdf_context}
        ### 撰写要求:
        1. **结构化**: 必须包含背景、现状、核心技术瓶颈、未来趋势分析及结论。
        2. **引用**: 在描述关键数据或结论时，必须注明来源（例如：[Web] 或 [PDF]）。
        3. **冲突处理**: 若两类信息源存在矛盾（如量产时间不一致），请在报告中明确指出，并进行客观分析。
        4. **风格**: 专业、干练，避免口语化。
    
    课题: {task}
    报告内容:
    """
    )
    chain=prompt|llm
    response=chain.invoke({
        "web_context":state["web_context"],
        "pdf_context":state["pdf_context"],
        "task":state["task"]
    })
    return {"report": response.content, "steps": ["报告撰写完成"]}