import streamlit as st 
from openai import OpenAI
from prompts.prompts import Tutor_prompt
import os
import dotenv
import json
import uuid
from datetime import datetime
import time

SESSION_FILE = "chat_sessions.json"

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
st.set_page_config(
    page_title="TutorBot - AI Tutor Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open('UI_component/Chat_component.html', 'r') as file:
    html_content = file.read()
# Custom CSS for modern UI
st.markdown(html_content, unsafe_allow_html=True)

# Load environment variables
dotenv.load_dotenv()

# Initialize session state
if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "show_menu" not in st.session_state:
    st.session_state["show_menu"] = None
if "confirm_new" not in st.session_state:
    st.session_state["confirm_new"] = False
if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None
if "typing" not in st.session_state:
    st.session_state["typing"] = False

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
    st.markdown("### 💬 Quản lý phiên chat")
    
    # Statistics
    total_sessions = len(sessions)
    total_messages = sum(len(s.get("messages", [])) for s in sessions)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Phiên chat", total_sessions)
    with col2:
        st.metric("Tin nhắn", total_messages)
    
    st.markdown("---")
    
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
                new_session = {
                    "id": new_id,
                    "name": "",
                    "messages": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                sessions.append(new_session)
                save_sessions(sessions)
                st.session_state["current_session_id"] = new_id
                st.session_state["messages"] = []
                st.session_state["confirm_new"] = False
                st.success("✅ Đã tạo phiên chat mới!")
                time.sleep(1)
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
                            
                            st.success("✅ Đã xóa phiên chat!")
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button("❌ Hủy", key=f"cancel_delete_{session['id']}"):
                            st.session_state["confirm_delete"] = None
                            st.rerun()
                
                st.markdown("---")

# Main chat area
col1, col2 = st.columns([3, 1])

with col1:
    # Current session info
    if st.session_state["current_session_id"]:
        current_session = next((s for s in sessions if s["id"] == st.session_state["current_session_id"]), None)
        if current_session:
            session_name = current_session.get("name", "") or get_session_preview(current_session.get("messages", []))
            st.markdown(f"### 💬 {session_name}")
            st.caption(f"📅 Tạo: {format_timestamp(current_session.get('created_at'))} | 🔄 Cập nhật: {format_timestamp(current_session.get('updated_at'))}")
            st.session_state["messages"] = current_session.get("messages", [])
    else:
        st.markdown("### 💬 Chọn phiên chat hoặc tạo mới")
        st.info("👈 Hãy chọn một phiên chat từ sidebar hoặc tạo phiên mới để bắt đầu trò chuyện!")

with col2:
    # Quick actions
    st.markdown("### ⚡ Thao tác nhanh")
    if st.button("🔄 Làm mới", use_container_width=True):
        st.rerun()
    
    if st.button("📤 Xuất chat", use_container_width=True):
        if st.session_state["messages"]:
            chat_export = {
                "session_id": st.session_state["current_session_id"],
                "messages": st.session_state["messages"],
                "exported_at": datetime.now().isoformat()
            }
            st.download_button(
                "💾 Tải xuống",
                data=json.dumps(chat_export, ensure_ascii=False, indent=2),
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("Không có tin nhắn để xuất!")

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
    
    # Chat input
    if prompt := st.chat_input("💭 Đặt câu hỏi hoặc bắt đầu cuộc trò chuyện..."):
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        # Update session name if first message
        for s in sessions:
            if s["id"] == st.session_state["current_session_id"]:
                if len(st.session_state["messages"]) == 1:
                    s["name"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
                s["messages"] = st.session_state["messages"]
                s["updated_at"] = datetime.now().isoformat()
        save_sessions(sessions)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get Monica API key
        monica_api_key = os.getenv('MONICA_API_KEY', '')
        
        if not monica_api_key:
            st.error("❌ Không tìm thấy Monica API key. Vui lòng kiểm tra file .env")
        else:
            # Initialize Monica client
            client = OpenAI(
                base_url="https://openapi.monica.im/v1",
                api_key=monica_api_key,
            )
            
            # Generate response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Set typing indicator
                st.session_state["typing"] = True
                
                # Prepare messages for API
                messages = [{"role": "system", "content": Tutor_prompt}]
                messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
                
                try:
                    # Stream response
                    for response in client.chat.completions.create(
                        model="gemini-2.0-flash-exp",
                        messages=messages,
                        stream=True
                    ):
                        content = getattr(response.choices[0].delta, "content", "")
                        full_response += content if isinstance(content, str) else ""
                        message_placeholder.markdown(full_response + "▌")
                    
                    # Final response
                    message_placeholder.markdown(full_response)
                    st.session_state["typing"] = False
                    
                    # Add assistant message
                    st.session_state["messages"].append({"role": "assistant", "content": full_response})
                    
                    # Save session
                    for s in sessions:
                        if s["id"] == st.session_state["current_session_id"]:
                            s["messages"] = st.session_state["messages"]
                            s["updated_at"] = datetime.now().isoformat()
                    save_sessions(sessions)
                    
                    # Show success message
                    st.success("✅ Phản hồi hoàn tất!")
                    
                except Exception as e:
                    st.session_state["typing"] = False
                    st.error(f"❌ Đã xảy ra lỗi: {str(e)}")
                    st.error("Vui lòng thử lại sau hoặc kiểm tra kết nối mạng.")

# Footer
# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; color: #666; margin-top: 2rem;">
#     <p>🎓 TutorBot - Trợ lý AI thông minh cho việc học tập</p>
#     <p>Được tạo bởi Streamlit và Monica AI</p>
# </div>
# """, unsafe_allow_html=True)import streamlit as st 
import openai
from prompts.prompts import Tutor_prompt, Classify_prompt
import os
import requests
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from typing import TypedDict
from typing import List, Dict, Any
from dotenv import load_dotenv
import json

load_dotenv()

st.title("Bot dạy học")
math_solver_api = os.getenv('MATH_SOLVER')
math_tutor_api = os.getenv('MATH_TUTOR')

#define langgraph state
class ChatState(TypedDict):
    messages:List[Dict[str, Any]] = []
    ground_truth: str = ""
    problem: str = ""
    student_solution: str = ""
    student_get_it_right: int = 0

#define langgraph tool
@tool
def get_solver(problem:str):
    """Get solution for a math problem"""
    payload = {"prompt": problem}
    response = requests.post(math_solver_api, json=payload)
    result = response.json()
    return result.get('response')

@tool # để có thể sử dụng được invoke
def get_tutor_response(history_chat: list, problem: str, ground_truth: str):
    """Get tutor response """
    def create_diaglouge(history_chat):
        res = ""
        for message in history_chat:
            if message['role'] == "user":
                res += f"Student: {message['content']}\n"
            else:
                res += f"Teacher: {message['content']}\n"

        return res
    dialouge = create_diaglouge(history_chat[1:])
    user_prompt = f"""
        Problem: {problem}
        Ground truth solution: {ground_truth}
        Dialogue_history: {dialouge}
    """
    print("+++User prompt:", user_prompt)
    payload = {"prompt": user_prompt, "language": "Tiếng Việt"}

    response = requests.post(math_tutor_api, json=payload)
    result = response.json()
    print(result)
    return result.get('response')

from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o-mini", temperature=0.4)

model = model.bind_tools([get_solver, get_tutor_response])

classify_client = openai.OpenAI()

def identify_intent(state: ChatState):
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    student_get_it_right = state["student_get_it_right"]
    last_message = messages[-1]["content"]
    # print("Messages: ",last_message)
    response = classify_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": Classify_prompt(problem, student_solution, ground_truth, last_message)},
            ]
    )
    print("Extraction: ", response)
    result = json.loads(response.choices[0].message.content)
    # print("Extraction: ", result)
    if problem == "" and result["problem"] != "":
        state['problem'] = result['problem']
    if state['student_solution'] == "":
        state['student_solution'] = result['student_solution']
    if state['student_get_it_right'] == "":
        state['student_get_it_right'] = result['student_get_it_right']
    
    return state

def which_tool(state: ChatState): #conditional edge
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    student_get_it_right = state["student_get_it_right"]
    last_message = messages[-1]["content"]
    typee = ""
    if problem == "":
        return "call_general_chat"
    if problem != "" and ground_truth == "":
        return 'solver'
    if problem != "" and student_solution == "":
        return "call_general_chat"
    if problem != "" and student_solution != "" and student_get_it_right == 0:
        return "tutor"
    return "call_general_chat"
    

def call_general_chat(state):
    messages = state["messages"]
    response = model.invoke(messages)
    messages.append({"role": "assistant", "content": response.content})
    state["messages"] = messages
    return state


def solver(state: ChatState):
    problem = state['problem']
    ground_truth = get_solver.invoke({"problem": problem})
    state['ground_truth'] = ground_truth
    # state.messagesappend({"role": "assistant", "content": f"Here is the solution: {ground_truth}"})
    return state

def tutor(state: ChatState):
    problem = state['problem']
    ground_truth = state['ground_truth']
    messages = state['messages']
    response = get_tutor_response.invoke({"history_chat":messages,"problem": problem, "ground_truth": ground_truth})
    messages.append({"role": "assistant", "content": response})
    state["messages"] = messages
    return state


workflow = StateGraph(ChatState)


workflow.add_node('dummy_node', identify_intent)
workflow.add_node('tutor', tutor)
workflow.add_node('solver', solver)
workflow.add_node('call_general_chat', call_general_chat)

workflow.add_conditional_edges(
    'dummy_node',
    which_tool,
    ['tutor','solver','call_general_chat']
)

workflow.add_edge(START,'dummy_node')
workflow.add_edge('tutor',END) 
workflow.add_edge('solver','dummy_node')
workflow.add_edge('call_general_chat',END) 

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

app = workflow.compile(checkpointer=memory)
config = {'configurable': {"thread_id": "1"}}


import re

def convert_latex_to_markdown(text):
    # Pattern to match the entire LaTeX block
    pattern = r"\\\[(.*?)\\\]"
    
    # Function to replace each match with markdown LaTeX block
    def replacer(match):
        content = match.group(1).strip()
        return f"$$\n{content}\n$$"

    # Replace using re.sub with DOTALL to capture multiline LaTeX
    new_text = re.sub(pattern, replacer, text, flags=re.DOTALL)
    
    return new_text




### Streamlit session
if "messages" not in st.session_state:
    st.session_state["messages"] = [{'role':'assistant','content': 'Chào bạn, tôi là gia sư toán, có bằng tốt nghiệp xuất sắc sư phạm toán. Tôi có thể giúp gì được cho bạn'}]

if "problem" not in st.session_state:
    st.session_state["problem"] = ""

if "ground_truth" not in st.session_state:
    st.session_state["ground_truth"] = ""

if "student_solution" not in st.session_state:
    st.session_state["student_solution"] = ""

if "student_get_it_right" not in st.session_state:
    st.session_state["student_get_it_right"] = 0

# Render các message trước
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Hỏi gì ?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        messages = [{"role": "system", "content": Tutor_prompt}]
        # messages = []
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
        # print(messages)
        
        # out = app.invoke({'messages': messages,
        #                 'problem': st.session_state['problem'],
        #                 'ground_truth': st.session_state['ground_truth']},
        #                 config)
        print("+++++++++++++++++ New iteration ++++++++++++++++++")
        for step in app.stream({'messages': messages,
                                'problem': st.session_state['problem'],
                                'ground_truth': st.session_state['ground_truth'],
                                'student_solution': st.session_state['student_solution'],
                                'student_get_it_right': st.session_state['student_get_it_right']},
                                config,
                                stream_mode='updates'):
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
        if st.session_state['problem'] == "" and last_state['problem']:
            st.session_state['problem'] = last_state['problem']
        
        if st.session_state['ground_truth'] == "" and last_state['ground_truth']:
            st.session_state['ground_truth'] = last_state['ground_truth']
        full_response = convert_latex_to_markdown(last_state['messages'][-1]['content'])

        # for response in st.session_state['client'].chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=messages,
        #     stream=True):
        #     content = getattr(response.choices[0].delta, "content", "")
        #     full_response += content if type(content) == str else ""
        #     message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})    