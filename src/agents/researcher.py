from src.schema import AgentState
import trafilatura
from tavily import TavilyClient
from config import Config
from tools.web_scraper import WebScraper
def web_researcher_node(state:AgentState):
    # 1. 初始化搜索客户端和抓取工具
    #Tavily 搜索引擎的客户端，专门为 RAG 优化，返回结构化的搜索结果（包含 URL、标题、摘要等）
    tavily=TavilyClient(api_key=Config.TAVILY_API_KEY)
    #利用 WebScraper 批量抓取这些网页的正文，最后将清洗后的文本存入状态供后续使用
    scraper=WebScraper(max_length=1500)

    query=state['task']
    print(f"---[Web Researcher]正在执行互联网搜索:{query}---")

    # 2. 执行搜索获取 URL 列表
    search_results=tavily.search(query=query,search_depth="advanced", max_results=3)
    urls=[res['url'] for res in search_results['results']]
    
    #3.调用工具进行批量内容提取与清洗
    web_content=scraper.batch_scrape(urls)

    return {
        "web_context": web_content if web_content else "未能通过互联网搜集到有效信息。",
        "steps": ["完成互联网实时信息采集与正文清洗"]
    }


