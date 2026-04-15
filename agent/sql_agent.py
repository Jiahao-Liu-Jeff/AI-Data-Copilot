import os
import sqlite3
from typing import Optional
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

from agent.memory_store import UserMemoryStore, get_memory_store


# ---------------- LLM 初始化 ----------------
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ---------------- RAG 全局状态 ----------------
_rag_initialized = False
_rag_available = False

# ---------------- RAG 初始化 ----------------
def init_rag(doc_dir: str = "data/docs", force: bool = False):
    """
    初始化 RAG 系统
    如果 embedding 模型下载失败，会跳过 RAG 但不影响 SQL 功能

    Args:
        doc_dir: 业务文档目录
        force: 是否强制重新初始化

    Returns:
        bool: RAG 是否可用
    """
    global _rag_initialized, _rag_available

    # 避免重复初始化（除非强制）
    if _rag_initialized and not force:
        return _rag_available

    # 强制重新初始化时，先重置状态
    if force:
        _rag_initialized = False

    # 设置代理（如果环境变量未设置）
    os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:1087")
    os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:1087")

    try:
        from agent.vector_store import VectorStoreManager
        from agent.document_loader import load_documents
        from agent.rag_tool import set_vector_store_manager

        vector_store_manager = VectorStoreManager(persist_directory="data/vector_db")

        # 检查向量存储是否已存在
        if os.path.exists("data/vector_db") and os.listdir("data/vector_db"):
            try:
                vector_store_manager.load()
                set_vector_store_manager(vector_store_manager)
                _rag_available = True
                print("RAG 已加载")
            except Exception as e:
                print(f"RAG 加载失败: {e}")
                _rag_available = False
        else:
            # 创建新的向量存储
            if os.path.exists(doc_dir):
                docs = load_documents(doc_dir)
                if docs:
                    vector_store_manager.create_from_documents(docs)
                    set_vector_store_manager(vector_store_manager)
                    _rag_available = True
                    print(f"RAG 已创建，共 {len(docs)} 个文档块")
                else:
                    print("文档目录为空")
                    _rag_available = False
            else:
                print(f"文档目录不存在: {doc_dir}")
                _rag_available = False
    except Exception as e:
        print(f"RAG 初始化失败: {e}")
        _rag_available = False

    _rag_initialized = True
    return _rag_available


def reset_rag():
    """重置 RAG 状态（用于测试或重新初始化）"""
    global _rag_initialized, _rag_available
    _rag_initialized = False
    _rag_available = False


def is_rag_available():
    """检查 RAG 是否可用"""
    return _rag_available


# ---------------- 数据库查询工具 ----------------
def sql_query_tool(query: str) -> str:
    """接收 SQL 查询字符串，执行 SQLite 并返回结果字符串"""
    conn = sqlite3.connect("data/orders.db")
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return str(result)
    except Exception as e:
        return f"SQL 执行出错: {e}"
    finally:
        conn.close()


# ---------------- 创建 Agent ----------------
def create_agent(user_id: str = "default", conversation_id: str = "default") -> tuple:
    """
    创建为特定用户定制的 Agent

    Args:
        user_id: 用户标识
        conversation_id: 会话标识

    Returns:
        (agent, memory_store, conversation_id) 元组
    """
    # 获取持久化记忆存储
    memory_store = get_memory_store()

    # 加载该用户的对话历史
    messages = memory_store.load(user_id, conversation_id)

    # 创建 Memory，将历史消息加载进去
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    if messages:
        # 恢复对话历史到 memory
        for msg in messages:
            if isinstance(msg, dict):
                msg_type = msg.get("type", "")
                msg_content = msg.get("content", "")
                if msg_type == "human":
                    memory.chat_memory.add_user_message(msg_content)
                elif msg_type == "ai":
                    memory.chat_memory.add_ai_message(msg_content)

    # 获取 RAG 工具（仅在 RAG 可用时）
    all_tools = [
        Tool(
            name="SQL Database",
            func=sql_query_tool,
            description="用于执行 SQL 查询。输入完整 SQL，返回查询结果。"
        )
    ]

    # 只有 RAG 可用时才添加 RAG 工具
    if is_rag_available():
        from agent.rag_tool import get_rag_tools
        all_tools.extend(get_rag_tools())

    # 初始化 Agent
    agent = initialize_agent(
        all_tools,
        llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False
    )

    return agent, memory_store, conversation_id


# ---------------- 持久化对话历史 ----------------
def save_conversation(
    memory_store: UserMemoryStore,
    user_id: str,
    conversation_id: str,
    memory: ConversationBufferMemory,
    conversation_title: str = None
) -> None:
    """
    保存对话历史到持久化存储

    Args:
        memory_store: 记忆存储器实例
        user_id: 用户标识
        conversation_id: 会话标识
        memory: ConversationBufferMemory 实例
        conversation_title: 会话标题（第一个用户问题）
    """
    # 从 memory 中获取消息历史
    messages = []
    for msg in memory.chat_memory.messages:
        if hasattr(msg, 'type') and hasattr(msg, 'content'):
            messages.append({
                "type": msg.type,
                "content": msg.content
            })

    # 如果没有标题，从第一个用户问题中提取
    if not conversation_title:
        for msg in messages:
            if msg.get("type") == "human":
                conversation_title = msg.get("content", "")[:50]
                break

    memory_store.save(user_id, conversation_id, messages, conversation_title)


# ---------------- 主循环 ----------------
def run_agent():
    """交互式运行 Agent（单用户版本）"""
    print("=== AI SQL Agent ===")
    print("初始化 RAG 系统...")
    init_rag()

    user_id = "cli_user"
    conversation_id = "default"

    agent, memory_store, conversation_id = create_agent(user_id, conversation_id)

    print("Agent 初始化完成，输入问题开始对话（exit/quit 退出）")
    while True:
        try:
            user_input = input("问题: ")
            if user_input.lower() in ["exit", "quit"]:
                # 保存对话历史
                save_conversation(memory_store, user_id, conversation_id, agent.memory)
                print("对话已保存，退出 Agent")
                break
            result = agent.run(input=user_input)
            print("=== Agent 输出 ===")
            print(result)
        except KeyboardInterrupt:
            save_conversation(memory_store, user_id, conversation_id, agent.memory)
            print("\n对话已保存，手动退出 Agent")
            break


def run(user_input: str, user_id: str = "default", conversation_id: str = "default") -> str:
    """
    运行 Agent 处理用户输入

    Args:
        user_input: 用户问题
        user_id: 用户标识
        conversation_id: 会话标识

    Returns:
        Agent 的输出结果
    """
    # 确保 RAG 已初始化
    init_rag()

    agent, memory_store, conv_id = create_agent(user_id, conversation_id)

    # 获取当前对话历史，用于判断是否是第一个问题
    current_messages = memory_store.load(user_id, conversation_id)
    is_first_message = len(current_messages) == 0

    result = agent.run(input=user_input)

    # 保存对话历史，传入第一个问题作为标题
    title = user_input[:50] if is_first_message else None
    save_conversation(memory_store, user_id, conv_id, agent.memory, title)

    return result


# ---------------- Web 入口 ----------------
def create_run_func(user_id: str = "web_user"):
    """
    创建带用户隔离的 run 函数

    Args:
        user_id: 用户标识

    Returns:
        可调用的 run 函数
    """
    def run_with_user(
        user_input: str,
        conversation_id: str = "default"
    ) -> str:
        return run(user_input, user_id=user_id, conversation_id=conversation_id)

    return run_with_user
