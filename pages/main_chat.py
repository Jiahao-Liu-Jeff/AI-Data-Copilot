"""主聊天页面"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 隐藏 Streamlit 默认导航栏（必须放在最前面）
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

from agent import sql_agent
from agent.memory_store import get_memory_store
import auth


def render():
    """渲染主聊天页面"""

    # 隐藏默认的多页面导航
    st.set_page_config(
        page_title="AI Data Copilot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 检查登录状态
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("请先登录")
        if st.button("返回登录页"):
            st.switch_page("pages/login.py")
        return

    user_info = st.session_state.user_info
    username = user_info["username"]
    is_admin_user = user_info["role"] == "admin"

    # 页面标题
    st.title("🤖 AI Data Copilot")
    st.markdown("基于自然语言的 SQL 查询助手，支持业务文档 RAG 检索")

    # 顶部用户栏
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.write(f"👤 **{user_info.get('display_name', username)}** ({username})")
    with col2:
        st.write(f"角色: {'管理员' if is_admin_user else '普通用户'}")
    with col3:
        if st.button("登出", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    st.divider()

    # 侧边栏 - 会话历史
    with st.sidebar:
        st.title("💬 会话历史")

        # 获取用户的会话列表
        memory_store = get_memory_store()
        conversations = memory_store.list_conversations(username)

        # 新建会话按钮
        if st.button("➕ 新建会话", use_container_width=True):
            st.session_state.current_conv_id = f"conv_{len(conversations) + 1}"
            st.session_state.messages = []
            st.session_state.loaded_from_db = False
            st.rerun()

        st.divider()

        # 当前会话
        current_conv = st.session_state.get("current_conv_id", "default")

        for conv in conversations:
            conv_id = conv["conversation_id"]
            conv_title = conv.get("conversation_title", conv_id)
            updated_at = conv.get("updated_at", "")[:16] if conv.get("updated_at") else ""

            # 截取显示名称（使用标题，最多显示25个字符）
            display_name = conv_title if len(conv_title) <= 25 else conv_title[:22] + "..."

            button_type = "primary" if conv_id == current_conv else "secondary"

            if st.button(f"💬 {display_name}", key=f"conv_{conv_id}", use_container_width=True, type=button_type):
                # 切换会话
                st.session_state.current_conv_id = conv_id
                st.session_state.messages = []
                st.session_state.loaded_from_db = False
                st.rerun()

        st.divider()

        # RAG 状态
        st.caption(f"📚 RAG: {'✅ 已启用' if sql_agent.is_rag_available() else '❌ 已禁用'}")

        if is_admin_user:
            st.divider()
            if st.button("📂 知识库管理", use_container_width=True):
                st.switch_page("pages/knowledge_base.py")

    # 初始化消息
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_conv_id" not in st.session_state:
        st.session_state.current_conv_id = "default"

    if "loaded_from_db" not in st.session_state:
        st.session_state.loaded_from_db = False

    # 加载当前会话的历史
    if not st.session_state.loaded_from_db:
        current_conv = st.session_state.current_conv_id
        memory_store = get_memory_store()
        db_messages = memory_store.load(username, current_conv)

        st.session_state.messages = []
        for msg in db_messages:
            if isinstance(msg, dict):
                msg_type = msg.get("type", "")
                msg_content = msg.get("content", "")
                if msg_type == "human":
                    st.session_state.messages.append({"role": "user", "content": msg_content})
                elif msg_type == "ai":
                    st.session_state.messages.append({"role": "assistant", "content": msg_content})

        st.session_state.loaded_from_db = True

    # 显示历史消息（只显示当前会话的，不累积显示之前的）
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # 输入框
    user_input = st.chat_input("输入你的问题...")

    if user_input:
        # 显示用户消息
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 调用 Agent
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("思考中..."):
                    current_conv = st.session_state.current_conv_id
                    result = sql_agent.run(
                        user_input,
                        user_id=username,
                        conversation_id=current_conv
                    )
                    st.markdown(result)
                    st.session_state.messages.append({"role": "assistant", "content": result})
        except Exception as e:
            error_msg = f"出错: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    render()
