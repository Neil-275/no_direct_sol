import streamlit as st
import time
from datetime import datetime
from utils.authentification import require_login, show_user_info, get_current_user
import json
import os

# Cấu hình trang
st.set_page_config(
    page_title="Bot_dạy_học - Trang Chủ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh cho trang chủ
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Reset và base styles */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 4rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 3rem;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='7' cy='7' r='7'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    animation: float 20s ease-in-out infinite;
    z-index: 1;
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 1.3rem;
    margin-bottom: 2rem;
    opacity: 0.9;
    font-weight: 300;
}

.hero-stats {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-top: 2rem;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    display: block;
}

.stat-label {
    font-size: 0.9rem;
    opacity: 0.8;
}

/* Feature Cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 3rem 0;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border: 1px solid #f0f0f0;
    position: relative;
    overflow: hidden;
}

.feature-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}

.feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
}

.feature-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #333;
}

.feature-description {
    color: #666;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

.feature-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.8rem 1.5rem;
    border: none;
    border-radius: 8px;
    text-decoration: none;
    display: inline-block;
    font-weight: 500;
    transition: all 0.3s ease;
}

.feature-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    color: white;
    text-decoration: none;
}

/* Quick Stats */
.quick-stats {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin: 3rem 0;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    text-align: center;
}

.quick-stat-item {
    padding: 1rem;
}

.quick-stat-number {
    font-size: 2rem;
    font-weight: 700;
    display: block;
    margin-bottom: 0.5rem;
}

.quick-stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
}

/* Welcome Message */
.welcome-message {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
}

.welcome-title {
    font-size: 2rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 1rem;
}

.welcome-text {
    color: #666;
    font-size: 1.1rem;
    line-height: 1.6;
}

/* Recent Activity */
.activity-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.activity-card:hover {
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.activity-time {
    color: #888;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.activity-title {
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
}

.activity-description {
    color: #666;
    font-size: 0.95rem;
}

/* Animations */
@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.pulse {
    animation: pulse 2s ease-in-out infinite;
}

/* Responsive */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.5rem;
    }
    
    .hero-stats {
        flex-direction: column;
        gap: 1rem;
    }
    
    .feature-grid {
        grid-template-columns: 1fr;
    }
}

/* Loading Animation */
.loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

def load_user_stats():
    """Load user statistics"""
    try:
        # Thống kê từ chat sessions
        if os.path.exists("chat_sessions.json"):
            with open("chat_sessions.json", "r", encoding="utf-8") as f:
                sessions = json.load(f)
                total_sessions = len(sessions)
                total_messages = sum(len(s.get("messages", [])) for s in sessions)
        else:
            total_sessions = 0
            total_messages = 0
        
        # Thống kê từ uploaded files
        upload_dir = "archives/uploads"
        total_files = len(os.listdir(upload_dir)) if os.path.exists(upload_dir) else 0
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_files": total_files,
            "study_hours": total_sessions * 0.5  # Ước tính
        }
    except:
        return {
            "total_sessions": 0,
            "total_messages": 0,
            "total_files": 0,
            "study_hours": 0
        }

def get_recent_activities():
    """Get recent user activities"""
    activities = []
    try:
        if os.path.exists("chat_sessions.json"):
            with open("chat_sessions.json", "r", encoding="utf-8") as f:
                sessions = json.load(f)
                # Lấy 5 session gần nhất
                recent_sessions = sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)[:5]
                
                for session in recent_sessions:
                    if session.get("messages"):
                        activities.append({
                            "time": session.get("updated_at", ""),
                            "title": "Phiên chat mới",
                            "description": session.get("name", "Trò chuyện với Bot_dạy_học")[:50] + "..."
                        })
    except:
        pass
    
    return activities

