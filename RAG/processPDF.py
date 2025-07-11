from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from openai import OpenAI

from langchain_core.documents import Document
import os
#from RAG.processPDF import update_pdf_data, read_vectordb, ask_with_monica, template, init_faiss_db


vector_db_path = "vector/db_faiss"
embedding_model_file = "Model/all-MiniLM-L6-v2-f16.gguf"
monica_api_key = "sk-4d1b2c0f-3e6a-4b5c-bf8c-7d9e1f8a2b3c"
monica_base_url = "https://openapi.monica.im/v1"

pdf_data_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_data_path+= "/archives/uploads"


# def update_pdf_data(pdf_files=None):
#     """
#     Nếu `pdf_files` là None, load toàn bộ thư mục.
#     Nếu `pdf_files` là danh sách tên file, chỉ load file đó.
#     """
#     if pdf_files is None:
#         loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls=PyPDFLoader)
#     else:
#         loader = DirectoryLoader(
#             pdf_data_path,
#             glob="*.pdf",
#             loader_cls=PyPDFLoader,
#             silent_errors=True,
#             show_progress=True
#         )
#         loader.file_paths = [f"{pdf_data_path}/{f}" for f in pdf_files]
    
#     documents = loader.load()
#     textsplitter= RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
#     chunks = textsplitter.split_documents(documents) 
#     texts = [doc.page_content for doc in chunks]
    
#     embedding = GPT4AllEmbeddings(model_file=embedding_model_file)
#     db = FAISS.load_local(vector_db_path, embedding, allow_dangerous_deserialization=True)

#     db.add_texts(texts)  # thêm dữ liệu mới

#     db.save_local(vector_db_path)
#     return db
def update_pdf_data(pdf_files=None, similarity_threshold=0.95):
    """
    Nếu `pdf_files` là None, load toàn bộ thư mục.
    Nếu `pdf_files` là danh sách tên file, chỉ load file đó.
    Kiểm tra trùng văn bản trước khi add.
    """
    if pdf_files is None:
        loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls=PyPDFLoader)
    else:
        loader = DirectoryLoader(
            pdf_data_path,
            glob="*.pdf",
            loader_cls=PyPDFLoader,
            silent_errors=True,
            show_progress=True
        )
        loader.file_paths = [f"{pdf_data_path}/{f}" for f in pdf_files]
    
    documents = loader.load()
    textsplitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = textsplitter.split_documents(documents) 
    texts = [doc.page_content for doc in chunks]

    embedding = GPT4AllEmbeddings(model_file=embedding_model_file)
    db = FAISS.load_local(vector_db_path, embedding, allow_dangerous_deserialization=True)

    # lọc texts chưa có
    unique_texts = []
    for text in texts:
        query_emb = embedding.embed_query(text)
        results = db.similarity_search_by_vector(query_emb, k=1)
        if results:
            score = results[0].score if hasattr(results[0], 'score') else None
            if score and score >= similarity_threshold:
                continue  # trùng, bỏ qua
        unique_texts.append(text)

    if unique_texts:
        db.add_texts(unique_texts)
        db.save_local(vector_db_path)
    
    return db


def init_faiss_db():
   
    index_file = os.path.join(vector_db_path, "index.faiss")

    if os.path.exists(index_file):
        print(f"FAISS DB already exists at {vector_db_path}")
        return

    print(f"FAISS DB not found. Initializing empty FAISS DB at {vector_db_path}")
    embedding = GPT4AllEmbeddings(model_file=embedding_model_file)

    dummy_doc = Document(page_content="dummy", metadata={"file_name": "dummy.txt"})
    db = FAISS.from_documents([dummy_doc], embedding)
    db.save_local(vector_db_path)
    print("Empty FAISS DB initialized.")








def load_pdf_data():
    loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    for doc in documents:
        doc.metadata['file_name'] = doc.metadata.get('source', '').split('/')[-1]

    textsplitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = textsplitter.split_documents(documents)

    for chunk in chunks:
        if 'file_name' not in chunk.metadata:
            chunk.metadata['file_name'] = chunk.metadata.get('source', '').split('/')[-1]

    embedding = GPT4AllEmbeddings(model_file="Model/all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.from_documents(chunks, embedding)
    db.save_local(vector_db_path)
    return db


def read_vectordb():
    embedding=GPT4AllEmbeddings(model_file="Model/all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.load_local(vector_db_path, embedding,allow_dangerous_deserialization=True)
    return db

template='''<|im_start|>system
Bạn là một trợ lý AI thông minh
, bạn sẽ trả lời câu hỏi của người dùng dựa hoàn toàn trên các tài liệu đã cho.
{context}
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant 
'''

from openai import OpenAI

client = OpenAI(
  base_url="https://openapi.monica.im/v1",
  api_key="sk-JRxR1PYhvYc62aVx6TOuKZV-C6SNGTWQf0re8j0lL583jo1SiZguflgSxdAsGCu8po0PS2pvPd-nAu3AZZZkYXojBjPx",
)

def ask_with_monica(db, query, template, file_filter=None):
    """
    file_filter: tên file PDF (hoặc None nếu không lọc)
    """
    retriever = db.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(query)
   # print(docs)
    # lọc theo file nếu có
    if file_filter:
        docs = [doc for doc in docs if file_filter in doc.metadata.get("source", "")]

    context = "\n".join([doc.page_content for doc in docs])
    print(f"Context: {context}")
    final_prompt = template.format(context=context, question=query)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": final_prompt
            }
        ]
    )
    return completion.choices[0].message.content
