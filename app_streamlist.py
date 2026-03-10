# app_streamlist.py
import streamlit as st
from agent import sql_agent

user_input = st.text_area("输入你的问题：")
if st.button("提交"):
    if user_input:
        result = sql_agent.run(user_input)
        st.text_area("结果", value = result, height = 400)