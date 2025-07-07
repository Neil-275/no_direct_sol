import streamlit as st 
import openai
from prompts.prompts import Tutor_prompt


st.title("TutorBot")

if "messages" not in st.session_state:
    st.session_state["messages"] = []


for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""


        messages = [{"role": "system", "content": Tutor_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

        for response in st.session_state['client'].chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True):
            content = getattr(response.choices[0].delta, "content", "")
            full_response += content if type(content) == str else ""
            message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})    