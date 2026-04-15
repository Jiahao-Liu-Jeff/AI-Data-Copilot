"""向量存储模块 - 使用 ChromaDB 存储和检索文档向量"""
import os
from typing import List, Optional
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(
        self,
        persist_directory: str = "data/vector_db"
    ):
        """
        初始化向量存储管理器

        Args:
            persist_directory: 向量数据库持久化路径
        """
        self.persist_directory = persist_directory
        self._vectordb: Optional[Chroma] = None
        self._embeddings: Optional[HuggingFaceBgeEmbeddings] = None

    def _get_embeddings(self):
        """获取本地嵌入模型（延迟初始化）"""
        if self._embeddings is None:
            self._embeddings = HuggingFaceBgeEmbeddings(
                model_name="BAAI/bge-small-zh-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        return self._embeddings

    def create_from_documents(
        self,
        documents: List[Document],
        collection_name: str = "business_docs"
    ) -> Chroma:
        """
        从文档列表创建向量存储

        Args:
            documents: Document 列表
            collection_name: 集合名称

        Returns:
            Chroma 向量数据库实例
        """
        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        embeddings = self._get_embeddings()

        self._vectordb = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=self.persist_directory,
            collection_name=collection_name
        )

        return self._vectordb

    def load(self, collection_name: str = "business_docs") -> Chroma:
        """
        加载已有的向量存储

        Args:
            collection_name: 集合名称

        Returns:
            Chroma 向量数据库实例
        """
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError(f"向量存储不存在: {self.persist_directory}")

        embeddings = self._get_embeddings()

        self._vectordb = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        return self._vectordb

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        搜索最相关的文档

        Args:
            query: 查询文本
            k: 返回数量
            filter_dict: 过滤条件

        Returns:
            相关文档列表
        """
        if self._vectordb is None:
            self.load()

        results = self._vectordb.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )

        return results

    def add_documents(self, documents: List[Document]) -> None:
        """
        添加新文档到向量存储

        Args:
            documents: Document 列表
        """
        if self._vectordb is None:
            raise ValueError("向量存储未初始化，请先调用 create_from_documents 或 load")

        self._vectordb.add_documents(documents)
        self._vectordb.persist()

    def get_relevant_context(self, query: str, k: int = 5) -> str:
        """
        获取与查询相关的上下文内容

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            合并的上下文字符串
        """
        docs = self.search(query, k=k)

        if not docs:
            return ""

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[文档{i}](来源: {source}):\n{doc.page_content}")

        return "\n\n".join(context_parts)
