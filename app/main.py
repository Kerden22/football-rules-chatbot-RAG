from __future__ import annotations  # Tip notlarını ertelemek için
import os
import json
import uuid
import base64
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pydantic import BaseModel
import uuid


# Pydantic modeller (models) burada tanımlandı
class QueryRequest(BaseModel):
    question: str

class RenameRequest(BaseModel):
    title: str

# Çevre değişkenlerini yükle
load_dotenv()

# FastAPI uygulamasını başlat
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------
# ChromaDB ve Google Gemini LLM Ayarları (main.py içinde yer alıyor)
# ------------------------------
from langchain_community.document_loaders import PyPDFLoader  
from langchain_text_splitters import RecursiveCharacterTextSplitter  
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

print("📖 PDF yükleniyor ve işleniyor...")
loader = PyPDFLoader("FutbolKuralları.pdf")  
data = loader.load()  
all_text = "\n".join([page.page_content for page in data])  
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)  
docs = text_splitter.split_text(all_text)

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = Chroma.from_texts(docs, embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.3,
    max_tokens=500
)

system_prompt = (
    "Sen bir yardımcı asistansın ve yalnızca futbol kuralları hakkında sorulara cevap veriyorsun. "
    "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
    "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
    "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

def get_rag_response(question: str) -> str:
    response = rag_chain.invoke({"input": question})
    return response["answer"]

# ------------------------------
# Chat History Fonksiyonları
# ------------------------------
SESSIONS_FILE = "chat_history.json"

def load_chat_history() -> dict:
    if not os.path.exists(SESSIONS_FILE):
        return {"sessions": []}
    with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"sessions": []}

def save_chat_history(data: dict):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_session(data: dict, session_id: str):
    for session in data.get("sessions", []):
        if session["id"] == session_id:
            return session
    return None

# ------------------------------
# app/endpoint.py dosyasındaki tüm Endpoint'leri uygulamaya dahil et
# ------------------------------
from app.endpoint import router as endpoints_router
app.include_router(endpoints_router)
