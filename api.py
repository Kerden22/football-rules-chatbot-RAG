# çalıştırmak için : uvicorn api:app --reload    http://localhost:8000/

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
import json
import os
import uuid
from typing import Optional
from fastapi import HTTPException

#  Çevre değişkenlerini yükle
load_dotenv()

#  FastAPI uygulamasını başlat
app = FastAPI()

#  Static ve Template dosyalarını bağla
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#  Ana sayfa (HTML arayüzü)
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#  ChromaDB ve LLM modelini yükleme
if "vectorstore" not in globals():
    print("📖 PDF yükleniyor ve işleniyor...")
    
    #  Google Gemini Embedding modelini başlat
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    #  ChromaDB'yi başlat ve yükle
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

    #  Retriever oluştur 
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    #  Google Gemini LLM'yi başlat
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0.3,
        max_tokens=500
    )

    #  Sistem Prompt'u
    system_prompt = (
        "Sen bir yardımcı asistansın ve yalnızca futbol kuralları hakkında sorulara cevap veriyorsun. "
        "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
        "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
        "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
        "{context}"
    )

    #  Prompt Şablonu
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}")
        ]
    )

    #  Question-Answer zincirini oluştur
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    #  Retriever + LLM kombinasyonu ile RAG zincirini oluştur
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

#  Kullanıcıdan gelen sorguyu tanımlamak için bir model oluştur
class QueryRequest(BaseModel):
    question: str

#  Chatbot için bir API endpoint'i oluştur
@app.post("/ask")
def ask_question(request: QueryRequest):
    query = request.question
    print(f"📨 Soru alındı: {query}")

    # Yanıtı oluştur
    response = rag_chain.invoke({"input": query})
    answer = response["answer"]

    print(f"🤖 Yanıt: {answer}")
    return {"question": query, "answer": answer}

# -------------------------------------------------------------------
# AŞAĞIDAN İTİBAREN YENİ EKLENEN KODLAR
# -------------------------------------------------------------------

SESSIONS_FILE = "chat_history.json"

def load_chat_history():
    """
    chat_history.json dosyasını okuyup sözlük (dict) olarak döndürür.
    Eğer dosya yoksa veya dosya boş/geçersizse, 'sessions': [] içeren bir sözlük oluşturur.
    """
    if not os.path.exists(SESSIONS_FILE):
        return {"sessions": []}
    with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"sessions": []}

def save_chat_history(data: dict):
    """
    Verilen sözlüğü chat_history.json dosyasına yazar.
    """
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_session(data: dict, session_id: str) -> Optional[dict]:
    """
    Verilen data içindeki sessions listesinde session_id eşleşen oturumu döndürür.
    Bulunamazsa None döner.
    """
    for session in data["sessions"]:
        if session["id"] == session_id:
            return session
    return None

def get_rag_response(question: str) -> str:
    """
    RAG zincirinden (rag_chain) bir cevap alır ve sadece metin cevabı döndürür.
    """
    response = rag_chain.invoke({"input": question})
    return response["answer"]

@app.get("/sessions")
def list_sessions():
    """
    Kayıtlı tüm sohbet oturumlarını (id ve title) döndürür.
    """
    data = load_chat_history()
    # Her oturumun id ve title alanını dönüyoruz
    return [{"id": s["id"], "title": s["title"]} for s in data["sessions"]]

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """
    Belirli bir oturumun tüm mesajlarını döndürür.
    """
    data = load_chat_history()
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/sessions")
def create_session(request: QueryRequest):
    """
    Yeni bir sohbet oturumu oluşturur.
    request.question -> İlk kullanıcı mesajı
    Bot cevabı da eklenir. Sonuçta oluşan oturum geri döndürülür.
    """
    data = load_chat_history()

    # Yeni session oluştur
    session_id = str(uuid.uuid4())
    user_msg = request.question
    bot_msg = get_rag_response(user_msg)

    new_session = {
        "id": session_id,
        "title": user_msg,  # Oturumun başlığı ilk sorudan
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": bot_msg}
        ]
    }

    data["sessions"].append(new_session)
    save_chat_history(data)

    return new_session

@app.post("/sessions/{session_id}/messages")
def add_message(session_id: str, request: QueryRequest):
    """
    Mevcut oturuma yeni bir kullanıcı mesajı ekler,
    RAG zincirinden bot cevabını alır ve onu da ekler.
    """
    data = load_chat_history()
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = request.question
    bot_msg = get_rag_response(user_msg)

    # Mesajları ekle
    session["messages"].append({"role": "user", "content": user_msg})
    session["messages"].append({"role": "assistant", "content": bot_msg})

    # Dosyayı güncelle
    save_chat_history(data)

    # Bot cevabını döndürüyoruz
    return {"question": user_msg, "answer": bot_msg}

