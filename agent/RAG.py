"""
论文数据库RAG检索系统
基于LangChain实现论文文档的检索增强生成
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback to deprecated version
    from langchain_community.embeddings import HuggingFaceEmbeddings

# Import config for RAG settings
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.config import Config
except ImportError:
    # Fallback if config not available
    Config = None


class PaperRAGSystem:
    """论文RAG检索系统"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        vector_store_path: Optional[str] = None
    ):
        """
        初始化RAG系统
        
        Args:
            base_url: LLM API基础URL（如果为None，从环境变量或配置读取）
            api_key: API密钥（如果为None，从环境变量或配置读取）
            model: 模型名称（如果为None，从环境变量或配置读取）
            temperature: 温度参数（如果为None，从环境变量或配置读取）
            vector_store_path: 向量数据库存储路径（None则使用默认路径）
        """
        # 从配置或环境变量读取参数
        if Config:
            self.base_url = base_url or Config.OPENAI_BASE_URL or None
            self.api_key = api_key or Config.OPENAI_API_KEY
            self.model = model or Config.OPENAI_MODEL
            self.temperature = temperature if temperature is not None else Config.OPENAI_TEMPERATURE
        else:
            # Fallback to environment variables
            self.base_url = base_url or os.environ.get('OPENAI_BASE_URL') or None
            self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
            self.model = model or os.environ.get('OPENAI_MODEL', 'gpt-5')
            self.temperature = temperature if temperature is not None else float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))
        
        # 验证必需参数
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY 未设置。请设置环境变量 OPENAI_API_KEY 或在配置文件中配置。"
            )
        
        # 验证 base_url（如果未设置，抛出错误而不是使用硬编码值）
        if not self.base_url:
            raise ValueError(
                "OPENAI_BASE_URL 未设置。请设置环境变量 OPENAI_BASE_URL 或在配置文件中配置。"
            )
        
        # 设置向量数据库存储路径
        if vector_store_path is None:
            # 使用默认路径：项目根目录下的 data/vectorDatabase
            base_dir = Path(__file__).parent.parent
            vector_store_path = str(base_dir / "data" / "vectorDatabase")
        
        self.vector_store_path = Path(vector_store_path)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化LLM（使用已经处理好的 self 属性）
        self.llm = ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature
        )
        
        # Initialize Embeddings
        # Use local HuggingFace model, supports Chinese and English
        # Model will be saved to vectorDatabase/models directory
        try:
            # Create model cache directory
            model_cache_dir = self.vector_store_path / "models"
            model_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Set environment variables to specify model cache directory
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(model_cache_dir)
            os.environ['HF_HOME'] = str(model_cache_dir)
            
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            
            from sentence_transformers import SentenceTransformer
            
            # Pre-load model to ensure proper loading and avoid meta tensor issues
            # Auto-detect GPU if available
            try:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                if device == 'cuda':
                    print(f"✅ 检测到 GPU，使用 CUDA 加速: {torch.cuda.get_device_name(0)}")
                else:
                    print("ℹ️  未检测到 GPU，使用 CPU")
            except ImportError:
                device = 'cpu'
                print("ℹ️  PyTorch 未安装，使用 CPU")
            
            try:
                st_model = SentenceTransformer(
                    model_name,
                    cache_folder=str(model_cache_dir),
                    device=device
                )
                _ = st_model.encode("test", normalize_embeddings=True)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load embedding model from {model_cache_dir}. "
                    f"Please ensure the model is downloaded correctly. Error: {str(e)}"
                ) from e
            
            # Create HuggingFaceEmbeddings wrapper
            try:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': device},
                    encode_kwargs={'normalize_embeddings': True}
                )
                test_embedding = self.embeddings.embed_query("test")
                if test_embedding is None or len(test_embedding) == 0:
                    raise ValueError("Embedding test failed, returned empty vector")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create HuggingFaceEmbeddings wrapper. "
                    f"Model loaded successfully but wrapper failed. Error: {str(e)}"
                ) from e
        except ImportError as e:
            print(f"❌ 错误: 缺少必要的依赖库")
            print(f"   错误详情: {str(e)}")
            print("   请安装: pip install sentence-transformers")
            self.embeddings = None
        except Exception as e:
            print(f"❌ 错误: 无法初始化Embeddings")
            print(f"   错误详情: {str(e)}")
            print("   请确保已安装: pip install sentence-transformers")
            print("   如果问题持续，请检查网络连接和磁盘空间")
            import traceback
            traceback.print_exc()
            self.embeddings = None
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 每个chunk的大小
            chunk_overlap=200,  # chunk之间的重叠
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
        # 向量数据库
        self.vector_store: Optional[FAISS] = None
        
        # 文档元数据
        self.doc_metadata: Dict[str, Dict] = {}
    
    def _extract_filename(self, file_dir: Path) -> str:
        """Extract filename from file directory"""
        # Try metadata.json
        metadata_file = file_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    if filename := metadata.get('original_filename'):
                        return filename
            except:
                pass
        
        # Try filename_info.json
        filename_info_file = file_dir / "filename_info.json"
        if filename_info_file.exists():
            try:
                with open(filename_info_file, 'r', encoding='utf-8') as f:
                    filename_info = json.load(f)
                    if filename := filename_info.get('original_filename'):
                        return filename
            except:
                pass
        
        # Extract from directory name
        dir_name = file_dir.name
        if '-' in dir_name:
            # Try PDF format: filename.pdf-uuid
            parts = dir_name.rsplit('.pdf-', 1)
            if len(parts) == 2:
                return parts[0] + '.pdf'
            # Try other extensions
            for ext in ['.md', '.txt', '.docx', '.doc']:
                if ext in dir_name:
                    parts = dir_name.rsplit(ext + '-', 1)
                    if len(parts) == 2:
                        return parts[0] + ext
            # Use longest part as filename
            return max(dir_name.split('-'), key=len)
        return dir_name
    
    def list_libraries(self) -> List[Dict]:
        """
        列出所有可用的文库
        
        Returns:
            文库列表，每个文库包含id、name、display_name等信息
        """
        base_dir = Path(__file__).parent.parent
        libraries_dir = base_dir / "data" / "output" / "libraries"
        
        libraries = []
        
        if not libraries_dir.exists():
            print(f"⚠️ 文库目录不存在: {libraries_dir}")
            return libraries
        
        # 遍历所有文库目录
        for library_dir in libraries_dir.iterdir():
            if not library_dir.is_dir():
                continue
            
            library_id = library_dir.name
            
            # 读取文库信息
            library_info = {
                'id': library_id,
                'name': library_id,
                'display_name': library_id,
                'description': ''
            }
            
            info_file = library_dir / "info.json"
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        library_info = json.load(f)
                except Exception as e:
                    print(f"⚠️ 读取文库信息失败 {library_id}: {str(e)}")
            
            libraries.append(library_info)
        
        return libraries
    
    def load_papers_from_library(self, library_id: str = "default") -> List[Dict]:
        """
        从文库中加载论文
        
        Args:
            library_id: 文库ID
            
        Returns:
            论文文档列表
        """
        base_dir = Path(__file__).parent.parent
        library_dir = base_dir / "data" / "output" / "libraries" / library_id
        
        if not library_dir.exists():
            print(f"⚠️ 文库目录不存在: {library_dir}")
            return []
        
        # 读取文库信息
        library_info = {
            'id': library_id,
            'name': library_id,
            'display_name': library_id,
            'description': ''
        }
        info_file = library_dir / "info.json"
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    library_info = json.load(f)
                    print(f"📚 加载文库: {library_info.get('display_name', library_id)}")
            except Exception as e:
                print(f"⚠️ 读取文库信息失败: {str(e)}")
        
        papers = []
        
        # 遍历文库中的所有文件目录
        for file_dir in library_dir.iterdir():
            if not file_dir.is_dir() or file_dir.name == "info.json":
                continue
            
            # 查找full.md文件（可能在子目录中）
            md_file = file_dir / "full.md"
            actual_file_dir = file_dir
            
            # 如果当前目录没有full.md，检查子目录
            if not md_file.exists():
                for sub_dir in file_dir.iterdir():
                    if sub_dir.is_dir():
                        potential_md = sub_dir / "full.md"
                        if potential_md.exists():
                            md_file = potential_md
                            actual_file_dir = sub_dir
                            break
                
                if not md_file.exists():
                    continue
            
            # 读取Markdown内容
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                filename = self._extract_filename(actual_file_dir) or "未命名文档"
                
                # 从filename_info.json获取正确的file_id，如果没有则从目录名提取
                file_id = None
                filename_info_file = actual_file_dir / "filename_info.json"
                if filename_info_file.exists():
                    try:
                        with open(filename_info_file, 'r', encoding='utf-8') as f:
                            file_info = json.load(f)
                            file_id = file_info.get('file_id')
                    except:
                        pass
                
                # 如果无法从filename_info.json获取，从目录名提取
                if not file_id:
                    dir_name = file_dir.name
                    # 如果目录名包含_b1后缀，去掉它
                    if dir_name.endswith('_b1'):
                        # 尝试从目录名提取file_id（格式：{文件名}-{file_id} 或 {file_id}_b1）
                        if '-' in dir_name:
                            # 格式：{文件名}-{file_id}
                            file_id = dir_name.rsplit('-', 1)[-1]
                        else:
                            # 格式：{file_id}_b1
                            file_id = dir_name.replace('_b1', '')
                    else:
                        # 如果目录名包含-，提取最后一部分作为file_id
                        if '-' in dir_name:
                            file_id = dir_name.rsplit('-', 1)[-1]
                        else:
                            file_id = dir_name
                
                papers.append({
                    'file_id': file_id,
                    'library_id': library_id,
                    'library_name': library_info.get('display_name', library_id),
                    'filename': filename,
                    'content': content,
                    'path': str(md_file)
                })
                
                print(f"✅ 加载论文: {filename} (file_id: {file_id}, dir: {file_dir.name})")
                
            except Exception as e:
                print(f"⚠️ 加载论文失败: {file_dir.name}, 错误: {str(e)}")
                continue
        
        print(f"📚 共加载 {len(papers)} 篇论文")
        return papers
    
    def build_vector_store(self, papers: List[Dict], library_id: str = "default") -> bool:
        """
        构建向量数据库
        
        Args:
            papers: 论文列表
            library_id: 文库ID
            
        Returns:
            是否成功
        """
        if not self.embeddings:
            print("❌ Embeddings未初始化，无法构建向量数据库")
            return False
        
        if not papers:
            print("⚠️ 没有论文可处理")
            return False
        
        # Clear existing vector store and metadata before building new one
        # This ensures we don't mix data from different libraries
        self.vector_store = None
        
        # Use local metadata dictionary to avoid being overwritten by concurrent requests
        # Only update self.doc_metadata after successful save
        local_metadata = {}
        all_documents = []
        
        # 处理每篇论文
        for paper in papers:
            content = paper['content']
            file_id = paper['file_id']
            filename = paper['filename']
            library_name = paper.get('library_name', library_id)
            
            # 分割文本
            chunks = self.text_splitter.split_text(content)
            
            # 创建文档对象
            for i, chunk in enumerate(chunks):
                from langchain_core.documents import Document
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'file_id': file_id,
                        'library_id': library_id,
                        'library_name': library_name,
                        'filename': filename,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                )
                all_documents.append(doc)
            
            # 保存文档元数据到局部变量
            local_metadata[file_id] = {
                'filename': filename,
                'library_id': library_id,
                'library_name': library_name,
                'chunk_count': len(chunks)
            }
        
        print(f"📝 共生成 {len(all_documents)} 个文本块")
        
        # 构建向量数据库
        try:
            print("🔄 正在构建向量数据库...")
            # Create vector store in local variable first
            vector_store = FAISS.from_documents(all_documents, self.embeddings)
            
            # 保存向量数据库
            store_path = self.vector_store_path / f"{library_id}_faiss"
            vector_store.save_local(str(store_path))
            print(f"✅ 向量数据库已保存到: {store_path}")
            
            # 保存元数据（使用局部变量，避免被并发请求覆盖）
            metadata_path = self.vector_store_path / f"{library_id}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(local_metadata, f, ensure_ascii=False, indent=2)
            
            # Only update instance variables after successful save
            # This ensures data consistency
            self.vector_store = vector_store
            self.doc_metadata = local_metadata
            
            return True
            
        except Exception as e:
            print(f"❌ 构建向量数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_vector_store_exists(self, library_id: str = "default") -> tuple[bool, int]:
        """
        检查向量数据库是否存在，不实际加载
        
        Args:
            library_id: 文库ID
            
        Returns:
            (是否存在, 论文数量)
        """
        store_path = self.vector_store_path / f"{library_id}_faiss"
        
        if not store_path.exists():
            return False, 0
        
        # Check metadata file to get paper count
        metadata_path = self.vector_store_path / f"{library_id}_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    paper_count = len(metadata) if isinstance(metadata, dict) else 0
                    return True, paper_count
            except Exception:
                return True, 0
        
        return True, 0
    
    def load_vector_store(self, library_id: str = "default") -> bool:
        """
        加载已存在的向量数据库
        
        Args:
            library_id: 文库ID
            
        Returns:
            是否成功
        """
        if not self.embeddings:
            print("❌ Embeddings未初始化，无法加载向量数据库")
            return False
        
        store_path = self.vector_store_path / f"{library_id}_faiss"
        
        if not store_path.exists():
            print(f"⚠️ 向量数据库不存在: {store_path}")
            return False
        
        try:
            print(f"🔄 正在加载向量数据库: {store_path}")
            # Clear existing vector store and metadata before loading new one
            self.vector_store = None
            self.doc_metadata = {}
            
            self.vector_store = FAISS.load_local(
                str(store_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # 加载元数据
            metadata_path = self.vector_store_path / f"{library_id}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.doc_metadata = json.load(f)
            
            print(f"✅ 向量数据库加载成功，包含 {len(self.doc_metadata)} 篇论文")
            return True
            
        except Exception as e:
            print(f"❌ 加载向量数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_rag_chain(self, k: int = 4, file_id: Optional[str] = None):
        """
        创建RAG检索链
        
        Args:
            k: 检索的文档数量
            file_id: 如果指定，只检索该文件的内容（None表示检索所有论文）
            
        Returns:
            RAG链
        """
        if not self.vector_store:
            raise ValueError("向量数据库未初始化，请先构建或加载向量数据库")
        
        # 定义检索器
        # 注意：FAISS不支持metadata过滤，所以我们需要在检索后过滤
        # 如果指定了file_id，需要检索更多文档然后过滤
        search_k = k * 10 if file_id else k  # 如果过滤，需要检索更多以确保有足够结果
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": search_k}
        )
        
        # 定义提示词模板
        template = """你是一个世界级论文专家，擅长分析和回答学术论文相关的问题。

请基于以下上下文信息回答用户的问题。如果上下文中没有相关信息，请说明你无法从提供的文档中找到答案。

上下文信息：
{context}

问题：{question}

请提供详细、准确的回答："""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个世界级论文专家。"),
            ("user", template)
        ])
        
        # 构建RAG链
        def filter_docs(docs):
            """过滤文档（如果指定了file_id）"""
            if file_id:
                filtered = [doc for doc in docs if doc.metadata.get('file_id') == file_id]
                return filtered[:k] if filtered else []
            return docs[:k]
        
        def format_docs(docs):
            """格式化检索到的文档"""
            formatted = []
            for doc in docs:
                filename = doc.metadata.get('filename', '未知文档')
                library_name = doc.metadata.get('library_name', '')
                chunk_index = doc.metadata.get('chunk_index', 0)
                if library_name:
                    formatted.append(f"[来源: {library_name} - {filename}, 片段: {chunk_index+1}]\n{doc.page_content}")
                else:
                    formatted.append(f"[来源论文: {filename}, 片段: {chunk_index+1}]\n{doc.page_content}")
            return "\n\n---\n\n".join(formatted)
        
        rag_chain = (
            {"context": retriever | filter_docs | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def query(self, question: str, k: int = 4, file_id: Optional[str] = None) -> str:
        """
        查询RAG系统
        
        Args:
            question: 问题
            k: 检索的文档数量
            file_id: 如果指定，只查询该文件的内容（None表示查询整个数据库）
            
        Returns:
            回答
        """
        if not self.vector_store:
            return "❌ 向量数据库未初始化，请先构建或加载向量数据库"
        
        try:
            rag_chain = self.create_rag_chain(k=k, file_id=file_id)
            response = rag_chain.invoke(question)
            return response
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"
    
    def query_with_sources(self, question: str, k: int = 4, file_id: Optional[str] = None) -> Dict:
        """
        查询RAG系统并返回来源信息
        
        Args:
            question: 问题
            k: 检索的文档数量
            file_id: 如果指定，只查询该文件的内容（None表示查询整个数据库）
            
        Returns:
            包含回答和来源的字典
        """
        if not self.vector_store:
            return {
                'answer': "❌ 向量数据库未初始化，请先构建或加载向量数据库",
                'sources': []
            }
        
        try:
            # 如果指定了file_id，验证是否存在
            if file_id:
                if file_id not in self.doc_metadata:
                    return {
                        'answer': f"❌ 错误: 指定的论文 (file_id: {file_id}) 不在向量数据库中",
                        'sources': [],
                        'paper_count': 0,
                        'query_scope': 'single_paper',
                        'error': 'file_not_found'
                    }
                
                # FAISS不支持metadata过滤，检索更多文档然后过滤
                search_k = max(k * 20, 100)
                retriever = self.vector_store.as_retriever(search_kwargs={"k": search_k})
                all_docs = retriever.invoke(question)
                docs = [doc for doc in all_docs if doc.metadata.get('file_id') == file_id]
                
                if len(docs) < k:
                    search_k = max(search_k * 2, 200)
                    retriever = self.vector_store.as_retriever(search_kwargs={"k": search_k})
                    all_docs = retriever.invoke(question)
                    docs = [doc for doc in all_docs if doc.metadata.get('file_id') == file_id]
                
                if not docs:
                    return {
                        'answer': f"❌ 无法从指定论文中找到相关内容。请尝试：\n1. 检查问题是否与论文内容相关\n2. 尝试使用更具体的关键词\n3. 确保论文已正确加载到向量数据库",
                        'sources': [],
                        'paper_count': 0,
                        'query_scope': 'single_paper',
                        'error': 'no_matching_content'
                    }
                docs = docs[:k]
            else:
                retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
                docs = retriever.invoke(question)
            
            # 获取回答
            rag_chain = self.create_rag_chain(k=k, file_id=file_id)
            answer = rag_chain.invoke(question)
            
            # 整理来源信息
            sources = []
            unique_papers = set()
            for doc in docs:
                paper_file_id = doc.metadata.get('file_id', '')
                if file_id and paper_file_id != file_id:
                    continue
                unique_papers.add(paper_file_id)
                sources.append({
                    'filename': doc.metadata.get('filename', '未知文档'),
                    'library_name': doc.metadata.get('library_name', ''),
                    'file_id': paper_file_id,
                    'chunk_index': doc.metadata.get('chunk_index', 0),
                    'content_preview': doc.page_content[:200] + "..."
                })
            
            return {
                'answer': answer,
                'sources': sources,
                'paper_count': len(unique_papers),
                'query_scope': 'single_paper' if file_id else 'all_papers'
            }
        except Exception as e:
            return {
                'answer': f"❌ 查询失败: {str(e)}",
                'sources': []
            }


def main(library_id: Optional[str] = None):
    """
    主函数 - 示例用法
    
    Args:
        library_id: 论文库ID，如果为None则交互式选择或使用默认值
    """
    print("=" * 60)
    print("📚 论文数据库RAG检索系统")
    print("=" * 60)
    
    # 初始化RAG系统
    rag_system = PaperRAGSystem()
    
    # 如果没有指定library_id，列出所有可用文库让用户选择
    if library_id is None:
        print("\n📚 可用的论文库:")
        libraries = rag_system.list_libraries()
        
        if not libraries:
            print("⚠️ 未找到任何论文库，使用默认库 'default'")
            library_id = "default"
        else:
            print("\n请选择要使用的论文库:")
            for i, lib in enumerate(libraries, 1):
                print(f"  {i}. {lib.get('display_name', lib['id'])} (ID: {lib['id']})")
                if lib.get('description'):
                    print(f"     描述: {lib['description']}")
            
            try:
                choice = input("\n请输入序号 (直接回车使用默认库 'default'): ").strip()
                if choice:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(libraries):
                        library_id = libraries[choice_idx]['id']
                        print(f"✅ 已选择: {libraries[choice_idx].get('display_name', library_id)}")
                    else:
                        print("⚠️ 无效选择，使用默认库 'default'")
                        library_id = "default"
                else:
                    library_id = "default"
                    print("✅ 使用默认库 'default'")
            except (ValueError, KeyboardInterrupt):
                print("\n⚠️ 输入无效，使用默认库 'default'")
                library_id = "default"
    
    # 方式1: 从文库加载论文并构建向量数据库
    print(f"\n1️⃣ 从文库加载论文 (库ID: {library_id})...")
    papers = rag_system.load_papers_from_library(library_id=library_id)
    
    if papers:
        print("\n2️⃣ 构建向量数据库...")
        success = rag_system.build_vector_store(papers, library_id=library_id)
        
        if not success:
            print(f"\n🔄 尝试加载已存在的向量数据库 (库ID: {library_id})...")
            rag_system.load_vector_store(library_id=library_id)
    else:
        print(f"\n🔄 未找到论文，尝试加载已存在的向量数据库 (库ID: {library_id})...")
        rag_system.load_vector_store(library_id=library_id)
    
    # 方式2: 直接查询（如果向量数据库已存在）
    if rag_system.vector_store:
        print("\n3️⃣ 开始查询...")
        print("-" * 60)
        
        # 示例查询
        questions = [
            "agent最火的论文是哪个？",
            "论文中提到了哪些关键技术？",
            "总结一下论文的主要贡献"
        ]
        
        for question in questions:
            print(f"\n❓ 问题: {question}")
            print("-" * 60)
            
            # 查询并显示结果（查询整个数据库）
            result = rag_system.query_with_sources(question, k=3)
            
            print(f"📊 查询范围: {'单篇论文' if result.get('query_scope') == 'single_paper' else '整个论文数据库'}")
            if result.get('paper_count'):
                print(f"📄 涉及论文数: {result['paper_count']} 篇")
            
            print(f"\n💡 回答:\n{result['answer']}")
            
            if result['sources']:
                print(f"\n📚 来源片段 ({len(result['sources'])} 个):")
                for i, source in enumerate(result['sources'], 1):
                    library_name = source.get('library_name', '')
                    if library_name:
                        print(f"  {i}. [{library_name}] {source['filename']} (片段 {source['chunk_index']+1})")
                    else:
                        print(f"  {i}. {source['filename']} (片段 {source['chunk_index']+1})")
                    print(f"     预览: {source['content_preview']}")
            
            print("\n" + "=" * 60)
        
        # 示例：查询单篇论文
        if rag_system.doc_metadata:
            print("\n" + "=" * 60)
            print("📝 示例：查询单篇论文")
            print("=" * 60)
            
            # 获取第一篇论文的file_id
            first_file_id = list(rag_system.doc_metadata.keys())[0]
            first_filename = rag_system.doc_metadata[first_file_id]['filename']
            
            print(f"\n📄 查询论文: {first_filename}")
            print(f"📋 File ID: {first_file_id}")
            print("-" * 60)
            
            question = "这篇论文的主要贡献是什么？"
            print(f"\n❓ 问题: {question}")
            
            result = rag_system.query_with_sources(question, k=3, file_id=first_file_id)
            
            print(f"📊 查询范围: 单篇论文 ({first_filename})")
            print(f"\n💡 回答:\n{result['answer']}")
            
            if result['sources']:
                print(f"\n📚 来源片段 ({len(result['sources'])} 个):")
                for i, source in enumerate(result['sources'], 1):
                    library_name = source.get('library_name', '')
                    if library_name:
                        print(f"  {i}. [{library_name}] {source['filename']} (片段 {source['chunk_index']+1})")
                    else:
                        print(f"  {i}. {source['filename']} (片段 {source['chunk_index']+1})")
    else:
        print("\n❌ 无法初始化向量数据库，请检查配置")


if __name__ == "__main__":
    import sys
    
    # 支持命令行参数传入library_id
    # 用法: python test_rag.py library_d8fd90da
    library_id = None
    if len(sys.argv) > 1:
        library_id = sys.argv[1]
        print(f"📋 从命令行参数获取库ID: {library_id}")
    
    main(library_id=library_id)


