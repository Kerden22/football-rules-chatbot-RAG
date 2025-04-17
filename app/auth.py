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

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.get("/login")
def login_form(request: Request, error: str = None):
    """
    login.html şablonunu döndürür.
    """
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/auth/login?error=1", status_code=303)

    # Kullanıcı adını base64 ile encode et
    encoded_username = base64.b64encode(username.encode("utf-8")).decode("utf-8")

    redirect = RedirectResponse(url="/index", status_code=303)
    redirect.set_cookie(key="user", value=encoded_username)
    return redirect

@router.get("/register")
def register_form(request: Request, error: str = None):
    """
    register.html şablonunu döndürür. Hata varsa ekranda gösterilir.
    """
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@router.post("/register")
def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if user:
        # Kayıt hatası: hata parametresi ile register sayfasına yönlendir
        return RedirectResponse(url="/auth/register?error=1", status_code=303)
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/auth/login", status_code=303)

@router.post("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user")  # Kullanıcıyı çıkış yaptır
    return response
