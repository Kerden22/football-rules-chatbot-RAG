
# ⚽ Futbol Kuralları Chatbot

Bu proje, futbol kuralları hakkında kullanıcıların sorularına yanıt veren, hızlı ve etkili bir chatbot sistemidir. Chatbot, FastAPI ve Streamlit kullanılarak geliştirilmiştir ve Google Gemini AI modellerini temel alan gelişmiş Retrieval-Augmented Generation (RAG) sistemiyle güçlendirilmiştir.

## 🛠️ Kullanılan Teknolojiler

-   **FastAPI** (Backend ve API Yönetimi)
-   **Streamlit** (Alternatif interaktif chatbot arayüzü)
-   **LangChain & ChromaDB** (PDF İçerik Yükleme ve Vektör Veri Depolama)
-   **Google Gemini API** (Chat ve Embeddings)
-   **HTML, CSS ve JavaScript** (Kullanıcı dostu ve interaktif web arayüzü)
-   **SpeechRecognition ve Web Speech API** (Sesli etkileşim özellikleri)

## 📂 Proje Yapısı

```
Futbol_ChatBot
│
├── api.py (FastAPI Backend)
├── bot.py (Streamlit Chatbot Arayüzü)
├── chat_history.json (Chat geçmişi veritabanı)
├── chroma_db (Vektör veritabanı)
├── static
│   ├── script.js
│   └── styles.css
├── templates
│   └── index.html
├── chat_history.json (Chat geçmişi kayıtları)
├── requirements.txt
└── .env (API anahtarları ve hassas veriler)

```

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin

```bash
pip install -r requirements.txt

```

### 2. FastAPI Backend Başlatma

```bash
uvicorn api:app --reload

```

Tarayıcınızda **[http://localhost:8000](http://localhost:8000/)** adresine giderek chatbot'un web sürümüne ulaşabilirsiniz.

### 2. Streamlit Arayüzünü Başlatma

```bash
streamlit run bot.py

```

Açılan tarayıcı penceresinde alternatif Streamlit arayüzünü kullanabilirsiniz.

## 🎯 Özellikler

-   **Chat Oturum Yönetimi:** Her sohbetin ayrı kaydedilmesi, kullanıcıların eski sohbetlere erişebilmesi
-   **Sohbet Geçmişi:** Kullanıcılar sohbet geçmişlerini görüntüleyebilir, eski sohbetleri yeniden açabilir ve kaldıkları yerden devam edebilirler.
-   **Sesli Komut Özelliği**: Kullanıcılar "Asistan" kelimesini söyleyerek sesli sorgulama yapabilir.
-   **Sesli Yanıtlar**: Bot cevapları sesli olarak okunabilir.
-   **Kolay ve Estetik Tasarım**: Kullanımı basit ve göz alıcı kullanıcı arayüzü ile etkileşim sağlar.

## 📞 İletişim

**Mahmut Kerem Erden** - [k.erden03@gmail.com](mailto:k.erden03@gmail.com)
