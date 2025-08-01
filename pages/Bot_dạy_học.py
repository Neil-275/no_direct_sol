import streamlit as st 
from openai import OpenAI
from prompts.prompts import Tutor_prompt
import os
import dotenv
import json
import uuid
from datetime import datetime
import time
# from utils.web_search import serpapi_search
from utils.agent import construct_agent
from utils.convert_latex import convert_latex_to_markdown
from RAG.processPDF import update_pdf_data, read_vectordb, ask_with_monica, template, init_faiss_db

from utils.convert_latex import convert_latex_to_markdown
from utils.authentification import require_login, show_user_info, get_current_user



st.set_page_config(
    page_title="TutorBot - AI Tutor Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
if not require_login("TutorBot - AI Tutor Assistant"):
    exit()

# Hiển thị thông tin user trong sidebar
show_user_info()


@st.cache_resource
def get_agent():
    """Cache the agent to avoid recreating it on every rerun"""
    return construct_agent()

# Get cached agent
agent = get_agent()

SESSION_FILE = "chat_sessions.json"

def handle_normal_chat(prompt, sessions, agent, Tutor_prompt):
   
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI()

    # Tin nhắn hệ thống + lịch sử
    messages = [{"role": "system", "content": Tutor_prompt}]
    messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    config = {'configurable': {"thread_id": "1"}}

    # Hiển thị assistant typing
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        print("+++++++++++++++++ New iteration ++++++++++++++++++")
        for step in agent.stream(
            {
                'messages': messages,
                'problem': st.session_state['problem'],
                'ground_truth': st.session_state['ground_truth'],
                'student_solution': st.session_state['student_solution'],
                'student_get_it_right': st.session_state['student_get_it_right'],
                'web_query': "",
            },
            config,
            stream_mode='updates'
        ):
            key = list(step.keys())[0]
            print("_________________\nStep output:")
            print("Node: ", list(step.keys())[0])
            print("messages:", step[key]['messages'][-1])
            for k in step[key].keys():
                if k != "messages":
                    print(f"{k}: {step[key][k]}")
            out = step

        last_state = None
        if out.get("call_general_chat"):
            last_state = out["call_general_chat"]
        if out.get("tutor"):
            last_state = out["tutor"]
        if out.get("web_search"):
            last_state = out["web_search"]

        if st.session_state['problem'] == "" and last_state['problem']:
            st.session_state['problem'] = last_state['problem']
        if st.session_state['ground_truth'] == "" and last_state['ground_truth']:
            st.session_state['ground_truth'] = last_state['ground_truth']

        full_response = convert_latex_to_markdown(last_state['messages'][-1]['content'])
        message_placeholder.markdown(full_response)
        st.session_state["typing"] = False

        # Thêm tin nhắn assistant
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

        # Cập nhật session
        for s in sessions:
            if s["id"] == st.session_state["current_session_id"]:
                s["messages"] = st.session_state["messages"]
                s["updated_at"] = datetime.now().isoformat()
        save_sessions(sessions)

        # Hiển thị trạng thái
        success_placeholder = st.empty()
        success_placeholder.success("✅ Phản hồi hoàn tất!")
        time.sleep(2)
        success_placeholder.empty()

def handle_rag_chat(prompt, sessions, db, template, file_filter=None):
    with st.chat_message("user"):
        st.markdown(prompt)

    # Thêm user message vào session state
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # Cập nhật session name nếu là tin nhắn đầu
    user_messages = [m for m in st.session_state["messages"] if m["role"] == "user"]
    for s in sessions:
        if s["id"] == st.session_state["current_session_id"]:
            if len(user_messages) == 1:
                s["name"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
            s["messages"] = st.session_state["messages"]
            s["updated_at"] = datetime.now().isoformat()
    save_sessions(sessions)

    # Query RAG
    result = ask_with_monica(db, prompt, template, file_filter=file_filter)
    print(f"RAG result: {result}")
    with st.chat_message("assistant"):
        st.markdown(result)

    st.session_state["messages"].append({"role": "assistant", "content": result})

    # Cập nhật session
    for s in sessions:
        if s["id"] == st.session_state["current_session_id"]:
            s["messages"] = st.session_state["messages"]
            s["updated_at"] = datetime.now().isoformat()
    save_sessions(sessions)

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sessions(sessions):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def get_session_preview(messages, max_length=50):
    """Get a preview of the session from the first user message"""
    if not messages:
        return "Phiên trống"
    
    first_user_msg = next((msg for msg in messages if msg["role"] == "user"), None)
    if not first_user_msg:
        return "Phiên trống"
    
    preview = first_user_msg["content"].strip()
    return preview[:max_length] + "..." if len(preview) > max_length else preview

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d/%m %H:%M")
    except:
        return datetime.now().strftime("%d/%m %H:%M")

# Configure page
# st.set_page_config(
#     page_title="TutorBot - AI Tutor Assistant",
#     page_icon="🎓",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

with open('UI_component/Chat_component.html', 'r') as file:
    html_content = file.read()
# Custom CSS for modern UI
st.markdown(html_content, unsafe_allow_html=True)

# Load environment variables
dotenv.load_dotenv()

# Initialize session state
if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = None
if "show_menu" not in st.session_state:
    st.session_state["show_menu"] = None
if "confirm_new" not in st.session_state:
    st.session_state["confirm_new"] = False
if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None
if "typing" not in st.session_state:
    st.session_state["typing"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "problem" not in st.session_state:
    st.session_state["problem"] = ""
if "ground_truth" not in st.session_state:
    st.session_state["ground_truth"] = ""
if "student_solution" not in st.session_state:
    st.session_state["student_solution"] = ""
if "student_get_it_right" not in st.session_state:
    st.session_state["student_get_it_right"] = 0


# Main header
st.markdown("""
<div class="main-header">
    <h1>🎓 TutorBot</h1>
    <p>Trợ lý AI thông minh cho việc học tập</p>
</div>
""", unsafe_allow_html=True)

# Load sessions
sessions = load_sessions()

# Sidebar for session management
with st.sidebar:
    # New chat button
    if st.button("🆕 Phiên chat mới", type="primary", use_container_width=True):
        st.session_state["confirm_new"] = True
        st.rerun()
    
    # Confirm new chat
    if st.session_state.get("confirm_new"):
        st.warning("⚠️ Bạn có chắc muốn tạo phiên chat mới?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Xác nhận", type="primary"):
                new_id = str(uuid.uuid4())
                # Tạo tin nhắn chào hỏi
                welcome_message = {'role':'assistant','content': 'Chào bạn, tôi là gia sư toán, có bằng tốt nghiệp xuất sắc sư phạm toán. Tôi có thể giúp gì được cho bạn'}
                new_session = {
                    "id": new_id,
                    "name": "",
                    "messages": [welcome_message],  # Lưu tin nhắn chào hỏi vào session
                    "problem": "",
                    "ground_truth": "",
                    "student_solution": "",
                    "student_get_it_right": "",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                sessions.append(new_session)
                save_sessions(sessions)
                st.session_state["current_session_id"] = new_id
                st.session_state["messages"] = [welcome_message]  # Cập nhật session state
                st.session_state["confirm_new"] = False
                # st.success("✅ Đã tạo phiên chat mới!")
                time.sleep(.5)
                st.rerun()
        with col2:
            if st.button("❌ Hủy"):
                st.session_state["confirm_new"] = False
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Danh sách phiên chat")
    
    if not sessions:
        st.markdown("""
        <div class="empty-state">
            <p>🔍 Chưa có phiên chat nào</p>
            <p>Hãy tạo phiên chat mới để bắt đầu!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Sort sessions by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        for i, session in enumerate(sessions):
            is_current = session["id"] == st.session_state["current_session_id"]
            
            # Session container
            container = st.container()
            with container:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    session_name = session.get("name", "") or get_session_preview(session.get("messages", []))
                    button_type = "primary" if is_current else "secondary"
                    
                    if st.button(
                        f"{'🔵' if is_current else '⚪'} {session_name}",
                        key=f"session_{session['id']}",
                        type=button_type,
                        use_container_width=True
                    ):
                        st.session_state["current_session_id"] = session["id"]
                        st.session_state["messages"] = session.get("messages", [])
                        st.session_state["show_menu"] = None
                        st.rerun()
                
                with col2:
                    if st.button("⋮", key=f"menu_{session['id']}"):
                        st.session_state["show_menu"] = session["id"] if st.session_state.get("show_menu") != session["id"] else None
                        st.rerun()
                
                # Show menu if selected
                if st.session_state.get("show_menu") == session["id"]:
                    if st.button("🗑️ Xóa", key=f"delete_{session['id']}", type="secondary", use_container_width=True):
                        st.session_state["confirm_delete"] = session["id"]
                        st.rerun()
                    
                    # Show session info
                    st.caption(f"📅 {format_timestamp(session.get('created_at'))}")
                    st.caption(f"💬 {len(session.get('messages', []))} tin nhắn")
                
                # Confirm delete
                if st.session_state.get("confirm_delete") == session["id"]:
                    st.error("⚠️ Bạn có chắc muốn xóa phiên này?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Xác nhận", key=f"confirm_delete_{session['id']}", type="primary"):
                            sessions = [s for s in sessions if s["id"] != session["id"]]
                            save_sessions(sessions)
                            st.session_state["show_menu"] = None
                            st.session_state["confirm_delete"] = None
                            
                            # If deleting current session, switch to another or clear
                            if st.session_state["current_session_id"] == session["id"]:
                                if sessions:
                                    st.session_state["current_session_id"] = sessions[0]["id"]
                                    st.session_state["messages"] = sessions[0].get("messages", [])
                                else:
                                    st.session_state["current_session_id"] = None
                                    st.session_state["messages"] = []
                            
                            # st.success("✅ Đã xóa phiên chat!")
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button("❌ Hủy", key=f"cancel_delete_{session['id']}"):
                            st.session_state["confirm_delete"] = None
                            st.rerun()
                
                st.markdown("---")

# Main chat area

# Current session info
if st.session_state["current_session_id"]:
    current_session = next((s for s in sessions if s["id"] == st.session_state["current_session_id"]), None)
    if current_session:
        session_name = current_session.get("name", "") or get_session_preview(current_session.get("messages", []))
        st.markdown(f"### 💬 {session_name}")
        st.caption(f"📅 Tạo: {format_timestamp(current_session.get('created_at'))} | 🔄 Cập nhật: {format_timestamp(current_session.get('updated_at'))}")
        # Đảm bảo messages được sync từ session
        st.session_state["messages"] = current_session.get("messages", [])
else:
    st.markdown("### 💬 Chọn phiên chat hoặc tạo mới")
    st.info("👈 Hãy chọn một phiên chat từ sidebar hoặc tạo phiên mới để bắt đầu trò chuyện!")


# Chat interface
if st.session_state["current_session_id"]:
    # Messages container
    messages_container = st.container()
    
    with messages_container:
        # Display messages
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Typing indicator
        if st.session_state.get("typing"):
            with st.chat_message("assistant"):
                st.markdown("""
                <div class="typing-indicator">
                    <span>TutorBot đang soạn tin nhắn</span>
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    # import streamlit as st

    # with st.popover("Click me for a popup"):
    #     st.write("This is the content of the popup.")
    #     name = st.text_input("Your name")
    #     if name:
    #         st.write(f"Hello, {name}!")
    # Chat input
    with st.sidebar:
        st.markdown("## 🔧 Tuỳ chọn")
        use_rag = st.checkbox("📄 Sử dụng RAG", value=False)
    if prompt := st.chat_input("💭 Đặt câu hỏi hoặc bắt đầu cuộc trò chuyện..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        user_messages = [m for m in st.session_state["messages"] if m["role"] == "user"]
        for s in sessions:
            if s["id"] == st.session_state["current_session_id"]:
                if len(user_messages) == 1:
                    s["name"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
                s["messages"] = st.session_state["messages"]
                s["updated_at"] = datetime.now().isoformat()
        save_sessions(sessions)
        if use_rag:
            db= read_vectordb()
            handle_rag_chat(prompt, sessions, db, template, file_filter=None)
            #handle_rag_chat(prompt, sessions, agent, Tutor_prompt)
        else:
            handle_normal_chat(prompt, sessions, agent, Tutor_prompt)