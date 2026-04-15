#!/usr/bin/env python
"""RAG 系统初始化脚本"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.document_loader import load_documents
from agent.vector_store import VectorStoreManager


def main():
    print("=== 初始化 RAG 系统 ===\n")

    doc_dir = "data/docs"
    persist_dir = "data/vector_db"

    # 检查文档目录
    if not os.path.exists(doc_dir):
        print(f"❌ 文档目录不存在: {doc_dir}")
        print("请创建 data/docs 目录并放入 .txt 或 .md 文档")
        return

    # 加载文档
    print(f"📄 加载文档 from {doc_dir}...")
    try:
        docs = load_documents(doc_dir)
        print(f"   加载了 {len(docs)} 个文档块\n")
    except Exception as e:
        print(f"❌ 加载文档失败: {e}")
        return

    # 创建向量存储
    print(f"🗃️  创建向量存储到 {persist_dir}...")
    try:
        manager = VectorStoreManager(persist_directory=persist_dir)
        manager.create_from_documents(docs)
        print(f"✅ 向量存储创建成功！共 {len(docs)} 个文档块")
    except Exception as e:
        print(f"❌ 创建向量存储失败: {e}")
        return

    print("\n=== RAG 初始化完成 ===")
    print("现在可以启动应用了：")
    print("  streamlit run app_streamlit.py")


if __name__ == "__main__":
    main()
