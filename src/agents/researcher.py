from tavily import TavilyClient

from config import Config
from src.schema import AgentState
from tools.web_scraper import WebScraper


def web_researcher_node(state: AgentState):
    """为研究课题收集新鲜的网络内容"""
    query = state["task"]
    steps = state.get("steps", [])
    print(f"--- [Web Researcher] 正在搜索 web : {query} ---")

    if not Config.TAVILY_API_KEY:
        return {
            "web_context": "Web 搜索跳过: TAVILY_API_KEY没有认证",
            "steps": steps + ["Web 搜索跳过因为 Tavily API key 丢失"],
        }

    try:
        tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
        scraper = WebScraper(max_length=1500)

        search_results = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=3,
        )
        urls = [res["url"] for res in search_results.get("results", []) if res.get("url")]

        if not urls:
            return {
                "web_context": "没有返回有效的网络搜索结果。",
                "steps": steps + ["Web搜索已完成，但未返回有效的urls"],
            }
        #批量抓取网页正文
        web_content = scraper.batch_scrape(urls)
        return {
            "web_context": web_content or "找到了网页，但没有提取出有用的正文",
            "steps": steps + [f"从{len(urls)} urls中收集并清理了web上下文"],
        }
    except Exception as exc:
        return {
            "web_context": f"Web 搜索失败: {exc}",
            "steps": steps + [f"Web 搜索失败: {exc}"],
        }
