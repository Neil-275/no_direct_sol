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

# Hiển thị thông tin user trong sidebar
show_user_info()

# Configuration
UPLOAD_DIR = "archives/uploads"
SEARCH_RESULTS_DIR = "archives/search_results"
THUMBNAILS_DIR = "archives/thumbnails"

# Ensure directories exist
for directory in [UPLOAD_DIR, SEARCH_RESULTS_DIR, THUMBNAILS_DIR]:
    os.makedirs(directory, exist_ok=True)

class ArchiveProtocol:
    """Protocol for communication between chatbot and archive system"""
    
    @staticmethod
    def save_search_result(query, results, metadata=None):
        """Save web search results to archive"""
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
        
        # Save to JSON file
        filename = f"search_{result_id}.json"
        filepath = os.path.join(SEARCH_RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2, ensure_ascii=False)
        
        # Generate thumbnail for search result
        ArchiveProtocol.generate_search_thumbnail(result_id, query, results)
        
        return result_id
    
    @staticmethod
    def generate_search_thumbnail(result_id, query, results):
        """Generate a thumbnail for search results"""
        # Create a simple thumbnail image for search results
        img = Image.new('RGB', (200, 150), color='lightblue')
        # In a real implementation, you might want to use PIL's ImageDraw
        # to add text or create a more sophisticated thumbnail
        
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f"search_{result_id}.png")
        img.save(thumbnail_path)
        
        return thumbnail_path

class ArchiveManager:
    """Main archive management class"""
    
    def __init__(self):
        self.protocol = ArchiveProtocol()
    
    def save_uploaded_file(self, uploaded_file):
        """Save uploaded file and generate thumbnail"""
        if uploaded_file is not None:
            # Generate unique filename
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file_hash}_{uploaded_file.name}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            # Save file
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Generate thumbnail
            self.generate_pdf_thumbnail(filepath)
            
            init_faiss_db()
            update_pdf_data([filename])

            return filepath
        return None
    
    def generate_pdf_thumbnail(self, filepath):
        """Generate thumbnail for PDF file"""
        try:
            # Open PDF and get first page
            doc = fitz.open(filepath)
            page = doc[0]
            
            # Render page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
            img_data = pix.tobytes("png")
            
            # Save thumbnail
            filename = Path(filepath).stem + ".png"
            thumbnail_path = os.path.join(THUMBNAILS_DIR, filename)
            
            with open(thumbnail_path, "wb") as f:
                f.write(img_data)
            
            doc.close()
            return thumbnail_path
            
        except Exception as e:
            st.error(f"Error generating thumbnail: {str(e)}")
            return None
    
    def get_uploaded_files(self):
        """Get list of uploaded files with metadata"""
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
        """Get list of saved search results"""
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
                        st.error(f"Error reading {filename}: {str(e)}")
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def get_thumbnail_path(self, item):
        """Get thumbnail path for an item"""
        if item.get("type") == "uploaded_file":
            filename = Path(item["name"]).stem + ".png"
            return os.path.join(THUMBNAILS_DIR, filename)
        elif item.get("type") == "web_search":
            return os.path.join(THUMBNAILS_DIR, f"search_{item['id']}.png")
        return None

def display_pdf_viewer(filepath):
    """Display PDF in Streamlit"""
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
        st.error(f"Error displaying PDF: {str(e)}")

def display_search_result(result_data):
    """Display search result details"""
    st.subheader(f"Search Query: {result_data['query']}")
    st.write(f"**Timestamp:** {result_data['timestamp']}")
    
    if result_data.get('metadata'):
        st.write("**Metadata:**")
        st.json(result_data['metadata'])
    
    st.write("**Results:**")
    if isinstance(result_data['results'], list):
        for i, result in enumerate(result_data['results'], 1):
            st.write(f"{i}. {result}")
    else:
        st.write(result_data['results'])

def main():
    st.set_page_config(page_title="Archives", layout="wide")
    
    st.title("📁 Archives")
    st.markdown("---")
    
    # Initialize archive manager
    archive_manager = ArchiveManager()
    
    # Create tabs
    tab1, tab2 = st.tabs(["📤 Upload Files", "🗂️ View Archives"])
    
    with tab1:
        st.header("File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload PDF files to add them to your archive"
        )
        
        if uploaded_file is not None:
            if st.button("Save to Archive"):
                with st.spinner("Saving file, write to database and generating thumbnail..."):
                    saved_path = archive_manager.save_uploaded_file(uploaded_file)
                    if saved_path:
                        st.success(f"File saved successfully!")
                        st.info(f"Saved to: {saved_path}")
                    else:
                        st.error("Failed to save file")
    
    with tab2:
        st.header("Archive Browser")
        
        # Get all items
        uploaded_files = archive_manager.get_uploaded_files()
        search_results = archive_manager.get_search_results()
        
        # Combine and sort all items
        all_items = []
        all_items.extend(uploaded_files)
        all_items.extend(search_results)
        
        if not all_items:
            st.info("No items in archive yet. Upload some files or run web searches to populate the archive.")
            return
        
        # Display items in a grid
        cols = st.columns(3)
        
        for i, item in enumerate(all_items):
            with cols[i % 3]:
                # Display thumbnail
                thumbnail_path = archive_manager.get_thumbnail_path(item)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    st.image(thumbnail_path, use_container_width=True)
                else:
                    st.info("No thumbnail available")
                
                # Display item info
                if item.get("type") == "uploaded_file":
                    st.write(f"**📄 {item['name']}**")
                    st.write(f"Size: {item['size']} bytes")
                    st.write(f"Modified: {item['modified'].strftime('%Y-%m-%d %H:%M')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"View", key=f"view_{i}"):
                            st.session_state[f"viewing_{i}"] = True
                    
                    with col2:
                        if st.button(f"Apply RAG", key=f"util_{i}"):
                            st.info("Utilities feature will be implemented later")
                
                elif item.get("type") == "web_search":
                    st.write(f"**🔍 Search: {item['query']}**")
                    st.write(f"Timestamp: {item['timestamp'][:16]}")
                    
                    if st.button(f"View Results", key=f"search_{i}"):
                        st.session_state[f"viewing_search_{i}"] = True
                
                st.markdown("---")
        
        # Display viewers based on session state
        for i, item in enumerate(all_items):
            if item.get("type") == "uploaded_file" and st.session_state.get(f"viewing_{i}"):
                st.subheader(f"Viewing: {item['name']}")
                if st.button(f"Close", key=f"close_{i}"):
                    st.session_state[f"viewing_{i}"] = False
                    st.rerun()
                
                display_pdf_viewer(item['path'])
            
            elif item.get("type") == "web_search" and st.session_state.get(f"viewing_search_{i}"):
                st.subheader("Search Result Details")
                if st.button(f"Close Search", key=f"close_search_{i}"):
                    st.session_state[f"viewing_search_{i}"] = False
                    st.rerun()
                
                display_search_result(item)

# API endpoints for chatbot integration
def chatbot_save_search_result(query, results, metadata=None):
    """
    Function to be called by chatbot when web search is performed
    
    Args:
        query (str): The search query
        results (list or str): Search results
        metadata (dict): Additional metadata
    
    Returns:
        str: Result ID for reference
    """
    return ArchiveProtocol.save_search_result(query, results, metadata)

if __name__ == "__main__":
    main()
