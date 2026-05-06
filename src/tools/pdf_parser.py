import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFParser:
    """直接解析文本pdf并使用OCR作为扫描pdf的备份."""

    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def _perform_ocr(self, file_path):
        """扫描型 PDF 的 OCR 处理"""
        print(f"检测到扫描的PDF。运行OCR {os.path.basename(file_path)}...")
        try:
            import fitz
            from rapidocr_onnxruntime import RapidOCR

            engine = RapidOCR()
            #逐页处理
            doc = fitz.open(file_path)
            ocr_text = ""
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes()
                result, _ = engine(img_bytes)
                #收集文本
                if result:
                    page_text = "\n".join([line[1] for line in result])
                    ocr_text += page_text + "\n"

            return ocr_text
        except ImportError:
            print("缺少OCR依赖项。安装pymupdf和rapid -onnxruntime")
            return ""
        except Exception as exc:
            print(f"OCR 失败 {file_path}: {exc}")
            return ""

    def parse_directory(self, directory_path):
        if not os.path.exists(directory_path):
            print(f"PDF 文件不存在: {directory_path}")
            return []

        all_docs = []
        pdf_files = [file for file in os.listdir(directory_path) if file.lower().endswith(".pdf")]
        
        #逐个处理 PDF 文件
        for file in pdf_files:
            file_path = os.path.join(directory_path, file)
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                #判断是否需要 OCR
                valid_pages = [page for page in pages if len(page.page_content.strip()) > 10]
                if not valid_pages:# 如果所有页面都无效（文本长度≤10）
                    full_text = self._perform_ocr(file_path)
                    # OCR 得到完整文本后封装为 Document
                    if full_text.strip():
                        docs = [Document(page_content=full_text, metadata={"source": file_path})]
                        parsed_chunks = self.text_splitter.split_documents(docs)
                    else:
                        parsed_chunks = [] # OCR 也失败
                # 存在有效文本页（非扫描件），直接使用
                #split_documents 会自动遍历每个 Document（每页一个 Document），将长文本按 chunk_size 切分成多个新的 Document，并保留原 metadata
                else:
                    parsed_chunks = self.text_splitter.split_documents(valid_pages)

                if parsed_chunks:
                    #将有效的 chunks 加入 all_docs
                    all_docs.extend(parsed_chunks)
                    print(f"解析{file}: {len(parsed_chunks)} 文件块")
                else:
                    print(f"没有文本提取 {file}. 文件可能被加密或损坏。")
            except Exception as exc:
                print(f"解析失败 {file}: {exc}")

        return all_docs
