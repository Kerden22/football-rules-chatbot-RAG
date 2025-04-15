# çalıştırmak için : uvicorn api:app --reload    http://localhost:8000/

from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader  
from langchain_text_splitters import RecursiveCharacterTextSplitter  
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

import base64
import requests

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

    # PDF'yi yükle ve metin haline getir
    loader = PyPDFLoader("FutbolKuralları.pdf")  
    data = loader.load()  
    all_text = "\n".join([page.page_content for page in data])  

    # Metni chunk'lara böl
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)  
    docs = text_splitter.split_text(all_text)  
    
    #  Google Gemini Embedding modelini başlat
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Chunk'ları (docs) kullanarak ilk kez ChromaDB oluştur
    vectorstore = Chroma.from_texts(docs, embeddings, persist_directory="./chroma_db")

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

#  Hugging Face API anahtarı ve modelleri için ayarlar
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HF_MODEL_ID = "runwayml/stable-diffusion-v1-5"  # Görsel üretimi için model
MUSICGEN_MODEL_ID = "facebook/musicgen-small"  # Müzik üretimi için model

######################################
# Stability AI API ile Görsel Üretimi
######################################
def generate_image(prompt: str) -> str:
    """
    Stability AI API kullanarak, önce verilen promptu Türkçeden İngilizceye çevirir,
    ardından Stable Diffusion ile görsel üretir ve gelen JSON cevabından
    base64 kodlanmış görseli döndürür.
    """
    # Türkçe promptu İngilizceye çevirmek için yardımcı fonksiyon
    def translate_to_english(text: str) -> str:
        try:
            translation_response = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": "tr|en"}
            )
            if translation_response.status_code == 200:
                data = translation_response.json()
                translated_text = data.get("responseData", {}).get("translatedText", text)
                return translated_text
            else:
                return text
        except Exception as ex:
            print("Translation error:", ex)
            return text

    # Girilen promptu İngilizceye çeviriyoruz
    english_prompt = translate_to_english(prompt)

    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
    if not STABILITY_API_KEY:
        raise Exception("STABILITY_API_KEY is not set in .env")
    try:
        response = requests.post(
            url="https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "text_prompts": [{"text": english_prompt}],
                "cfg_scale": 7,
                "height": 512,
                "width": 512,
                "samples": 1,
                "steps": 30,
            },
        )
        if response.status_code != 200:
            print("Stability API error:", response.text)
            raise Exception("Stability API image generation failed")
        image_base64 = response.json()["artifacts"][0]["base64"]
        return image_base64
    except Exception as e:
        print("Error in generate_image:", e)
        raise Exception(f"Stability API image generation error: {e}")

######################################
# Hugging Face MusicGen ile Müzik Üretimi
######################################
def generate_music(prompt: str) -> str:
    if not HUGGINGFACE_API_KEY:
        raise Exception("HUGGINGFACE_API_KEY is not set in .env")
    api_url = f"https://api-inference.huggingface.co/models/{MUSICGEN_MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        error_message = f"HuggingFace MusicGen API error: {response.text}"
        print("Müzik üretimi sırasında hata oluştu:")
        print(error_message)
        raise Exception(error_message)
    audio_bytes = response.content
    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    return b64_audio

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
# Chat_History json için kodlar
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
    user_msg = request.question.strip()

    if user_msg.lower().startswith("müzik üret:"):
        prompt = user_msg[len("müzik üret:"):].strip()
        try:
            b64_audio = generate_music(prompt)
            new_session = {
                "id": session_id,
                "title": user_msg[:40],
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant_audio", "content": b64_audio}
                ]
            }
        except Exception as e:
            new_session = {
                "id": session_id,
                "title": "Müzik Üretim Hatası",
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": "Müzik üretimi sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin."}
                ]
            }
    elif user_msg.lower().startswith("resim üret:"):
        prompt = user_msg[len("resim üret:"):].strip()
        try:
            b64_image = generate_image(prompt)
            new_session = {
                "id": session_id,
                "title": user_msg[:40],
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant_image", "content": b64_image}
                ]
            }
        except Exception as e:
            new_session = {
                "id": session_id,
                "title": "Görsel Üretim Hatası",
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": "Görsel üretimi sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin."}
                ]
            }
    else:
        new_session = {
            "id": session_id,
            "title": user_msg,
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": get_rag_response(user_msg)}
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

    user_msg = request.question.strip()

    if user_msg.lower().startswith("müzik üret:"):
        prompt = user_msg[len("müzik üret:"):].strip()
        try:
            b64_audio = generate_music(prompt)
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant_audio", "content": b64_audio})
        except Exception as e:
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": "Müzik üretimi sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin."})
    elif user_msg.lower().startswith("resim üret:"):
        prompt = user_msg[len("resim üret:"):].strip()
        try:
            b64_image = generate_image(prompt)
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant_image", "content": b64_image})
        except Exception as e:
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": "Görsel üretimi sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin."})
    else:
        session["messages"].append({"role": "user", "content": user_msg})
        bot_msg = get_rag_response(user_msg)
        session["messages"].append({"role": "assistant", "content": bot_msg})

    save_chat_history(data)

    return {"question": user_msg, "answer": "OK"}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    data = load_chat_history()
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    data["sessions"].remove(session)
    save_chat_history(data)

    return {"status": "success", "id": session_id}

class RenameRequest(BaseModel):
    title: str

@app.patch("/sessions/{session_id}")
def rename_session(session_id: str, request: RenameRequest):
    """
    Belirli bir oturumun başlığını (title) değiştirir.
    """
    data = load_chat_history()
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session["title"] = request.title
    save_chat_history(data)
    return {"status": "renamed", "id": session_id, "newTitle": request.title}
