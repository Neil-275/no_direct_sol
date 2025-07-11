import streamlit as st
import os
import json
import base64
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF for PDF handling
from PIL import Image
import io
import hashlib
import uuid
from RAG.processPDF import update_pdf_data, read_vectordb, ask_with_monica, template, init_faiss_db
from utils.authentification import require_login, show_user_info, get_current_user

# ===== KIỂM TRA ĐĂNG NHẬP =====
if not require_login("TutorBot - AI Tutor Assistant"):
    exit()

# Hiển thị thông tin người dùng trong sidebar
show_user_info()

# Cấu hình
UPLOAD_DIR = "archives/uploads"
SEARCH_RESULTS_DIR = "archives/search_results"
THUMBNAILS_DIR = "archives/thumbnails"

# Đảm bảo các thư mục tồn tại
for directory in [UPLOAD_DIR, SEARCH_RESULTS_DIR, THUMBNAILS_DIR]:
    os.makedirs(directory, exist_ok=True)

class ArchiveProtocol:
    """Giao thức cho việc giao tiếp giữa chatbot và hệ thống lưu trữ"""
    
    @staticmethod
    def save_search_result(query, results, metadata=None):
        """Lưu kết quả tìm kiếm web vào kho lưu trữ"""
        timestamp = datetime.now().isoformat()
        result_id = str(uuid.uuid4())
        
        search_data = {
            "id": result_id,
            "query": query,
            "results": results,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "type": "web_search"
        }
        
        # Lưu vào tệp JSON
        filename = f"search_{result_id}.json"
        filepath = os.path.join(SEARCH_RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2, ensure_ascii=False)
        
        # Tạo thumbnail cho kết quả tìm kiếm
        ArchiveProtocol.generate_search_thumbnail(result_id, query, results)
        
        return result_id
    
    @staticmethod
    def generate_search_thumbnail(result_id, query, results):
        """Tạo thumbnail cho kết quả tìm kiếm"""
        # Tạo một hình ảnh thumbnail đơn giản cho kết quả tìm kiếm
        img = Image.new('RGB', (200, 150), color='lightblue')
        # Trong một triển khai thực tế, bạn có thể muốn sử dụng ImageDraw của PIL
        # để thêm văn bản hoặc tạo một thumbnail phức tạp hơn
        
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f"search_{result_id}.png")
        img.save(thumbnail_path)
        
        return thumbnail_path

