"""登录页面"""
import streamlit as st
import sys
import os

# 添加项目根目录到 sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import auth


def render():
    """渲染登录页面"""

    # 页面配置
    st.set_page_config(
        page_title="登录 - AI Data Copilot",
        page_icon="🔐",
        layout="centered"
    )

    st.title("🔐 AI Data Copilot")
    st.markdown("请登录以继续")

    # 登录表单
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")

        submitted = st.form_submit_button("登录", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("请输入用户名和密码")
            else:
                user_info = auth.verify_user(username, password)
                if user_info:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_info
                    st.switch_page("pages/main_chat.py")
                else:
                    st.error("用户名或密码错误")

    # 底部提示
    st.divider()
    st.caption("默认用户:")
    st.code("""
    管理员: admin / admin123
    普通用户: user1 / user123
    """, language=None)


if __name__ == "__main__":
    render()
