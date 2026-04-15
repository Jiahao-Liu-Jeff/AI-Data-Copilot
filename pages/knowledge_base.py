"""知识库管理页面 - 仅管理员可见"""
import os
import streamlit as st
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.document_loader import load_single_document
import auth


def render():
    """渲染知识库管理页面"""

    # 检查登录状态
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("请先登录")
        if st.button("返回登录页"):
            st.switch_page("pages/login.py")
        return

    user_info = st.session_state.user_info
    username = user_info["username"]

    # 检查管理员权限
    if user_info["role"] != "admin":
        st.error("❌ 您没有权限访问此页面")
        if st.button("返回聊天"):
            st.switch_page("pages/main_chat.py")
        return

    # 页面标题
    st.title("📂 知识库管理")
    st.markdown("管理员可在此上传、查看和删除知识库文档")

    # 顶部用户栏
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"👤 **{user_info.get('display_name', username)}** ({username})")
    with col2:
        if st.button("← 返回聊天"):
            st.switch_page("pages/main_chat.py")

    st.divider()

    # 文档目录
    docs_dir = "data/docs"

    # 1. 上传新文档
    st.subheader("📤 上传文档")

    uploaded_file = st.file_uploader(
        "选择 Markdown 文件",
        type=["md", "txt"],
        help="支持 .md 和 .txt 格式"
    )

    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            content = uploaded_file.getvalue().decode("utf-8")
            st.markdown("**文件预览:**")
            st.code(content[:1000], language="markdown")
        with col2:
            st.write(f"📄 **{uploaded_file.name}**")
            st.write(f"大小: {len(content)} 字符")

        if st.button("✅ 上传到知识库"):
            # 保存文件
            os.makedirs(docs_dir, exist_ok=True)
            file_path = os.path.join(docs_dir, uploaded_file.name)

            # 如果文件已存在，先删除
            if os.path.exists(file_path):
                os.remove(file_path)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            st.success(f"✅ 文件 '{uploaded_file.name}' 已上传到知识库")

            # 清除向量存储缓存，强制重新加载
            from agent import sql_agent
            sql_agent.reset_rag()
            st.info("💡 请在聊天页面点击「重新初始化 RAG」以更新知识库索引")

            st.rerun()

    st.divider()

    # 2. 已有文档列表
    st.subheader("📚 已有文档")

    if not os.path.exists(docs_dir):
        st.warning("知识库目录不存在")
    else:
        files = [f for f in os.listdir(docs_dir) if f.endswith((".md", ".txt"))]

        if not files:
            st.info("知识库中暂无文档")
        else:
            for filename in files:
                file_path = os.path.join(docs_dir, filename)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)

                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.write(f"📄 **{filename}**")
                        st.caption(f"大小: {file_size} bytes | 修改时间: {modified_time}")

                    with col2:
                        # 下载
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        st.download_button(
                            "📥 下载",
                            file_content,
                            filename,
                            key=f"download_{filename}"
                        )

                    with col3:
                        # 查看内容（使用 expander）
                        with st.expander("👁️ 查看内容"):
                            st.markdown(file_content)

                    with col4:
                        # 删除
                        if st.button("🗑️ 删除", key=f"delete_{filename}"):
                            os.remove(file_path)
                            st.warning(f"文件 '{filename}' 已删除")
                            st.rerun()

                st.divider()

    # 3. 重新索引提示
    st.divider()
    st.subheader("🔄 重新索引")

    from agent import sql_agent
    st.caption(f"当前 RAG 状态: {'✅ 已启用' if sql_agent.is_rag_available() else '❌ 已禁用'}")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 重新初始化 RAG"):
            with st.spinner("正在重新初始化 RAG..."):
                rag_ok = sql_agent.init_rag(force=True)
            if rag_ok:
                st.success("RAG 初始化成功！")
            else:
                st.error("RAG 初始化失败")
            st.rerun()
    with col2:
        st.info("如果上传新文档后 RAG 检索结果不正确，请点击重新初始化 RAG")


if __name__ == "__main__":
    render()
