
import openai
import streamlit as st
import os
from dotenv import load_dotenv
from utils.authentification import require_login, show_user_info, get_current_user

load_dotenv()

client = None

# Cấu hình trang
st.set_page_config(
    page_title="Đăng nhập & Đăng ký",
    page_icon="🔐",
    layout="centered"
)

# ===== KIỂM TRA ĐĂNG NHẬP =====
if not require_login("TutorBot - AI Tutor Assistant"):
    exit()

# Hiển thị thông tin user trong sidebar
show_user_info()
# print(os.getcwd())

# # st.title('🤖💬 OpenAI Chatbot')
# input_api_key = st.text_input('Enter OpenAI API token to proceed:', type='password')
# env_api_key = os.getenv('OPENAI_API_KEY')

# openai_api_key = input_api_key if input_api_key.startswith('sk-') else env_api_key
# # print(openai_api_key)
# if not openai_api_key.startswith('sk-'):
#     st.warning('Please enter your credentials!', icon='⚠️')        
# else:
#     st.success('Proceed to entering your prompt message!', icon='👉')
#     st.session_state['client'] = openai.OpenAI(api_key=openai_api_key)
