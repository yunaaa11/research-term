import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class PDFParser:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    def _perform_ocr(self, file_path):
        """对扫描件 PDF 执行 OCR 识别"""
        print(f"检测到扫描件，正在启动 OCR 识别: {os.path.basename(file_path)}...")
        try:
            import fitz  # PyMuPDF
            from rapidocr_onnxruntime import RapidOCR
            
            engine = RapidOCR()
            doc = fitz.open(file_path)
            ocr_text = ""
            
            for page in doc:
                # 将 PDF 页面转为图片 (增强分辨率提高 OCR 准确率)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
                img_bytes = pix.tobytes()
                
                # 执行 OCR
                result, _ = engine(img_bytes)
                if result:
                    # 拼接识别出的文本
                    page_text = "\n".join([line[1] for line in result])
                    ocr_text += page_text + "\n"
            #返回整份 PDF 的纯文本
            return ocr_text
        except ImportError:
            print("错误: 请安装 fitz (pymupdf) 和 rapidocr-onnxruntime 以支持 OCR")
            return ""
        except Exception as e:
            print(f"OCR 识别失败: {e}")
            return ""

    def parse_directory(self, directory_path):
        """解析目录下所有的PDF文件，支持扫描件"""
        if not os.path.exists(directory_path):
            return []
            
        all_docs = []
        #仅处理 .pdf 后缀（不区分大小写）
        pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]

        for file in pdf_files:
            file_path = os.path.join(directory_path, file)
            try:
                # 1. 尝试常规解析
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                
                # 过滤掉内容过少的页面（可能是扫描件占位符） 
                valid_pages = [p for p in pages if len(p.page_content.strip()) > 10]
                
                if not valid_pages:
                    # valid_pages 为空（说明所有页面几乎无文本）→ 调用 OCR
                    full_text = self._perform_ocr(file_path)
                    if full_text.strip():
                        # 若 OCR 成功获得文本，则构建一个 Document 对象（元数据记录源文件路径），然后切块。
                        docs = [Document(page_content=full_text, metadata={"source": file_path})]
                        parsed_chunks = self.text_splitter.split_documents(docs)
                    else:
                        parsed_chunks = []
                else:
                     #有正常文本页面 → 直接对 valid_pages 进行切块
                    parsed_chunks = self.text_splitter.split_documents(valid_pages)

                if parsed_chunks:
                    all_docs.extend(parsed_chunks)
                    print(f"解析成功: {file} -> {len(parsed_chunks)} 个文本块")
                else:
                    print(f"无法解析: {file}，请检查文件是否损坏或完全加密")
                    
            except Exception as e:
                print(f"解析文件 {file} 报错: {e}")
        #成功解析后打印文件名和块数量
        return all_docs