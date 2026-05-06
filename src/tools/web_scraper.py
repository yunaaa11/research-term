import trafilatura
class WebScraper:
    #搜索、负责抓取并清洗单个网页正文，以及批量处理多个 URL
    def __init__(self,max_length=1500):
        self.max_length=max_length
    
    def scraper_url(self,url):
        """抓取单个url的内容并提取原文"""
        try:
            #下载网页
            downloaded=trafilatura.fetch_url(url)
            if not downloaded:
                return f"无法访问该链接:{url}"
            #提取正文（会自动识别并剔除广告，导航栏）
            content=trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,#保留表格（行业分析报告中表格很重要）
                no_fallback=False#如果无法提取正文，会尝试启发式回退
            )
            if content:
                #为了防止模型token溢出，对单个网页内容进行更新
                return content[:self.max_length]
            else:
                return f"未能从该链接提取到有效正文：{url}"
            
        except Exception as e:
            return f"抓取URL{url}时发送错误：{str(e)}"
    
    def batch_scrape(self,urls):
        """批量抓取并返回汇总文本"""
        results=[]
        for url in urls:
            content=self.scraper_url(url)
            results.append(f"来源:{url}\n内容:{content}")
        return "\n\n---\n\n".join(results)