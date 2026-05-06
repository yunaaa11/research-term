import trafilatura


class WebScraper:
    """获取urls和提取干净的文章正文文本"""

    def __init__(self, max_length=1500):
        self.max_length = max_length

    def scrape_url(self, url):
        """抓取并提取单个 URL 的正文内容"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return f"无法访问 URL: {url}"
            
            #从 HTML 中智能提取文章主体文本
            content = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,#保留表格内容
                no_fallback=False,
            )
            if content:
                return content[: self.max_length]
            return f"无法从 URL 提取有用正文文本: {url}"
        except Exception as exc:
            return f"抓取 URL 失败 {url}: {exc}"

    def batch_scrape(self, urls):
        """批量处理多个 URL"""
        results = []
        for url in urls:
            content = self.scrape_url(url)
            results.append(f"Source: {url}\nContent: {content}")
        return "\n\n---\n\n".join(results)
