"""应用入口 - 路由页面"""
import streamlit as st

# 隐藏 Streamlit 默认导航栏
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_info" not in st.session_state:
    st.session_state.user_info = None

# 根据登录状态决定显示哪个页面
if st.session_state.logged_in:
    # 已登录，显示主聊天页面
    st.switch_page("pages/main_chat.py")
else:
    # 未登录，显示登录页面
    st.switch_page("pages/login.py")
