import streamlit as st
from openai import OpenAI
from prompts.prompts import Tutor_prompt
import os
import dotenv
import json
import uuid
from serpapi import GoogleSearch
import PyPDF2
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

def serpapi_search(query, api_key):
    """Enhanced web search with better error handling and formatting"""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 5,
            "hl": "vi"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])
        
        if not organic:
            return "Không tìm thấy kết quả web search."
        
        output = []
        for i, item in enumerate(organic, 1):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            output.append(f"**{i}. {title}**\n{snippet}\n🔗 {link}")
        
        return "\n\n".join(output)
    except Exception as e:
        return f"⚠️ Không thể lấy kết quả web search: {str(e)}"

def extract_pdf_content(uploaded_files):
    """Extract text content from uploaded PDF files"""
    content = ""
    file_info = []
    
    for uploaded_file in uploaded_files:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            file_content = ""
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                file_content += page_text
            
            content += f"\n\n=== {uploaded_file.name} ===\n{file_content}"
            file_info.append({
                "name": uploaded_file.name,
                "pages": len(reader.pages),
                "size": len(file_content)
            })
        except Exception as e:
            st.error(f"❌ Lỗi đọc file {uploaded_file.name}: {str(e)}")
    
    return content, file_info

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
    page_title="TutorBot - Web Enhanced AI Tutor",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .feature-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        margin: 0 4px;
        display: inline-block;
        backdrop-filter: blur(10px);
    }
    
    .session-item {
        background: white;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .session-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
    .pdf-upload-area {
        background: #f8f9fa;
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    
    .pdf-info {
        background: #e8f4f8;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    .search-result {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .search-result h4 {
        color: #856404;
        margin: 0 0 8px 0;
    }
    
    .typing-indicator {
        display: flex;
        align-items: center;
        margin: 10px 0;
        color: #666;
    }
    
    .typing-dots {
        display: flex;
        margin-left: 10px;
    }
    
    .typing-dots span {
        height: 8px;
        width: 8px;
        background-color: #667eea;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-15px); }
    }
    
    .status-card {
        background: white;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .status-online {
        border-left: 4px solid #28a745;
    }
    
    .status-offline {
        border-left: 4px solid #dc3545;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 2em;
        margin-bottom: 10px;
    }
    
    .web-search-spinner {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .search-indicator {
        display: flex;
        align-items: center;
        background: #e3f2fd;
        border: 1px solid #bbdefb;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 8px 0;
        font-size: 0.9em;
    }
    
    .search-indicator .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #2196f3;
        border-top: 2px solid transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .api-status {
        font-size: 0.9em;
        padding: 8px 12px;
        border-radius: 20px;
        margin: 4px 0;
        display: inline-block;
    }
    
    .api-status.connected {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .api-status.disconnected {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

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
if "searching" not in st.session_state:
    st.session_state["searching"] = False

# Main header
st.markdown("""
<div class="main-header">
    <h1>🌐 TutorBot Web Enhanced</h1>
    <p>Trợ lý AI thông minh với tích hợp Web Search & PDF</p>
    <div>
        <span class="feature-badge">📄 PDF Upload</span>
        <span class="feature-badge">🔍 Web Search</span>
        <span class="feature-badge">🤖 AI Chat</span>
        <span class="feature-badge">💾 Session Save</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Load sessions
sessions = load_sessions()

# API Keys status
monica_api_key = os.getenv('MONICA_API_KEY', '')
serpapi_key = os.getenv('SERPAPI_KEY', '')

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 Cấu hình & Tài liệu")
    
    # API Status
    st.markdown("#### 🔑 Trạng thái API")
    if monica_api_key:
        st.markdown('<div class="api-status connected">✅ Monica API: Đã kết nối</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status disconnected">❌ Monica API: Chưa kết nối</div>', unsafe_allow_html=True)
    
    if serpapi_key:
        st.markdown('<div class="api-status connected">✅ SerpAPI: Đã kết nối</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status disconnected">❌ SerpAPI: Chưa kết nối</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PDF Upload Section
    st.markdown("#### 📄 Tải lên tài liệu PDF")
    uploaded_pdfs = st.file_uploader(
        "Chọn file PDF để tham khảo", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Tải lên các file PDF để TutorBot có thể tham khảo thông tin từ tài liệu của bạn"
    )
    
    pdf_content = ""
    pdf_info = []
    
    if uploaded_pdfs:
        with st.spinner("🔄 Đang xử lý file PDF..."):
            pdf_content, pdf_info = extract_pdf_content(uploaded_pdfs)
        
        if pdf_info:
            st.success(f"✅ Đã tải thành công {len(uploaded_pdfs)} file PDF")
            
            # Display PDF info
            for info in pdf_info:
                st.markdown(f"""
                <div class="pdf-info">
                    <strong>📄 {info['name']}</strong><br>
                    📑 {info['pages']} trang<br>
                    📊 {info['size']} ký tự
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Session Management
    st.markdown("### 💬 Quản lý phiên chat")
    
    # Statistics
    total_sessions = len(sessions)
    total_messages = sum(len(s.get("messages", [])) for s in sessions)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Phiên chat", total_sessions)
    with col2:
        st.metric("Tin nhắn", total_messages)
    
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
        <div style="text-align: center; padding: 2rem; color: #666;">
            <p>🔍 Chưa có phiên chat nào</p>
            <p>Hãy tạo phiên chat mới để bắt đầu!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Sort sessions by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        for session in sessions:
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
            
            # Session metadata
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.caption(f"📅 {format_timestamp(current_session.get('created_at'))}")
            with col_b:
                st.caption(f"💬 {len(current_session.get('messages', []))} tin nhắn")
            with col_c:
                st.caption(f"🔄 {format_timestamp(current_session.get('updated_at'))}")
            
            st.session_state["messages"] = current_session.get("messages", [])
    else:
        st.markdown("### 💬 Chọn phiên chat hoặc tạo mới")
        
        # Feature showcase
        st.markdown("""
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h4>Web Search</h4>
                <p>Tìm kiếm thông tin mới nhất từ internet</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <h4>PDF Upload</h4>
                <p>Tải lên và phân tích tài liệu PDF</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h4>AI Chat</h4>
                <p>Trò chuyện thông minh với AI</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("👈 Hãy chọn một phiên chat từ sidebar hoặc tạo phiên mới để bắt đầu!")

with col2:
    # Quick actions and status
    st.markdown("### ⚡ Thao tác nhanh")
    
    if st.button("🔄 Làm mới", use_container_width=True):
        st.rerun()
    
    if st.button("📤 Xuất chat", use_container_width=True):
        if st.session_state["messages"]:
            chat_export = {
                "session_id": st.session_state["current_session_id"],
                "messages": st.session_state["messages"],
                "pdf_files": [info["name"] for info in pdf_info] if pdf_info else [],
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
    
    # Status indicators
    st.markdown("---")
    st.markdown("### 📊 Trạng thái")
    
    if pdf_info:
        st.markdown(f"📄 **PDF:** {len(pdf_info)} file đã tải")
    else:
        st.markdown("📄 **PDF:** Chưa tải file nào")
    
    if st.session_state.get("searching"):
        st.markdown("🔍 **Web Search:** Đang tìm kiếm...")
    else:
        st.markdown("🔍 **Web Search:** Sẵn sàng")

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
    if prompt := st.chat_input("💭 Đặt câu hỏi, tìm kiếm thông tin hoặc thảo luận về tài liệu..."):
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
        
        # Web search
        web_results = ""
        if serpapi_key:
            st.session_state["searching"] = True
            
            # Show search indicator
            search_placeholder = st.empty()
            with search_placeholder:
                st.markdown("""
                <div class="search-indicator">
                    <div class="spinner"></div>
                    🔍 Đang tìm kiếm thông tin trên internet...
                </div>
                """, unsafe_allow_html=True)
            
            web_results = serpapi_search(prompt, serpapi_key)
            st.session_state["searching"] = False
            search_placeholder.empty()
            
            # Display web results
            if web_results and "Không tìm thấy" not in web_results:
                with st.expander("🔍 Kết quả Web Search", expanded=True):
                    st.markdown(f"""
                    <div class="search-result">
                        <h4>🌐 Thông tin từ Internet</h4>
                        {web_results}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Check API keys
        if not monica_api_key:
            st.error("❌ Không tìm thấy Monica API key. Vui lòng kiểm tra file .env")
        else:
            # Initialize Monica client
            client = OpenAI(
                base_url="https://openapi.monica.im/v1",
                api_key=monica_api_key,
            )
            
            # Prepare messages for API
            messages = [{"role": "system", "content": Tutor_prompt}]
            
            # Add PDF content if available
            if pdf_content:
                messages.append({
                    "role": "system",
                    "content": f"Nội dung tài liệu PDF người dùng cung cấp (ưu tiên sử dụng thông tin này nếu liên quan):\n{pdf_content[:4000]}\n(Hết trích đoạn, chỉ dùng để tham khảo trả lời nếu liên quan)"
                })
            
            # Add web search results if available
            if web_results and "Không tìm thấy" not in web_results and "Không thể lấy" not in web_results:
                messages.append({
                    "role": "system",
                    "content": f"Kết quả web search liên quan (chỉ dùng nếu tài liệu PDF không đủ thông tin):\n{web_results}"
                })
            
            # Add conversation history
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
            
            # Generate response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Set typing indicator
                st.session_state["typing"] = True
                
                try:
                    # Stream response
                    for response in client.chat.completions.create(
                        model="gpt-4.1-mini",
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
                    # Save session
                    for s in sessions:
                        if s["id"] == st.session_state["current_session_id"]:
                            s["messages"] = st.session_state["messages"]
                            s["updated_at"] = datetime.now().isoformat()
                            break
                    save_sessions(sessions)
                    
                except Exception as e:
                    st.session_state["typing"] = False
                    st.error(f"❌ Lỗi khi gọi API: {str(e)}")
                    st.info("💡 Hãy kiểm tra API key và kết nối internet")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🌐 <strong>TutorBot Web Enhanced</strong> - Powered by Monica AI & SerpAPI</p>
    <p>📚 Hỗ trợ PDF Upload | 🔍 Web Search | 💬 AI Chat | 💾 Session Management</p>
    <div style="margin-top: 1rem;">
        <span style="margin: 0 10px;">📧 Support: contact@tutorbot.com</span>
        <span style="margin: 0 10px;">🔗 GitHub: github.com/tutorbot</span>
        <span style="margin: 0 10px;">📖 Docs: docs.tutorbot.com</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-scroll to bottom (JavaScript)
st.markdown("""
<script>
    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }
    
    // Auto-scroll when new messages arrive
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                setTimeout(scrollToBottom, 100);
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Cleanup and optimization
if st.session_state.get("typing") and not st.session_state.get("searching"):
    time.sleep(0.1)  # Small delay to prevent excessive rerunning

# Performance monitoring (optional)
if st.checkbox("🔧 Debug Mode", value=False):
    st.markdown("### 🔍 Debug Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.json({
            "current_session_id": st.session_state.get("current_session_id"),
            "messages_count": len(st.session_state.get("messages", [])),
            "total_sessions": len(sessions),
            "typing": st.session_state.get("typing", False),
            "searching": st.session_state.get("searching", False)
        })
    
    with col2:
        st.json({
            "pdf_files_loaded": len(pdf_info) if pdf_info else 0,
            "pdf_content_length": len(pdf_content) if pdf_content else 0,
            "monica_api_configured": bool(monica_api_key),
            "serpapi_configured": bool(serpapi_key),
            "session_file_exists": os.path.exists(SESSION_FILE)
        })
    
    if st.button("🧹 Clear Session State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ Session state cleared!")
        st.rerun()

# Error handling wrapper
try:
    # Validate session integrity
    if st.session_state.get("current_session_id"):
        current_session = next((s for s in sessions if s["id"] == st.session_state["current_session_id"]), None)
        if not current_session:
            st.warning("⚠️ Phiên chat hiện tại không tồn tại. Đang tạo phiên mới...")
            st.session_state["current_session_id"] = None
            st.session_state["messages"] = []
            st.rerun()
    
    # Auto-save sessions periodically
    if len(st.session_state.get("messages", [])) > 0:
        current_time = datetime.now()
        last_save = st.session_state.get("last_auto_save")
        
        if not last_save or (current_time - datetime.fromisoformat(last_save)).seconds > 30:
            # Auto-save every 30 seconds
            for s in sessions:
                if s["id"] == st.session_state["current_session_id"]:
                    s["messages"] = st.session_state["messages"]
                    s["updated_at"] = current_time.isoformat()
                    break
            save_sessions(sessions)
        except Exception as e:
            st.error(f"An error occurred: {e}")
