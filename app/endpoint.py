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

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/ask")
def ask_question(request: Request, request_body: QueryRequest):
    query = request_body.question.strip()
    answer = get_rag_response(query)
    return {"question": query, "answer": answer}

@router.get("/sessions")
def list_sessions(request: Request):
    data = load_chat_history(request)
    return [{"id": s["id"], "title": s["title"]} for s in data.get("sessions", [])]

@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request):
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/upload-document")
async def upload_document(request: Request, file: UploadFile = File(...)):
    # 1) Kullanıcı adı al
    encoded_user = request.cookies.get("user")
    if not encoded_user:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama hatası")
    try:
        username = base64.b64decode(encoded_user).decode("utf-8")
    except Exception:
        username = "anonymous"

    # 2) Timestamp oluştur
    timestamp = datetime.now().strftime("%d.%m.%Y-%H.%M")

    # 3) Uzantıyı ayıkla ve uploads klasörünü hazırla
    ext = os.path.splitext(file.filename)[1]
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # 4) Dosyayı kaydet
    save_name = f"{username}-{timestamp}{ext}"
    save_path = os.path.join(upload_dir, save_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    # tekrar okuyabilmek için stream’i başa sar
    file.file.seek(0)

    # 5) Mevcut işlemle metni çıkar
    try:
        extracted_text = process_uploaded_file(file)
    except Exception as e:
        print("Dosya işleme hatası:", e)
        raise HTTPException(status_code=400, detail=str(e))

    # 6) Yeni oturum (session) yarat ve cevap döndür
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
        "saved_path": save_path  # (isteğe bağlı)
    }

@router.post("/sessions/{session_id}/reset-document")
def reset_document(session_id: str, request: Request):
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["document_text"] = ""
    save_chat_history(request, data)
    return {"status": "document reset", "session_id": session_id}

@router.post("/sessions")
def create_session(request: Request, request_body: QueryRequest):
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
        except Exception as e:
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
        except Exception as e:
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
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = request_body.question.strip()

    if "document_text" in session and session["document_text"].strip():
        try:
            chain = build_rag_chain(session["document_text"])
            response = chain.invoke({"input": user_msg})
            bot_msg = response["answer"]
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": bot_msg})
        except Exception as e:
            session["messages"].append({"role": "user", "content": user_msg})
            session["messages"].append({"role": "assistant", "content": "Dinamik sorgu oluşturulurken hata meydana geldi."})
    else:
        if user_msg.lower().startswith("resim üret:"):
            prompt_text = user_msg[len("resim üret:"):].strip()
            try:
                b64_image = generate_image(prompt_text)
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant_image", "content": b64_image})
            except Exception as e:
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant", "content": "Görsel üretimi sırasında hata oluştu, lütfen daha sonra deneyin."})
        elif user_msg.lower().startswith("müzik üret:"):
            prompt_text = user_msg[len("müzik üret:"):].strip()
            try:
                b64_audio = generate_music(prompt_text)
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant_audio", "content": b64_audio})
            except Exception as e:
                session["messages"].append({"role": "user", "content": user_msg})
                session["messages"].append({"role": "assistant", "content": "Müzik üretimi sırasında hata oluştu, lütfen daha sonra deneyin."})
        else:
            session["messages"].append({"role": "user", "content": user_msg})
            bot_msg = get_rag_response(user_msg)
            session["messages"].append({"role": "assistant", "content": bot_msg})

    save_chat_history(request, data)
    return {"question": user_msg, "answer": "OK"}

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, request: Request):
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    data["sessions"].remove(session)
    save_chat_history(request, data)
    return {"status": "success", "id": session_id}

@router.patch("/sessions/{session_id}")
def rename_session(session_id: str, request: Request, request_body: RenameRequest):
    data = load_chat_history(request)
    session = find_session(data, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["title"] = request_body.title
    save_chat_history(request, data)
    return {"status": "renamed", "id": session_id, "newTitle": request_body.title}

# GERİ BİLDİRİM ENDPOINTİ
@router.post("/feedback")
async def save_feedback(request: Request, db: Session = Depends(get_db)):
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