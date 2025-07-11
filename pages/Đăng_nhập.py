import streamlit as st
import json
import hashlib
import os
from datetime import datetime
import re
import time

# Cấu hình trang
st.set_page_config(
    page_title="Đăng nhập & Đăng ký",
    page_icon="🔐",
    layout="centered"
)

# File lưu trữ database
DATABASE_FILE = "users_database.json"

def load_users():
    """Tải dữ liệu người dùng từ file JSON"""
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_data):
    """Lưu dữ liệu người dùng vào file JSON"""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """Mã hóa mật khẩu bằng SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password(password):
    """Kiểm tra độ mạnh của mật khẩu"""
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    if not re.search(r'[A-Za-z]', password):
        return False, "Mật khẩu phải chứa ít nhất 1 chữ cái"
    if not re.search(r'\d', password):
        return False, "Mật khẩu phải chứa ít nhất 1 số"
    return True, "Mật khẩu hợp lệ"

def register_user(username, password):
    """Đăng ký người dùng mới"""
    users = load_users()
    
    # Kiểm tra username đã tồn tại
    if username in users:
        return False, "Tên đăng nhập đã tồn tại"
    
    # Thêm người dùng mới
    users[username] = {
        'password': hash_password(password),
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    
    save_users(users)
    return True, "Đăng ký thành công!"

def login_user(username, password):
    """Đăng nhập người dùng"""
    users = load_users()
    
    if username not in users:
        return False, "Tên đăng nhập không tồn tại"
    
    if users[username]['password'] != hash_password(password):
        return False, "Mật khẩu không chính xác"
    
    # Cập nhật thời gian đăng nhập cuối
    users[username]['last_login'] = datetime.now().isoformat()
    save_users(users)
    
    return True, "Đăng nhập thành công!"

def init_session_state():
    """Khởi tạo session state cho authentication"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""

def main():
    # CSS tùy chỉnh
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #F63366;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .form-container {
        background-color: #F0F2F6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .redirect-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 10px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">🔐 Hệ thống Đăng nhập</h1>', unsafe_allow_html=True)

    # Khởi tạo session state
    init_session_state()

    # Nếu đã đăng nhập
    if st.session_state.logged_in:
        users = load_users()
        user_data = users.get(st.session_state.username, {})
        
        # Hiển thị thông báo chuyển hướng
        st.markdown(f"""
        <div class="redirect-message">
            <h2>🎉 Chào mừng, {st.session_state.username}!</h2>
            <p style="font-size: 1.2rem; margin: 1rem 0;">Đăng nhập thành công!</p>
            <div style="margin: 2rem 0;">
                <div class="loading-spinner"></div>
                <span>Đang chuyển hướng đến trang chủ...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Thông tin người dùng
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Tên đăng nhập:** {st.session_state.username}")
        with col2:
            st.info(f"**Ngày tạo:** {user_data.get('created_at', 'N/A')[:10]}")
            last_login = user_data.get('last_login')
            if last_login:
                st.info(f"**Đăng nhập cuối:** {last_login[:16]}")
        
        # Các nút hành động
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🏠 Đi đến Trang chủ", type="primary", use_container_width=True):
                st.switch_page("Trang_chủ.py")
        
        with col2:
            if st.button("💬 Chat ngay", use_container_width=True):
                st.switch_page("pages/Bot_dạy_học.py")
        
        with col3:
            if st.button("🚪 Đăng xuất", type="secondary", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        
        # Auto redirect sau 3 giây
        time.sleep(0.1)  # Ngắn để không block UI
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.href = '/';
        }, 3000);
        </script>
        """, unsafe_allow_html=True)
        
        return

    # Tab đăng nhập và đăng ký
    tab1, tab2 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])

    with tab1:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("Đăng nhập vào tài khoản")
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập của bạn")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            
            login_button = st.form_submit_button("🔑 Đăng nhập", type="primary")
            
            if login_button:
                if not username or not password:
                    st.error("Vui lòng điền đầy đủ thông tin!")
                else:
                    with st.spinner("Đang xác thực..."):
                        success, message = login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success(message)
                            time.sleep(1)  # Hiển thị thông báo thành công
                            st.rerun()
                        else:
                            st.error(message)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("Tạo tài khoản mới")
        
        with st.form("register_form"):
            username = st.text_input("Tên đăng nhập", placeholder="Chọn tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password", placeholder="Tạo mật khẩu mạnh")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")
            
            register_button = st.form_submit_button("📝 Đăng ký", type="primary")
            
            if register_button:
                # Kiểm tra các trường bắt buộc
                if not all([username, password, confirm_password]):
                    st.error("Vui lòng điền đầy đủ tất cả thông tin!")
                elif password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp!")
                else:
                    # Kiểm tra độ mạnh mật khẩu
                    is_valid, password_message = validate_password(password)
                    if not is_valid:
                        st.error(password_message)
                    else:
                        with st.spinner("Đang tạo tài khoản..."):
                            success, message = register_user(username, password)
                            if success:
                                st.success(message)
                                st.balloons()
                                st.info("💡 Bây giờ bạn có thể đăng nhập bằng tài khoản vừa tạo!")
                            else:
                                st.error(message)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Thông tin hướng dẫn
    with st.expander("ℹ️ Hướng dẫn sử dụng"):
        st.markdown("""
        **Đăng ký tài khoản:**
        - Chọn tên đăng nhập duy nhất
        - Mật khẩu phải có ít nhất 6 ký tự, bao gồm chữ và số
        - Xác nhận mật khẩu phải khớp với mật khẩu đã nhập
        
        **Đăng nhập:**
        - Sử dụng tên đăng nhập và mật khẩu đã đăng ký
        - Hệ thống sẽ tự động chuyển hướng đến trang chủ sau khi đăng nhập thành công
        
        **Bảo mật:**
        - Mật khẩu được mã hóa SHA256
        - Dữ liệu lưu trữ trong file JSON cục bộ
        - Phiên đăng nhập được duy trì trong suốt session
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem 0;">
        <p>🎓 <strong>Bot_dạy_học</strong> - Trợ lý AI thông minh cho việc học tập</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    from RAG.processPDF import init_faiss_db
    init_faiss_db()  # Khởi tạo cơ sở dữ liệu FAISS nếu cần thiết