class ArchiveManager:
    """Lớp quản lý kho lưu trữ chính"""
    
    def __init__(self):
        self.protocol = ArchiveProtocol()
    
    def save_uploaded_file(self, uploaded_file):
        """Lưu tệp đã tải lên và tạo thumbnail"""
        if uploaded_file is not None:
            # Tạo tên tệp duy nhất
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file_hash}_{uploaded_file.name}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            # Lưu tệp
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Tạo thumbnail
            self.generate_pdf_thumbnail(filepath)
            
            # init_faiss_db()
            update_pdf_data([filename])

            return filepath
        return None
    
    def delete_file(self, item):
        """Xoá tệp và thumbnail liên quan"""
        try:
            if item.get("type") == "uploaded_file":
                # Xoá tệp gốc
                if os.path.exists(item["path"]):
                    os.remove(item["path"])
                
                # Xoá thumbnail
                thumbnail_path = self.get_thumbnail_path(item)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                
                # # Xoá dữ liệu trong cơ sở dữ liệu FAISS
                # faiss_path = '../vector/db_faiss'
                # for filename in os.listdir(faiss_path):
                #     file_path = os.path.join(faiss_path, filename)
                #     try:
                #         if os.path.isfile(file_path):
                #             os.remove(file_path)  # Xóa tệp
                #             print(f'Đã xóa tệp: {file_path}')
                #     except Exception as e:
                #         print(f'Lỗi khi xóa tệp {file_path}: {e}')
                
            elif item.get("type") == "web_search":
                # Xoá tệp JSON kết quả tìm kiếm
                search_file = os.path.join(SEARCH_RESULTS_DIR, f"search_{item['id']}.json")
                if os.path.exists(search_file):
                    os.remove(search_file)
                
                # Xoá thumbnail
                thumbnail_path = self.get_thumbnail_path(item)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                
                return True
                
        except Exception as e:
            st.error(f"Lỗi khi xoá tệp: {str(e)}")
            return False
        
        return False
    
    def generate_pdf_thumbnail(self, filepath):
        """Tạo thumbnail cho tệp PDF"""
        try:
            # Mở PDF và lấy trang đầu tiên
            doc = fitz.open(filepath)
            page = doc[0]
            
            # Render trang dưới dạng hình ảnh
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
            img_data = pix.tobytes("png")
            
            # Lưu thumbnail
            filename = Path(filepath).stem + ".png"
            thumbnail_path = os.path.join(THUMBNAILS_DIR, filename)
            
            with open(thumbnail_path, "wb") as f:
                f.write(img_data)
            
            doc.close()
            return thumbnail_path
            
        except Exception as e:
            st.error(f"Lỗi khi tạo thumbnail: {str(e)}")
            return None
    
    def get_uploaded_files(self):
        """Lấy danh sách các tệp đã tải lên với thông tin metadata"""
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                filepath = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "name": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "type": "uploaded_file"
                    })
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def get_search_results(self):
        """Lấy danh sách các kết quả tìm kiếm đã lưu"""
        results = []
        if os.path.exists(SEARCH_RESULTS_DIR):
            for filename in os.listdir(SEARCH_RESULTS_DIR):
                if filename.endswith('.json'):
                    filepath = os.path.join(SEARCH_RESULTS_DIR, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            results.append(data)
                    except Exception as e:
                        st.error(f"Lỗi khi đọc {filename}: {str(e)}")
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def get_thumbnail_path(self, item):
        """Lấy đường dẫn thumbnail cho một mục"""
        if item.get("type") == "uploaded_file":
            filename = Path(item["name"]).stem + ".png"
            return os.path.join(THUMBNAILS_DIR, filename)
        elif item.get("type") == "web_search":
            return os.path.join(THUMBNAILS_DIR, f"search_{item['id']}.png")
        return None

def display_pdf_viewer(filepath):
    """Hiển thị PDF trong Streamlit"""
    try:
        with open(filepath, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" height="600" type="application/pdf">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Lỗi khi hiển thị PDF: {str(e)}")

def display_search_result(result_data):
    """Hiển thị chi tiết kết quả tìm kiếm"""
    st.subheader(f"Câu hỏi tìm kiếm: {result_data['query']}")
    st.write(f"**Thời gian:** {result_data['timestamp']}")
    
    if result_data.get('metadata'):
        st.write("**Thông tin bổ sung:**")
        st.json(result_data['metadata'])
    
    st.write("**Kết quả:**")
    if isinstance(result_data['results'], list):
        for i, result in enumerate(result_data['results'], 1):
            st.write(f"{i}. {result}")
    else:
        st.write(result_data['results'])

def main():
    st.set_page_config(page_title="Kho Lưu Trữ", layout="wide")
    
    st.title("📁 Kho Lưu Trữ")
    st.markdown("---")
    
    # Khởi tạo quản lý kho lưu trữ
    archive_manager = ArchiveManager()
    
    # Tạo các tab
    tab1, tab2 = st.tabs(["📤 Tải Lên Tệp", "🗂️ Xem Kho Lưu Trữ"])
    
    with tab1:
        st.header("Tải Lên Tệp")
        
        uploaded_file = st.file_uploader(
            "Chọn tệp PDF",
            type=['pdf'],
            help="Tải lên các tệp PDF để thêm vào kho lưu trữ của bạn"
        )
        
        if uploaded_file is not None:
            if st.button("Lưu vào Kho Lưu Trữ"):
                with st.spinner("Đang lưu tệp, ghi vào cơ sở dữ liệu và tạo thumbnail..."):
                    saved_path = archive_manager.save_uploaded_file(uploaded_file)
                    if saved_path:
                        st.success(f"Tệp đã được lưu thành công!")
                        st.info(f"Đã lưu tại: {saved_path}")
                    else:
                        st.error("Lưu tệp không thành công")
    
    with tab2:
        st.header("Trình Duyệt Kho Lưu Trữ")
        
        # Lấy tất cả các mục
        uploaded_files = archive_manager.get_uploaded_files()
        search_results = archive_manager.get_search_results()
        
        # Kết hợp và sắp xếp tất cả các mục
        all_items = []
        all_items.extend(uploaded_files)
        all_items.extend(search_results)
        
        if not all_items:
            st.info("Chưa có mục nào trong kho lưu trữ. Tải lên một số tệp hoặc thực hiện tìm kiếm web để làm đầy kho lưu trữ.")
            return
        
        # Hiển thị các mục trong một lưới
        cols = st.columns(3)
        
        for i, item in enumerate(all_items):
            with cols[i % 3]:
                # Hiển thị thumbnail
                thumbnail_path = archive_manager.get_thumbnail_path(item)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    st.image(thumbnail_path, use_container_width=True)
                else:
                    st.info("Không có thumbnail khả dụng")
                
                # Hiển thị thông tin mục
                if item.get("type") == "uploaded_file":
                    st.write(f"**📄 {item['name']}**")
                    st.write(f"Kích thước: {item['size']} bytes")
                    st.write(f"Đã sửa đổi: {item['modified'].strftime('%Y-%m-%d %H:%M')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Xem", key=f"view_{i}"):
                            st.session_state[f"viewing_{i}"] = True
                    
                    with col2:
                        if st.button(f"Xoá", key=f"delete_{i}", type="secondary"):
                            st.session_state[f"show_delete_confirm_{i}"] = True
                
                elif item.get("type") == "web_search":
                    st.write(f"**🔍 Tìm kiếm: {item['query']}**")
                    st.write(f"Thời gian: {item['timestamp'][:16]}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Xem Kết Quả", key=f"search_{i}"):
                            st.session_state[f"viewing_search_{i}"] = True
                    
                    with col2:
                        if st.button(f"Xoá", key=f"delete_search_{i}", type="secondary"):
                            st.session_state[f"show_delete_confirm_{i}"] = True
                
                # Hiển thị dialog xác nhận xoá
                if st.session_state.get(f"show_delete_confirm_{i}"):
                    item_name = item.get('name', item.get('query', 'Không rõ tên'))
                    st.warning(f"Bạn có chắc chắn muốn xoá tệp **{item_name}**?")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button("Có", key=f"confirm_yes_{i}", type="primary"):
                            # Xác nhận xoá
                            if archive_manager.delete_file(item):
                                st.success(f"Đã xoá thành công!")
                                st.session_state[f"show_delete_confirm_{i}"] = False
                                st.rerun()
                            else:
                                st.error("Xoá tệp không thành công!")
                    
                    with col2:
                        if st.button("Không", key=f"confirm_no_{i}"):
                            # Huỷ xoá
                            st.session_state[f"show_delete_confirm_{i}"] = False
                            st.rerun()
                
                st.markdown("---")
        
        # Hiển thị trình xem dựa trên trạng thái phiên
        for i, item in enumerate(all_items):
            if item.get("type") == "uploaded_file" and st.session_state.get(f"viewing_{i}"):
                st.subheader(f"Đang xem: {item['name']}")
                if st.button(f"Đóng", key=f"close_{i}"):
                    st.session_state[f"viewing_{i}"] = False
                    st.rerun()
                
                display_pdf_viewer(item['path'])
            
            elif item.get("type") == "web_search" and st.session_state.get(f"viewing_search_{i}"):
                st.subheader("Chi tiết Kết Quả Tìm Kiếm")
                if st.button(f"Đóng Tìm Kiếm", key=f"close_search_{i}"):
                    st.session_state[f"viewing_search_{i}"] = False
                    st.rerun()
                
                display_search_result(item)

# API endpoints for chatbot integration
def chatbot_save_search_result(query, results, metadata=None):
    """
    Hàm được gọi bởi chatbot khi thực hiện tìm kiếm web
    
    Args:
        query (str): Câu hỏi tìm kiếm
        results (list or str): Kết quả tìm kiếm
        metadata (dict): Thông tin bổ sung
    
    Returns:
        str: ID kết quả để tham khảo
    """
    return ArchiveProtocol.save_search_result(query, results, metadata)

if __name__ == "__main__":
    main()
