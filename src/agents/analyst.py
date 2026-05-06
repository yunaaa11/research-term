import os
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from schema import AgentState
from config import Config
from tools.pdf_parser import PDFParser

def pdf_analyst_node(state: AgentState):
    """把本地 PDF 研报变成可检索的知识库，并针对当前问题查询相关内容"""
    print(f"--- [PDF Analyst] 正在分析本地研报库 ---")
    # 1. 初始化 Embedding 模型 
    embeddings = HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'} 
    )
    
    # 2. 检查向量库是否已存在，不存在则现场构建
    persist_directory = Config.CHROMA_DB_PATH
    if not os.path.exists(persist_directory):
        print("向量库不存在，正在调用PDFparser解析原始文档...")
        parser = PDFParser(chunk_size=500, chunk_overlap=50)
        # 解析 data/reports 目录下所有的 PDF
        docs = parser.parse_directory("data/reports/")
        print(f"DEBUG: 扫描到的文档数量: {len(docs)}")
        if docs:
            vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                persist_directory=persist_directory
            )
            print(f"向量库构建完成，共处理 {len(docs)} 个文本块")
        else:
            return {
                "pdf_context": "本地库中无PDF文件可供分析（请确认 data/reports 下有可解析的 PDF）",
                "steps": ["未命中本地 PDF 资料"]
            }
    else:
        # 加载已有库
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
       
    
    # 3. 执行检索 (根据任务课题检索 Top 3 相关片段)
    query = state['task']
    related_docs = vectorstore.similarity_search(query, k=3)
    
    # 4. 格式化输出
    context_parts=[]
    for d in related_docs:
        #将每个检索到的片段附上来源文件名
        source_name=os.path.basename(d.metadata.get('source','未知文档'))
        context_parts.append(f"[文件：{source_name}]\n内容:{d.page_content}")
    pdf_context="\n\n".join(context_parts)
    
    return {
        "pdf_context": pdf_context if pdf_context else "未在本地研报库中找到相关深度分析信息。",
        "steps": ["完成本地 PDF 深度语义检索"]
    }