from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import Config
from src.schema import AgentState


def writer_node(state: AgentState):
    """根据检索到的上下文生成最终 Markdown 报告。"""
    steps = state.get("steps", [])

    if not Config.OPENAI_API_KEY:
        return {
            "report": _fallback_report(state, "OPENAI_API_KEY 未配置"),
            "steps": steps + ["报告生成跳过：缺少 LLM API Key"],
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
你是一位资深行业分析师。仅基于提供的网页与本地 PDF 上下文撰写报告。

研究主题：{task}

Web 上下文：
{web_context}

PDF 上下文：
{pdf_context}

要求：
1. 使用 Markdown。
2. 包含：背景、现状、主要瓶颈、未来趋势、结论。
3. 关键结论按证据来源标注 [Web] 或 [PDF]。
4. 若来源之间存在冲突，请明确说明并给出平衡判断。
5. 不要编造数据或来源。
"""
        )
        #构建链并调用
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
            "steps": steps + ["生成最终 Markdown 研究报告"],
        }
    except Exception as exc:
        #如果 LLM 调用失败或 API Key 缺失，则回退到一个降级报告（展示原始上下文，避免信息丢失）
        return {
            "report": _fallback_report(state, f"LLM 生成失败: {exc}"),
            "steps": steps + [f"报告生成失败: {exc}"],
        }


def _fallback_report(state: AgentState, reason: str):
    """用于在 LLM 不可用时生成一个手工拼接的报告草稿"""
    return f"""# 研究报告草稿

## 主题
{state['task']}

## 生成状态
未自动生成最终 LLM 报告。

原因：{reason}

## 可用 Web 上下文
{state.get('web_context') or '没有可用的 web context'}

## 可用 PDF 上下文
{state.get('pdf_context') or '没有可用的 PDF context'}
"""
