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
        results = search_results.get("results", [])
        urls = [res["url"] for res in results if res.get("url")]

        if not urls:
            return {
                "web_context": "没有返回有效的网络搜索结果。",
                "steps": steps + ["Web搜索已完成，但未返回有效的urls"],
            }

        web_content = _build_web_context(results, scraper)
        return {
            "web_context": web_content or "找到了网页，但没有提取出可用的 Web 正文或搜索摘要",
            "steps": steps + [f"从{len(urls)} urls中收集Web上下文，其中{web_content.count('Source:')}条可用"],
        }
    except Exception as exc:
        return {
            "web_context": f"Web 搜索失败: {exc}",
            "steps": steps + [f"Web 搜索失败: {exc}"],
        }


def _build_web_context(results, scraper):
    context_parts = []
    failure_prefixes = (
        "无法访问 URL",
        "无法从 URL 提取有用正文文本",
        "抓取 URL 失败",
    )

    for result in results:
        url = result.get("url")
        if not url:
            continue

        title = result.get("title") or "Untitled"
        tavily_content = (result.get("content") or result.get("raw_content") or "").strip()
        scraped_content = scraper.scrape_url(url).strip()
        use_scraped = scraped_content and not scraped_content.startswith(failure_prefixes)
        content = scraped_content if use_scraped else tavily_content

        if not content:
            continue

        context_parts.append(
            f"Source: {url}\nTitle: {title}\nContent: {content[: scraper.max_length]}"
        )

    return "\n\n---\n\n".join(context_parts)
