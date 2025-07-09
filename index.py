
import openai
import streamlit as st
import os
client = None

st.set_page_config(page_title="My Multipage App")
st.title("🏠 Home Page")


# st.title('🤖💬 OpenAI Chatbot')
# openai_api_key = st.text_input('Enter OpenAI API token to proceed   :', type='password')
# openai_api_key = os.getenv('OPENAI_API_KEY')
# if not openai_api_key.startswith('sk-'):
#     st.warning('Please enter your credentials!', icon='⚠️')        
# else:
#     st.success('Proceed to entering your prompt message!', icon='👉')
#     st.session_state['client'] = openai.OpenAI(api_key=openai_api_key)
