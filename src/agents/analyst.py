import os

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import Config
from schema import AgentState
from tools.pdf_parser import PDFParser


def pdf_analyst_node(state: AgentState):
    """构建或加载本地 PDF 向量存储，然后检索相关片段"""
    steps = state.get("steps", [])
    print("--- [PDF Analyst]正在检索本地 PDF 知识库 ---")

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )

        persist_directory = Config.CHROMA_DB_PATH
        if not os.path.exists(persist_directory):
            print("向量存储未找到。正在解析 data/reports 下的 PDF 文件...  ")
            parser = PDFParser(chunk_size=500, chunk_overlap=50)
            docs = parser.parse_directory("data/reports/")

            if not docs:
                return {
                    "pdf_context": "在 data/reports 下未找到可解析的 PDF 文件",
                    "steps": steps + [" 由于未找到可解析的文档，因此跳过 PDF 检索"],
                }

            vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                persist_directory=persist_directory,
            )
            print(f"已使用 {len(docs)} 个文本块构建向量存储")
        else:
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
            )
        #相似性检索：在向量库中检索最相似的 3 个文本块
        related_docs = vectorstore.similarity_search(state["task"], k=3)
        #格式化检索结果
        context_parts = []
        for doc in related_docs:
            source_name = os.path.basename(doc.metadata.get("source", "unknown_document"))
            page = doc.metadata.get("page")
            page_text = f", page {page + 1}" if isinstance(page, int) else ""
            #组装成易读的引用格式，例如：[PDF: annual_report.pdf, page 3]\nContent: 公司去年营收增长8%...
            context_parts.append(
                f"[PDF: {source_name}{page_text}]\nContent: {doc.page_content}"
            )
        #将所有检索块用两个换行分隔，形成最终上下文
        pdf_context = "\n\n".join(context_parts)
        return {
            "pdf_context": pdf_context or "未检索到相关 PDF 块",
            "steps": steps + [f"检索到 {len(related_docs)} 个相关 PDF 块"],
        }
    except Exception as exc:
        return {
            "pdf_context": f" PDF 检索失败：{exc}",
            "steps": steps + [f" PDF 检索失败：{exc}"],
        }
