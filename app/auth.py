from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from passlib.context import CryptContext
import jwt
import os
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import base64

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")


# =====================================
# 1. Parola Hashleme ve Doğrulama
# =====================================

def get_password_hash(password: str) -> str:
    """
    Düz metin parolayı bcrypt ile hash’ler.
    """
    return pwd_context.hash(password)  # Güvenli hash üret

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Düz parolayı ve hash’i karşılaştırarak doğrular.
    """
    return pwd_context.verify(plain_password, hashed_password)


# =====================================
# 2. Giriş Formu ve İşleme
# =====================================

@router.get("/login")
def login_form(request: Request, error: str = None):
    """
    login.html şablonunu döndürür.
    error parametresi varsa formda gösterilir.
    """
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı adı ve parolayı kontrol eder;
    Başarılıysa base64 ile kodlanmış kullanıcıyı çerezde saklar.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        # Başarısızsa tekrar login sayfasına yönlendir
        return RedirectResponse(url="/auth/login?error=1", status_code=303)

    encoded_username = base64.b64encode(username.encode("utf-8")).decode("utf-8")  # Çereze yazılacak değer

    redirect = RedirectResponse(url="/index", status_code=303)
    redirect.set_cookie(key="user", value=encoded_username)  # Kimlik çerezi ayarla
    return redirect


# =====================================
# 3. Kayıt Formu ve İşleme
# =====================================

@router.get("/register")
def register_form(request: Request, error: str = None):
    """
    register.html şablonunu döndürür.
    error parametresi varsa formda gösterilir.
    """
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@router.post("/register")
def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı kaydını yapar;
    Kullanıcı adı veya email var ise hata ile kayıt formuna yönlendirir.
    """
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        return RedirectResponse(url="/auth/register?error=1", status_code=303)  # Çakışma

    hashed_password = get_password_hash(password)   # Parolayı hashle
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/auth/login", status_code=303)  # Kayıt sonrası login’e yönlendir


# =====================================
# 4. Çıkış (Logout)
# =====================================

@router.post("/logout")
def logout():
    """
    Kullanıcı çerezini siler ve login sayfasına yönlendirir.
    """
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user")  # Kimlik çerezini temizle
    return response
