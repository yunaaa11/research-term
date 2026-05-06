from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import Config
from src.schema import AgentState


def writer_node(state: AgentState):
    """根据检索到的上下文生成最终的Markdown研究报告。"""
    steps = state.get("steps", [])

    if not Config.OPENAI_API_KEY:
        return {
            "report": _fallback_report(state, "OPENAI_API_KEY没有认证"),
            "steps": steps + ["报告生成跳过，因为LLM API密钥丢失"],
        }

    try:
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
            openai_api_base=Config.OPENAI_BASE_URL,
            temperature=Config.TEMPERATURE,
        )
        prompt = ChatPromptTemplate.from_template(
            """
            你是一位资深行业分析师。仅根据所提供的网页和PDF上下文撰写结构化、客观的研究报告。
            研究主题：{task} 
            Web上下文: {web_context}
            本地PDF上下文:{pdf_context}
            要求：
            1.使用Markdown。
            2.包括：背景、现状、主要瓶颈、未来趋势、结论。
            3. 根据证据来源，用[Web]或[PDF]标记重要的主张。
            4. 如果两个来源冲突，解释冲突并提供一个平衡的判断。
            5. 避免没有根据的数字或结论。
"""
        )
        chain = prompt | llm
        response = chain.invoke(
            {
                "web_context": state.get("web_context", ""),
                "pdf_context": state.get("pdf_context", ""),
                "task": state["task"],
            }
        )
        return {
            "report": response.content,
            "steps": steps + ["生成最终Markdown研究报告"],
        }
    except Exception as exc:
        return {
            "report": _fallback_report(state, f"LLM 生成失败: {exc}"),
            "steps": steps + [f"报告生成失败: {exc}"],
        }

#任何异常（网络、API 限流、解析错误等）都会触发降级报告，保证工作流不崩溃。 降级报告生成器
#包含主题、失败原因、以及两个上下文的原文输出 便于人工后续处理或排查问题
def _fallback_report(state: AgentState, reason: str):
    return f"""# 研究报告草稿

##主题
{state["task"]}

## 生成状态
最终的LLM报告没有自动生成

原因: {reason}

## 可用的Web上下文
{state.get("web_context") or "没有可用的web context"}

## 可用的PDF上下文
{state.get("pdf_context") or "没有可用的 PDF context"}
"""
