import streamlit as st
from openai import OpenAI
from prompts.prompts import Tutor_prompt
import os
import dotenv
import json
import uuid
from pathlib import Path

from RAG.processPDF import load_pdf_data, read_vectordb, ask_with_monica, template

SESSION_FILE = "chat_sessions.json"

def load_sessions():
    if Path(SESSION_FILE).exists():
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sessions(sessions):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

dotenv.load_dotenv()
st.title("TutorBot 📚")

# Sidebar: Quản lý phiên chat
st.sidebar.title("Lịch sử phiên chat")
sessions = load_sessions()
if "current_session_id" not in st.session_state:
    if sessions:
        st.session_state["current_session_id"] = sessions[-1]["id"]
    else:
        st.session_state["current_session_id"] = None

# Nút Chat mới
if st.sidebar.button("Chat mới"):
    st.session_state["confirm_new"] = True

if st.session_state.get("confirm_new"):
    st.sidebar.warning("Bạn có chắc muốn tạo phiên chat mới?")
    col_new1, col_new2 = st.sidebar.columns(2)
    if col_new1.button("Xác nhận"):
        new_id = str(uuid.uuid4())
        new_session = {"id": new_id, "name": "", "messages": []}
        sessions.append(new_session)
        save_sessions(sessions)
        st.session_state["current_session_id"] = new_id
        st.session_state["messages"] = []
        st.session_state["confirm_new"] = False
        st.rerun()
    if col_new2.button("Huỷ"):
        st.session_state["confirm_new"] = False

# Hiển thị danh sách phiên chat
for s in sessions:
    display_name = s["name"] if s["name"] else "Phiên mới"
    col1, col2 = st.sidebar.columns([8,1])
    if col1.button(display_name, key=s["id"]):
        st.session_state["current_session_id"] = s["id"]
        st.session_state["messages"] = s["messages"]
        st.session_state["show_menu"] = None
        st.rerun()
    with col2:
        if st.button("⋮", key="menu_"+s["id"]):
            st.session_state["show_menu"] = s["id"]
        if st.session_state.get("show_menu") == s["id"]:
            if st.button("Delete", key="delete_"+s["id"]):
                st.session_state["confirm_delete"] = s["id"]
            if st.session_state.get("confirm_delete") == s["id"]:
                st.sidebar.warning("Bạn có chắc muốn xoá phiên này?")
                col_del1, col_del2 = st.sidebar.columns(2)
                if col_del1.button("Xác nhận xoá", key="confirm_delete_btn_"+s["id"]):
                    sessions = [sess for sess in sessions if sess["id"] != s["id"]]
                    save_sessions(sessions)
                    st.session_state["show_menu"] = None
                    st.session_state["confirm_delete"] = None
                    if st.session_state["current_session_id"] == s["id"]:
                        if sessions:
                            st.session_state["current_session_id"] = sessions[-1]["id"]
                            st.session_state["messages"] = sessions[-1]["messages"]
                        else:
                            st.session_state["current_session_id"] = None
                            st.session_state["messages"] = []
                    st.rerun()
                if col_del2.button("Huỷ", key="cancel_delete_btn_"+s["id"]):
                    st.session_state["confirm_delete"] = None

if st.session_state["current_session_id"]:
    session = next((s for s in sessions if s["id"] == st.session_state["current_session_id"]), None)
    if session:
        st.session_state["messages"] = session["messages"]
else:
    st.session_state["messages"] = []

# Monica client
monica_api_key = os.getenv('MONICA_API_KEY', '')
st.session_state['client'] = OpenAI(
    base_url="https://openapi.monica.im/v1",
    api_key=monica_api_key,
)

# Hiển thị chat messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input: text hoặc file PDF
col1, col2 = st.columns([3, 1])
with col1:
    prompt = st.chat_input("Nhập câu hỏi:")
with col2:
    uploaded_file = st.file_uploader("📄 PDF", type=["pdf"], label_visibility="collapsed")

if uploaded_file and prompt:
    with st.chat_message("user"):
        st.markdown(f"📄 **Đã tải lên file:** `{uploaded_file.name}`\n\n💬 **Câu hỏi:** {prompt}")

    # Lưu file PDF vào thư mục data/
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    pdf_path = data_dir / uploaded_file.name
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Đang xử lý PDF và xây dựng vector DB…"):
        load_pdf_data()

    db = read_vectordb()

    with st.chat_message("assistant"):
        answer = ask_with_monica(db, prompt, template)
        st.markdown(answer)

    st.session_state["messages"].append({"role": "user", "content": f"Tải lên file: {uploaded_file.name}\n\nCâu hỏi: {prompt}"})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    for s in sessions:
        if s["id"] == st.session_state["current_session_id"]:
            s["messages"] = st.session_state["messages"]
    save_sessions(sessions)

elif prompt and not uploaded_file:
    # Nếu chỉ có prompt không có file PDF → xử lý bình thường
    st.session_state["messages"].append({"role": "user", "content": prompt})
    for s in sessions:
        if s["id"] == st.session_state["current_session_id"]:
            if len(st.session_state["messages"]) == 1:
                short_name = prompt if len(prompt) <= 30 else prompt[:27] + "..."
                s["name"] = short_name
            s["messages"] = st.session_state["messages"]
    save_sessions(sessions)

    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        messages = [{"role": "system", "content": Tutor_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

        try:
            for response in st.session_state['client'].chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=messages,
                stream=True
            ):
                content = getattr(response.choices[0].delta, "content", "")
                full_response += content if isinstance(content, str) else ""
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            for s in sessions:
                if s["id"] == st.session_state["current_session_id"]:
                    s["messages"] = st.session_state["messages"]
            save_sessions(sessions)
        except Exception as e:
            st.error(f"An error occurred: {e}")
