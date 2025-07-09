import streamlit as st 
from openai import OpenAI
from prompts.prompts import Tutor_prompt
import os
import dotenv
import json
import uuid

SESSION_FILE = "chat_sessions.json"

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sessions(sessions):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

dotenv.load_dotenv()
st.title("TutorBot")

# Sidebar: Quản lý phiên chat
st.sidebar.title("Lịch sử phiên chat")
sessions = load_sessions()
if "current_session_id" not in st.session_state:
    if sessions:
        st.session_state["current_session_id"] = sessions[-1]["id"]
    else:
        st.session_state["current_session_id"] = None

# Nút Chat mới với xác nhận
if st.sidebar.button("Chat mới"):
    st.session_state["confirm_new"] = True

if st.session_state.get("confirm_new"):
    st.sidebar.warning("Bạn có chắc muốn tạo phiên chat mới?")
    col_new1, col_new2 = st.sidebar.columns(2)
    if col_new1.button("Xác nhận"):
        new_id = str(uuid.uuid4())
        new_session = {
            "id": new_id,
            "name": "",
            "messages": []
        }
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
    if col1.button(s["name"], key=s["id"]):
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
                    # Nếu đang ở phiên vừa xoá thì chuyển sang phiên cuối hoặc rỗng
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

# Load messages cho phiên hiện tại
if st.session_state["current_session_id"]:
    session = next((s for s in sessions if s["id"] == st.session_state["current_session_id"]), None)
    if session:
        st.session_state["messages"] = session["messages"]
else:
    st.session_state["messages"] = []

# Input cho Monica API key
monica_api_key = os.getenv('MONICA_API_KEY', '')

# Monica client
st.session_state['client'] = OpenAI(
    base_url="https://openapi.monica.im/v1",
    api_key=monica_api_key,
)

# Hiển thị chat messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Nếu là câu chat đầu tiên, cập nhật tên phiên
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

        # Chuẩn bị messages cho API
        messages = [{"role": "system", "content": Tutor_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

        # Gọi API Monica
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
            # Lưu lại vào session hiện tại và file NGAY SAU KHI assistant trả lời
            for s in sessions:
                if s["id"] == st.session_state["current_session_id"]:
                    s["messages"] = st.session_state["messages"]
            save_sessions(sessions)
        except Exception as e:
            st.error(f"An error occurred: {e}")