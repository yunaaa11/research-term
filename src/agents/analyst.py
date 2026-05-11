import hashlib
import os
import shutil

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import Config
from schema import AgentState
from tools.pdf_parser import PDFParser


def pdf_analyst_node(state: AgentState):
    """构建或加载本地 PDF 向量库，并检索相关片段。"""
    steps = state.get("steps", [])
    print("--- [PDF Analyst] 正在检索本地 PDF 知识库 ---")

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )

        #确定需要处理的 PDF 文件列表
        reports_directory = Config.PDF_REPORTS_DIR
        selected_pdf_files = _select_relevant_pdf_files(reports_directory, state["task"])
        #确定向量库的持久化目录（基于文件列表签名）
        persist_directory = _topic_vectorstore_path(Config.CHROMA_DB_PATH, selected_pdf_files)
        #判断是否需要重建向量库
        if _should_rebuild_vectorstore(persist_directory, selected_pdf_files):
            if os.path.exists(persist_directory):
                #如果需要重建，先删除旧目录（避免残留数据）
                shutil.rmtree(persist_directory)

            print(f"向量库未找到或已过期，正在解析目录: {reports_directory}")
            #重建向量库（如果需要）
            parser = PDFParser(chunk_size=500, chunk_overlap=50)
            docs = parser.parse_directory(reports_directory, query=state["task"])

            if not docs:
                return {
                    "pdf_context": f"在 {reports_directory} 下未找到可解析的 PDF 文本",
                    "steps": steps + ["未检索到可用 PDF 文本，跳过 PDF 上下文"],
                }

            vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                persist_directory=persist_directory,
            )
            print(f"已用 {len(docs)} 个文本块构建向量库")
        #加载已有的向量库（如果不需要重建）
        else:
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
            )
       #检索与任务最相似的片段
        related_docs = vectorstore.similarity_search(state["task"], k=3)
       #整理结果并返回
        context_parts = []
        for doc in related_docs:
            source_name = os.path.basename(doc.metadata.get("source", "unknown_document"))
            page = doc.metadata.get("page")
            page_text = f", page {page + 1}" if isinstance(page, int) else ""
            context_parts.append(f"[PDF: {source_name}{page_text}]\nContent: {doc.page_content}")

        pdf_context = "\n\n".join(context_parts)
        return {
            "pdf_context": pdf_context or "未检索到相关 PDF 片段",
            "steps": steps + [f"检索到 {len(related_docs)} 个相关 PDF 片段"],
        }
    except Exception as exc:
        return {
            "pdf_context": f"PDF 检索失败: {exc}",
            "steps": steps + [f"PDF 检索失败: {exc}"],
        }


def _should_rebuild_vectorstore(persist_directory: str, pdf_files: list[str]) -> bool:
    """判断现有向量库是否过期"""
    #向量库目录不存在 → 需要重建
    if not os.path.exists(persist_directory):
        return True
    #目录存在但缺少数据库文件 chroma.sqlite3 → 需要重建
    db_file = os.path.join(persist_directory, "chroma.sqlite3")
    if not os.path.exists(db_file):
        return True
    #如果没有 PDF 文件 → 无需重建（也无需建库）
    if not pdf_files:
        return False
    #该 PDF 文件在最后建库之后又被修改过，那么就认为向量库已经过时，需要重新构建。
    db_mtime = os.path.getmtime(db_file)
    return any(os.path.getmtime(file_path) > db_mtime for file_path in pdf_files)


def _topic_vectorstore_path(base_directory: str, pdf_files: list[str]) -> str:
    """为特定的 PDF 文件集合生成唯一的向量库子目录路径"""
    if not pdf_files:
        return base_directory
    #将所有 PDF 文件（按路径排序）的“文件名+修改时间+文件大小”拼接成一个字符串
    signature = "|".join(
        f"{os.path.basename(file_path)}:{os.path.getmtime(file_path)}:{os.path.getsize(file_path)}"
        for file_path in sorted(pdf_files)
    )
    #计算该字符串的 MD5 哈希，取前 10 位作为目录名
    digest = hashlib.md5(signature.encode("utf-8")).hexdigest()[:10]
    return os.path.join(base_directory, digest)


def _select_relevant_pdf_files(reports_directory: str, query: str) -> list[str]:
    """根据查询词（task）返回匹配的 PDF 文件全路径列表"""
    if not os.path.exists(reports_directory):
        return []

    pdf_files = [
        os.path.join(reports_directory, file)
        for file in os.listdir(reports_directory)
        if file.lower().endswith(".pdf")
    ]

    selected_names = PDFParser()._select_relevant_files(
        [os.path.basename(file_path) for file_path in pdf_files],
        query,
    )
    selected = {os.path.join(reports_directory, file_name) for file_name in selected_names}
    return [file_path for file_path in pdf_files if file_path in selected]
