from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends
import uuid
from sqlalchemy.orm import Session
from app.main import QueryRequest, RenameRequest, get_rag_response, load_chat_history, save_chat_history, find_session, templates
from app.utils import generate_image, generate_music, process_uploaded_file, build_rag_chain
from app.database import get_db
from app.models import Feedback, User
import base64
from datetime import datetime
import os

router = APIRouter()

# =====================================
# 1. Ana Sayfa ve Soru Sorma Endpoints
# =====================================

@router.get("/")
def home(request: Request):
    """Ana sayfa için index.html şablonunu döndürür."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/ask")
def ask_question(request: Request, request_body: QueryRequest):
    """
    Kullanıcıdan gelen soruyu alır, RAG zinciri üzerinden cevap üretir.

    Args:
        request: FastAPI isteği
        request_body: QueryRequest modeli ile soru içeriği

    Returns:
        dict: 'question' ve 'answer' içeren JSON yanıt
    """
    query = request_body.question.strip()                  # Gereksiz boşlukları kaldır
    answer = get_rag_response(query)                       # RAG cevabını al
    return {"question": query, "answer": answer}


# =====================================
# 2. Oturum Yönetimi (Session) Endpoints
# =====================================

@router.get("/sessions")
def list_sessions(request: Request):
    """Kullanıcının chat geçmişindeki oturumları listeler."""
    data = load_chat_history(request)
    return [{"id": s["id"], "title": s["title"]} for s in data.get("sessions", [])]

@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request):
    """
    Belirli bir oturumu getirir.

    Raises:
        HTTPException: Oturum bulunamazsa 404
    """
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")  # Oturum yok
    return session


# =====================================
# 3. Doküman Yükleme ve İşleme Endpoint’i
# =====================================

@router.post("/upload-document")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """
    Kullanıcının PDF/doküman yüklemesini alır, kaydeder ve metnini çıkarır.

    Returns:
        dict: 'session_id', 'message', 'saved_path'
    """
    encoded_user = request.cookies.get("user")
    if not encoded_user:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama hatası")  # Çerez yok

    try:
        username = base64.b64decode(encoded_user).decode("utf-8")
    except Exception:
        username = "anonymous"                                       # Çözme hatasında anonim kullanıcı

    timestamp = datetime.now().strftime("%d.%m.%Y-%H.%M")           # Yükleme zamanı
    ext = os.path.splitext(file.filename)[1]
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    save_name = f"{username}-{timestamp}{ext}"
    save_path = os.path.join(upload_dir, save_name)
    content = await file.read()                                     # Dosya içeriğini oku
    with open(save_path, "wb") as f:
        f.write(content)                                            # Diske kaydet
    file.file.seek(0)                                               # Akışı başa sar

    try:
        extracted_text = process_uploaded_file(file)                # Metni çıkar
    except Exception as e:
        print("Dosya işleme hatası:", e)
        raise HTTPException(status_code=400, detail=str(e))

    session_id = str(uuid.uuid4())
    new_session = {
        "id": session_id,
        "title": file.filename,
        "document_text": extracted_text,
        "messages": [
            {"role": "system", "content": "Belge başarıyla yüklendi ve işlendi. Şimdi soru sorabilirsiniz."}
        ]
    }
    data = load_chat_history(request)
    data.setdefault("sessions", []).append(new_session)
    save_chat_history(request, data)

    return {
        "session_id": session_id,
        "message": "Belge başarıyla yüklendi ve işlendi.",
        "saved_path": save_path
    }

@router.post("/sessions/{session_id}/reset-document")
def reset_document(session_id: str, request: Request):
    """Oturumdaki doküman metnini sıfırlar."""
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["document_text"] = ""                                   # Metni temizle
    save_chat_history(request, data)
    return {"status": "document reset", "session_id": session_id}


# =====================================
# 4. Oturum Oluşturma ve Mesaj Ekleme
# =====================================

@router.post("/sessions")
def create_session(request: Request, request_body: QueryRequest):
    """
    Yeni bir oturum oluşturur;
    Resim veya müzik isteğine göre içerik üretir veya RAG cevabı ekler.
    """
    data = load_chat_history(request)
    session_id = str(uuid.uuid4())
    user_msg = request_body.question.strip()

    if user_msg.lower().startswith("resim üret:"):
        prompt_text = user_msg[len("resim üret:"):].strip()
        try:
            b64_image = generate_image(prompt_text)
            new_session = {
                "id": session_id,
                "title": user_msg[:40],
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant_image", "content": b64_image}
                ]
            }
        except Exception:
            new_session = {
                "id": session_id,
                "title": "Görsel Üretim Hatası",
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": "Görsel üretimi sırasında hata oluştu, lütfen daha sonra deneyin."}
                ]
            }
    elif user_msg.lower().startswith("müzik üret:"):
        prompt_text = user_msg[len("müzik üret:"):].strip()
        try:
            b64_audio = generate_music(prompt_text)
            new_session = {
                "id": session_id,
                "title": user_msg[:40],
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant_audio", "content": b64_audio}
                ]
            }
        except Exception:
            new_session = {
                "id": session_id,
                "title": "Müzik Üretim Hatası",
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": "Müzik üretimi sırasında hata oluştu, lütfen daha sonra deneyin."}
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

    data.setdefault("sessions", []).append(new_session)
    save_chat_history(request, data)
    return new_session

@router.post("/sessions/{session_id}/messages")
def add_message(session_id: str, request: Request, request_body: QueryRequest):
    """
    Varolan bir oturuma kullanıcı mesajı ekler ve yanıt üretir.
    """
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = request_body.question.strip()

    if session.get("document_text", "").strip():
        try:
            chain = build_rag_chain(session["document_text"])
            response = chain.invoke({"input": user_msg})
            bot_msg = response["answer"]
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": bot_msg})
        except Exception:
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": "Dinamik sorgu oluşturulurken hata meydana geldi."})
    else:
        if user_msg.lower().startswith("resim üret:"):
            prompt_text = user_msg[len("resim üret:"):].strip()
            try:
                b64_image = generate_image(prompt_text)
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant_image", "content": b64_image})
            except Exception:
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant", "content": "Görsel üretimi sırasında hata oluştu, lütfen daha sonra deneyin."})
        elif user_msg.lower().startswith("müzik üret:"):
            prompt_text = user_msg[len("müzik üret:"):].strip()
            try:
                b64_audio = generate_music(prompt_text)
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant_audio", "content": b64_audio})
            except Exception:
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant", "content": "Müzik üretimi sırasında hata oluştu, lütfen daha sonra deneyin."})
        else:
            session["messages"].append({"role": "user", "content": user_msg})
            bot_msg = get_rag_response(user_msg)
            session["messages"].append({"role": "assistant", "content": bot_msg})

    save_chat_history(request, data)
    return {"question": user_msg, "answer": "OK"}


# =====================================
# 5. Oturum Silme ve Yeniden Adlandırma
# =====================================

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, request: Request):
    """Belirtilen oturumu siler."""
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    data["sessions"].remove(session)
    save_chat_history(request, data)
    return {"status": "success", "id": session_id}

@router.patch("/sessions/{session_id}")
def rename_session(session_id: str, request: Request, request_body: RenameRequest):
    """Oturum başlığını günceller."""
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["title"] = request_body.title                          # Yeni başlığı ata
    save_chat_history(request, data)
    return {"status": "renamed", "id": session_id, "newTitle": request_body.title}


# =====================================
# 6. Geri Bildirim Endpoint’i
# =====================================

@router.post("/feedback")
async def save_feedback(request: Request, db: Session = Depends(get_db)):
    """
    Kullanıcının oturum ile ilgili geri bildirimini veritabanına kaydeder.
    """
    body = await request.json()
    encoded = request.cookies.get("user")
    if not encoded:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama hatası")

    try:
        username = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=401, detail="Kullanıcı adı çözümlenemedi")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    feedback = Feedback(
        user_id=user.id,
        session_id=body.get("session_id"),
        question=body.get("question"),
        answer=body.get("answer"),
        feedback_text=body.get("feedback_text"),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"status": "success", "id": feedback.id}
