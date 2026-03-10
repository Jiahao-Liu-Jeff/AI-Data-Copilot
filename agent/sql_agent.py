import os
import sqlite3
import pandas as pd
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

# ---------------- LLM 初始化 ----------------
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

memory = ConversationBufferMemory(
    memory_key="chat_history",   # 内部存储的 key，Agent 会使用它来读取/写入对话
    return_messages=True         # 返回消息对象而不是纯文本
)

# ---------------- 数据库查询工具 ----------------
def sql_query_tool(query: str) -> str:
    """接收 SQL 查询字符串，执行 SQLite 并返回结果字符串"""
    conn = sqlite3.connect("data/orders.db")
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return str(result)
        # df = pd.read_sql_query(query, conn)
        # return df.to_string(index=False)
    except Exception as e:
        return f"SQL 执行出错: {e}"
    finally:
        conn.close()

# ---------------- 定义 Tools ----------------
tools = [
    Tool(
        name="SQL Database",
        func=sql_query_tool,
        description="用于执行 SQL 查询。输入完整 SQL，返回查询结果。"
    )
]

# ---------------- 初始化 Agent ----------------
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False
)

# ---------------- 主循环 ----------------
def run_agent():
    print("=== AI SQL Agent ===")
    while True:
        try:
            user_input = input("问题: ")
            if user_input.lower() in ["exit", "quit"]:
                print("退出 Agent")
                break
            result = agent.run(input=user_input)
            print("=== Agent 输出 ===")
            print(result)
        except KeyboardInterrupt:
            print("\n手动退出 Agent")
            break