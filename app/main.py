from __future__ import annotations  # Gelecekteki tip açıklamalarını etkinleştirir
import os  # Dosya/dizin işlemleri
import json  # JSON okuma/yazma
import uuid  # Benzersiz kimlik üretimi
import base64  # Base64 kodlama/çözme
import requests  # HTTP istekleri için
from dotenv import load_dotenv  # .env dosyasını yükleme
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles  # Statik dosya servisi
from fastapi.templating import Jinja2Templates  # Şablon motoru
from fastapi.responses import RedirectResponse  # Yönlendirme

load_dotenv()  # .env içindekileri yükle

# =====================================
# 2. FastAPI Uygulaması ve Statik İçerik
# =====================================
app = FastAPI()  # Uygulamayı başlat
app.mount("/static", StaticFiles(directory="static"), name="static")  # /static dizini
templates = Jinja2Templates(directory="templates")  # Şablonlar

# =====================================
# 3. Pydantic Modelleri
# =====================================
from pydantic import BaseModel

class QueryRequest(BaseModel):
    """
    question: Kullanıcının futbol kuralları hakkında sorduğu soru.
    """
    question: str  # Soru metni (zorunlu)

class RenameRequest(BaseModel):
    """
    title: Kaydedilen oturum veya belge başlığının yeni adı.
    """
    title: str  # Yeni başlık metni

# =====================================
# 4. Basit Yönlendirme Endpoint’leri
# =====================================

@app.get("/")
def root():
    """Ana sayfayı /login’e yönlendirir."""
    return RedirectResponse(url="/login")  # İlk açılışta login

@app.get("/login")
def login_page(request: Request):
    """Giriş formu sayfasını render eder."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    """Kayıt formu sayfasını render eder."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/index")
def index_page(request: Request):
    """
    index.html’i döndürür.
    Eğer 'user' çerezi yoksa veya çözme hatası alırsak /auth/login’e yönlendirir.
    """
    encoded_user = request.cookies.get("user")  # Çerez kontrolü
    if not encoded_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        username = base64.b64decode(encoded_user).decode("utf-8")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "username": username}
    )

# =====================================
# 5. PDF Yükleme ve RAG (Chroma + Gemini) Ayarları
# =====================================
print("📖 PDF yükleniyor ve işleniyor...")  

from langchain_community.document_loaders import PyPDFLoader  
from langchain_text_splitters import RecursiveCharacterTextSplitter  
from langchain_chroma import Chroma  
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI  
from langchain.chains import create_retrieval_chain  
from langchain_core.prompts import ChatPromptTemplate  
from langchain.chains.combine_documents import create_stuff_documents_chain  

# PDF’den metin yükle ve böl
loader = PyPDFLoader("FutbolKuralları.pdf")
data = loader.load()  
all_text = "\n".join(p.page_content for p in data)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_text(all_text)

# Embedding ve vektör veritabanı
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = Chroma.from_texts(docs, embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10}  
)

# LLM konfigürasyonu
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
    """
    RAG zincirini çalıştırır ve kullanıcı sorusuna bağlama dayalı cevap döner.
    """
    result = rag_chain.invoke({"input": question})
    return result["answer"]

# =====================================
# 6. Sohbet Geçmişi Yönetimi
# =====================================

def load_chat_history(request: Request) -> dict:
    """
    Kullanıcıya ait chat geçmişini JSON dosyasından yükler.
    """
    encoded = request.cookies.get("user")
    if not encoded:
        return {"sessions": []}

    try:
        username = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return {"sessions": []}

    user_file = f"data/chat_history_{username}.json"
    if not os.path.exists(user_file):
        return {"sessions": []}

    with open(user_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"sessions": []}

def save_chat_history(request: Request, data: dict):
    """
    Chat geçmişini JSON formatında diske yazar.
    """
    encoded = request.cookies.get("user")
    if not encoded:
        return

    try:
        username = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return

    os.makedirs("data", exist_ok=True)
    with open(f"data/chat_history_{username}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_session(data: dict, session_id: str):
    """
    session_id’ye göre oturum bilgisini döner.
    """
    for session in data.get("sessions", []):
        if session["id"] == session_id:
            return session
    return None

# =====================================
# 7. Uygulama Router’larının Dahil Edilmesi
# =====================================
from app.endpoint import router as endpoints_router  # Tüm endpoint tanımları
app.include_router(endpoints_router)

from app.auth import router as auth_router  # Kimlik doğrulama endpoint’leri
app.include_router(auth_router, prefix="/auth")
