"""文档加载模块 - 支持加载本地 .txt, .md 文件并分割"""
import os
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document


def load_documents(doc_dir: str, glob_pattern: str = "**/*.md") -> List[Document]:
    """
    加载指定目录下的所有文档

    Args:
        doc_dir: 文档目录路径
        glob_pattern: 文件匹配模式，默认为 **/*.md

    Returns:
        Document 列表
    """
    if not os.path.exists(doc_dir):
        raise FileNotFoundError(f"文档目录不存在: {doc_dir}")

    # 支持 .md 文件
    loader = DirectoryLoader(
        doc_dir,
        glob=glob_pattern,
        loader_cls=TextLoader,
        show_progress=True
    )

    docs = loader.load()

    if not docs:
        print(f"警告: 未找到匹配 {glob_pattern} 的文档")

    # 文本分割
    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separator="\n"
    )

    split_docs = splitter.split_documents(docs)
    return split_docs


def load_single_document(file_path: str) -> List[Document]:
    """
    加载单个文档文件

    Args:
        file_path: 文件路径

    Returns:
        Document 列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    loader = TextLoader(file_path)
    docs = loader.load()

    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separator="\n"
    )

    return splitter.split_documents(docs)
