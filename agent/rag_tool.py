"""RAG Tool - 供 Agent 调用进行文档检索"""
from langchain.agents import Tool
from agent.vector_store import VectorStoreManager


# 全局向量存储管理器实例（单例）
_vector_store_manager: VectorStoreManager = None


def get_vector_store_manager() -> VectorStoreManager:
    """获取向量存储管理器单例"""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager


def set_vector_store_manager(manager: VectorStoreManager) -> None:
    """设置向量存储管理器"""
    global _vector_store_manager
    _vector_store_manager = manager


def document_retrieval_tool_func(query: str) -> str:
    """
    文档检索工具函数

    根据用户问题检索相关业务文档，返回文档内容作为上下文。

    Args:
        query: 用户的问题

    Returns:
        检索到的相关文档内容，如果无结果返回空字符串
    """
    try:
        manager = get_vector_store_manager()
        context = manager.get_relevant_context(query, k=3)

        if not context:
            return "未找到相关业务文档"

        return f"以下是相关的业务文档内容：\n\n{context}"
    except Exception as e:
        return f"文档检索出错: {str(e)}"


def create_rag_tool() -> Tool:
    """
    创建 RAG 检索工具

    Returns:
        LangChain Tool 实例
    """
    return Tool(
        name="Business Document Retrieval",
        func=document_retrieval_tool_func,
        description="""当用户询问涉及公司业务、业务流程、业务术语、指标定义等问题时使用此工具。
        输入是用户的自然语言问题，此工具会检索相关的内部业务文档并返回内容。
        如果问题与业务知识无关，此工具可能返回空结果。"""
    )


def get_rag_tools() -> list[Tool]:
    """
    获取所有 RAG 相关工具

    Returns:
        Tool 列表
    """
    return [create_rag_tool()]
