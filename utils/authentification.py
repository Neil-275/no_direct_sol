import streamlit as st

def init_session_state():
    """Khởi tạo session state cho authentication"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""

def is_logged_in():
    """Kiểm tra xem người dùng đã đăng nhập chưa"""
    init_session_state()
    return st.session_state.logged_in

def get_current_user():
    """Lấy thông tin người dùng hiện tại"""
    init_session_state()
    if st.session_state.logged_in:
        return st.session_state.username
    return None

def require_login(page_title="Trang được bảo vệ"):
    """
    Decorator/function để yêu cầu đăng nhập trước khi truy cập trang
    Trả về True nếu đã đăng nhập, False nếu chưa
    """
    init_session_state()
    
    if not st.session_state.logged_in:
        # CSS cho trang yêu cầu đăng nhập
        st.markdown("""
        <style>
        .login-required {
            text-align: center;
            padding: 3rem 2rem;
            background-color: #F0F2F6;
            border-radius: 15px;
            margin: 2rem 0;
        }
        .login-icon {
            font-size: 4rem;
            color: #F63366;
            margin-bottom: 1rem;
        }
        .login-title {
            color: #262730;
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .login-message {
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Hiển thị thông báo yêu cầu đăng nhập
        st.markdown(f"""
        <div class="login-required">
            <div class="login-icon">🔒</div>
            <div class="login-title">Yêu cầu đăng nhập</div>
            <div class="login-message">Đăng nhập để tiếp tục</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Nút đăng nhập
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔑 Đăng nhập ngay", type="primary", use_container_width=True):
                st.switch_page("pages/Đăng_nhập.py")
        
        return False
    
    return True

def logout():
    """Đăng xuất người dùng"""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

def show_user_info():
    """Hiển thị thông tin người dùng đã đăng nhập"""
    if is_logged_in():
        with st.sidebar:
            st.success(f"👋 Xin chào, {st.session_state.username}!")
            if st.button("🚪 Đăng xuất", key="sidebar_logout"):
                logout()