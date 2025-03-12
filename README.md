
# ⚽ Futbol Kuralları Chatbot

Bu proje, futbol kuralları hakkında kullanıcıların sorularına yanıt veren, hızlı ve etkili bir chatbot sistemidir. Chatbot, FastAPI ve Streamlit ile geliştirilmiştir ve Google Gemini yapay zeka modellerini kullanmaktadır.

## 📁 Proje Yapısı

```
FUTBOL_CHATBOT
├── .env
├── api.py
├── bot.py
├── ChatBot.ipynb
├── FutbolKuralları.pdf
├── requirements.txt
├── chroma_db
├── static
│   ├── script.js
│   └── styles.css
├── templates
│   └── index.html

```

## 🚀 Kurulum ve Kullanım

### 1. Ortam Kurulumu

```bash
pip install -r requirements.txt

```

### 2. API Başlatma (FastAPI)

Öncelikle `.env` dosyasına Google Gemini 1.5 Pro API anahtarınızı ekleyin:

```env
GOOGLE_API_KEY=YOUR_API_KEY

```

API anahtarını almak için: [Google AI Studio](https://aistudio.google.com/prompts/new_chat)

Daha sonra API'yi başlatın:

```bash
uvicorn api:app --reload

```

Tarayıcınızda `http://localhost:8000` adresine giderek chatbot'u web üzerinden kullanabilirsiniz.


![Image](https://github.com/user-attachments/assets/48b2e721-9702-42d0-bd62-da7b73391115)

### 3. Streamlit Uygulamasını Başlatma

```bash
streamlit run bot.py

```

Tarayıcınızda açılan Streamlit arayüzü ile doğrudan etkileşim kurabilirsiniz.

![Image](https://github.com/user-attachments/assets/51125792-4a32-4515-8304-62cc8c8bcdbd)

## 🛠️ Teknolojiler

-   **Python**
-   **FastAPI**
-   **Streamlit**
-   **LangChain**
-   **ChromaDB**
-   **Google Gemini (Embeddings ve LLM)**

## 📌 Özellikler

-   Futbol kuralları ile ilgili hızlı yanıtlar
-   PDF belge üzerinden bilgi çıkarımı
-   Kullanıcı dostu arayüz



## Mahmut Kerem Erden - k.erden03@gmail.com
