
import openai
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

client = None

st.set_page_config(
    page_title="Bot dạy học",
    layout= "wide",
    initial_sidebar_state="expanded"
)
st.title("🏠 Trang chủ")

# print(os.getcwd())

# st.title('🤖💬 OpenAI Chatbot')
input_api_key = st.text_input('Enter OpenAI API token to proceed:', type='password')
env_api_key = os.getenv('OPENAI_API_KEY')

openai_api_key = input_api_key if input_api_key.startswith('sk-') else env_api_key
# print(openai_api_key)
if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your credentials!', icon='⚠️')        
else:
    st.success('Proceed to entering your prompt message!', icon='👉')
    st.session_state['client'] = openai.OpenAI(api_key=openai_api_key)
