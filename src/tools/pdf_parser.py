import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFParser:
    """Parse text-based PDF files and split them into chunks for retrieval."""

    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def parse_directory(self, directory_path, query=None):
        if not os.path.exists(directory_path):
            print(f"PDF directory does not exist: {directory_path}")
            return []

        all_docs = []
        #获取PDF文件列表并筛选
        pdf_files = [file for file in os.listdir(directory_path) if file.lower().endswith(".pdf")]
        selected_files = self._select_relevant_files(pdf_files, query)
        if selected_files != pdf_files:
            print("Selected PDF files:", ", ".join(selected_files))
        pdf_files = selected_files
        
        #逐个处理PDF文件
        for file in pdf_files:
            file_path = os.path.join(directory_path, file)
            try:
                #返回一个 Document 列表，每个元素对应PDF的一页，包含 page_content（文本）和 metadata（如页码、文件路径）。
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                #过滤掉页内容长度不超过10个字符（去除首尾空白后）的页面，避免处理空白页或只有少量符号的页。
                valid_pages = [page for page in pages if len(page.page_content.strip()) > 10]
                parsed_chunks = self.text_splitter.split_documents(valid_pages) if valid_pages else []

                #切分结果存储在 parsed_chunks 中
                if parsed_chunks:
                    all_docs.extend(parsed_chunks)
                    print(f"Parsed {file}: {len(parsed_chunks)} chunks")
                else:
                    print(f"No extractable text in {file}")
            except Exception as exc:
                print(f"Failed to parse {file}: {exc}")

        return all_docs

    def _select_relevant_files(self, pdf_files, query):
        """根据用户查询词选择相关的PDF文件（基于文件名匹配）"""
        #若 query 为空（None 或空字符串），直接返回全部PDF文件
        if not query:
            return pdf_files
        #否则，将查询转为小写，然后检查查询中是否包含预定义的主题别名
        normalized_query = query.lower()
        topic_aliases = {
            "ai_healthcare": ["ai医疗", "医疗", "医学", "医院", "healthcare", "medical"],
            "embodied_ai_robotics": ["具身", "机器人", "robot", "robotics", "embodied"],
            "ev_export": ["新能源", "汽车", "电动车", "出海", "ev", "export"],
            "low_altitude": ["低空", "无人机", "evtol", "low altitude", "低空经济"],
        }

        matched_topics = [
            topic
            for topic, aliases in topic_aliases.items()
            if any(alias in normalized_query for alias in aliases)
        ]
        if not matched_topics:
            return pdf_files

        selected = [
            file
            for file in pdf_files
            if any(topic in file.lower() for topic in matched_topics)
        ]
        return selected or pdf_files
