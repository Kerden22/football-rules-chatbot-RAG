# init_db.py
from app.database import Base, engine
from app import models  # Bu satır çok önemli! Kullanmazsan tablo oluşmaz

print("🔄 Veritabanı tabloları oluşturuluyor...")
Base.metadata.create_all(bind=engine)
print("✅ Veritabanı hazır.")