# ===== KIỂM TRA ĐĂNG NHẬP =====
if not require_login("Bot_dạy_học - Trang Chủ"):
    # Hiển thị banner cho người chưa đăng nhập
    st.markdown("""
    <div class="hero-section">
        <div class="hero-content">
            <h1 class="hero-title">🎓 Bot_dạy_học</h1>
            <p class="hero-subtitle">Trợ lý AI thông minh cho việc học tập</p>
            <p style="font-size: 1.1rem; margin-bottom: 2rem;">
                Khám phá sức mạnh của AI trong giáo dục. Học tập thông minh, hiệu quả và cá nhân hóa.
            </p>
            <div class="hero-stats">
                <div class="stat-item">
                    <span class="stat-number">1000+</span>
                    <span class="stat-label">Học sinh</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">50+</span>
                    <span class="stat-label">Môn học</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">24/7</span>
                    <span class="stat-label">Hỗ trợ</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Thông báo yêu cầu đăng nhập
    st.info("🔐 Vui lòng đăng nhập để sử dụng đầy đủ tính năng của Bot_dạy_học!")
    exit()

# Hiển thị thông tin người dùng trong sidebar
show_user_info()

# ===== TRANG CHỦ CHO NGƯỜI ĐÃ ĐĂNG NHẬP =====
current_user = get_current_user()
user_stats = load_user_stats()
recent_activities = get_recent_activities()

# Welcome Message
st.markdown(f"""
<div class="welcome-message">
    <h2 class="welcome-title">Chào mừng trở lại, {current_user}! 👋</h2>
    <p class="welcome-text">
        Sẵn sàng để tiếp tục hành trình học tập của bạn? Bot_dạy_học luôn ở đây để hỗ trợ bạn đạt được mục tiêu học tập.
    </p>
</div>
""", unsafe_allow_html=True)

# Quick Stats
st.markdown("""
<div class="quick-stats">
    <h3 style="text-align: center; margin-bottom: 2rem; font-size: 1.8rem;">📊 Thống kê học tập của bạn</h3>
    <div class="stats-grid">
        <div class="quick-stat-item">
            <span class="quick-stat-number">{}</span>
            <span class="quick-stat-label">Phiên chat</span>
        </div>
        <div class="quick-stat-item">
            <span class="quick-stat-number">{}</span>
            <span class="quick-stat-label">Tin nhắn</span>
        </div>
        <div class="quick-stat-item">
            <span class="quick-stat-number">{}</span>
            <span class="quick-stat-label">Tài liệu</span>
        </div>
        <div class="quick-stat-item">
            <span class="quick-stat-number">{:.1f}h</span>
            <span class="quick-stat-label">Thời gian học</span>
        </div>
    </div>
</div>
""".format(
    user_stats["total_sessions"],
    user_stats["total_messages"], 
    user_stats["total_files"],
    user_stats["study_hours"]
), unsafe_allow_html=True)

# Feature Cards
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <span class="feature-icon">💬</span>
        <h3 class="feature-title">Chat với Bot_dạy_học</h3>
        <p class="feature-description">
            Trò chuyện trực tiếp với AI tutor thông minh. Đặt câu hỏi, giải bài tập và nhận được hướng dẫn chi tiết.
        </p>
        <a href="/Bot_dạy_học" class="feature-button">Bắt đầu chat</a>
    </div>
    <div class="feature-card">
        <span class="feature-icon">📚</span>
        <h3 class="feature-title">Kho Tài Liệu</h3>
        <p class="feature-description">
            Upload và quản lý tài liệu học tập. Sử dụng RAG để tìm kiếm thông tin nhanh chóng và chính xác.
        </p>
        <a href="/Lưu_trữ" class="feature-button">Xem kho lưu trữ</a>
    </div>
    <div class="feature-card">
        <span class="feature-icon">🧠</span>
        <h3 class="feature-title">AI Thông Minh</h3>
        <p class="feature-description">
            Công nghệ AI tiên tiến giúp cá nhân hóa trải nghiệm học tập và đưa ra lời khuyên phù hợp.
        </p>
        <a href="#" class="feature-button">Tìm hiểu thêm</a>
    </div>
</div>
""", unsafe_allow_html=True)

# Recent Activities
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Hoạt động gần đây")
    
    if recent_activities:
        for activity in recent_activities:
            try:
                # Format time
                time_str = activity["time"][:16] if activity["time"] else "Không rõ"
                
                st.markdown(f"""
                <div class="activity-card">
                    <div class="activity-time">{time_str}</div>
                    <div class="activity-title">{activity["title"]}</div>
                    <div class="activity-description">{activity["description"]}</div>
                </div>
                """, unsafe_allow_html=True)
            except:
                continue
    else:
        st.info("Chưa có hoạt động nào. Hãy bắt đầu chat với Bot_dạy_học!")

with col2:
    st.markdown("### 🎯 Mục tiêu hôm nay")
    
    # Progress bars
    st.markdown("**Tiến độ học tập**")
    progress_value = min(user_stats["total_messages"] / 10, 1.0) if user_stats["total_messages"] > 0 else 0
    st.progress(progress_value)
    st.caption(f"Đã hoàn thành {int(progress_value * 100)}% mục tiêu tin nhắn")
    
    st.markdown("**Tài liệu đã xem**")
    file_progress = min(user_stats["total_files"] / 5, 1.0) if user_stats["total_files"] > 0 else 0
    st.progress(file_progress)
    st.caption(f"Đã xem {user_stats['total_files']} tài liệu")
    
    # Quick Actions
    st.markdown("### ⚡ Thao tác nhanh")
    
    if st.button("🆕 Chat mới", type="primary", use_container_width=True):
        st.switch_page("pages/Bot_dạy_học.py")
    
    if st.button("📤 Upload tài liệu", use_container_width=True):
        st.switch_page("pages/Lưu_trữ.py")
    
    if st.button("📊 Xem thống kê", use_container_width=True):
        st.info("Tính năng đang phát triển!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>🎓 <strong>Bot_dạy_học</strong> - Trợ lý AI thông minh cho việc học tập</p>
    <p>Phiên bản 1.0 | © 2024 Bot_dạy_học Team</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh stats every 30 seconds
if st.button("🔄 Làm mới", help="Cập nhật thống kê mới nhất"):
    st.rerun()

# JavaScript for dynamic effects
st.markdown("""
<script>
// Add some dynamic effects
document.addEventListener('DOMContentLoaded', function() {
    // Animate feature cards on scroll
    const cards = document.querySelectorAll('.feature-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease';
        observer.observe(card);
    });
});
</script>
""", unsafe_allow_html=True)