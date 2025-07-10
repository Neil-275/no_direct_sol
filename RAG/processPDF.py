from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from openai import OpenAI

pdf_data_path = "data"
vector_db_path = "vector/db_faiss"
embedding_model_file = "Model/all-MiniLM-L6-v2-f16.gguf"
monica_api_key = "sk-4d1b2c0f-3e6a-4b5c-bf8c-7d9e1f8a2b3c"
monica_base_url = "https://openapi.monica.im/v1"

def load_pdf_data():
    loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    textsplitter= RecursiveCharacterTextSplitter(chunk_size =512,chunk_overlap=50)
    chunks = textsplitter.split_documents(documents) 
    texts = [doc.page_content for doc in chunks]
    
    embedding=GPT4AllEmbeddings(model_file="Model/all-MiniLM-L6-v2-f16.gguf")
    db=FAISS.from_texts(texts, embedding)
    db.save_local(vector_db_path)
    return db
def read_vectordb():
    embedding=GPT4AllEmbeddings(model_file="Model/all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.load_local(vector_db_path, embedding,allow_dangerous_deserialization=True)
    return db

template='''<|im_start|>system
Bạn là một trợ lý AI thông minh
, bạn sẽ trả lời câu hỏi của người dùng dựa trên các tài liệu đã cho.
 Nếu câu hỏi không có trong tài liệu, hãy trả lời là 'Tôi không biết'.
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

def ask_with_monica(db, query, template):
    retriever = db.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    context = "\n".join([doc.page_content for doc in docs])

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

# load_pdf_data()
# db = read_vectordb()

# question = "dấu vân tay có đặc điểm gì"
# answer = ask_with_monica(db, question, template)

# print(answer)