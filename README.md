
# ⚽ Futbol Kuralları Chatbot

Bu proje, kullanıcıların futbol kurallarıyla ilgili sorularına hızlı, doğru ve interaktif olarak cevap alabilecekleri modern bir chatbot uygulamasıdır. Kullanıcı dostu tasarım ve gelişmiş AI altyapısıyla geliştirilmiş, hem yazılı hem de sesli iletişimi destekler.

----------

## 🛠️ Kullanılan Teknolojiler

-   **FastAPI** – Web servisleri ve API yönetimi için.
-   **Streamlit** – Alternatif chatbot arayüzü ve ses tanıma desteği.
-   **LangChain ve ChromaDB** – PDF verilerinin yüklenmesi ve vektör tabanlı içerik araması için.
-   **Google Gemini AI** – Gelişmiş AI yanıtları üretme ve embedding işlemleri.
-   **HTML/CSS/JavaScript** – Etkileşimli ve mobil uyumlu kullanıcı arayüzü.
-   **SpeechRecognition ve Web Speech API** – Sesli komut algılama ve sesli cevap özellikleri.

----------

## 📁 Proje Yapısı

```
Futbol_ChatBot
├── api.py                # FastAPI tabanlı Backend API
├── bot.py                # Streamlit chatbot arayüzü
├── chat_history.json     # Sohbet geçmişi verileri
├── chroma_db             # Vektör veritabanı (Chroma)
├── static
│   ├── script.js         # Front-end JavaScript fonksiyonları
│   └── styles.css        # Arayüz tasarım dosyası
├── templates
│   └── index.html        # Ana arayüz (Jinja2 template)
├── FutbolKuralları.pdf   # Chatbot'un bilgi kaynağı PDF
├── requirements.txt      # Python bağımlılıkları
└── .env                  # API anahtarları ve hassas veriler

```

----------

## 🚀 Kurulum ve Kullanım

### 1. Bağımlılıkları Yükleme

```bash
pip install -r requirements.txt

```

### 2. FastAPI Uygulamasını Başlatma

```bash
uvicorn api:app --reload

```

Tarayıcınızda `http://localhost:8000` adresinden chatbot arayüzüne erişebilirsiniz.


![Image](https://github.com/user-attachments/assets/7886a5ef-2ebc-485e-8cde-89f09d0e8933)



### 3. Streamlit Chatbot'u Başlatma

```bash
streamlit run bot.py

```

Sesli destekli alternatif chatbot arayüzü açılacaktır.


![Image](https://github.com/user-attachments/assets/cdf23fdb-5dac-4e8c-8f42-df8286f0803e)

----------

## 🌟 Temel Özellikler

-   **Chat Geçmişi Yönetimi:** Oturumları kaydetme, tekrar yükleme ve silme.
-   **Oturum Düzenleme:** Her sohbet başlığı düzenlenebilir ve silinebilir.
-   **Sesli Komut ve Yanıt:** Kullanıcılar "Asistan" diyerek sesli sorular sorabilir ve yanıtları sesli olarak dinleyebilir.
-   **Gerçek Zamanlı Etkileşim:** Kullanıcı dostu web arayüzü sayesinde hızlı ve anlık cevaplar.
-   **Gelişmiş Yapay Zeka:** Google Gemini AI ile sağlanan doğru ve bağlamsal yanıtlar.

----------

## 🎨 Kullanıcı Arayüzü Özellikleri

-   **Kolay ve Modern Tasarım:** Kullanıcı dostu, mobil uyumlu ve estetik bir arayüz.
-   **İnteraktif Butonlar:** Düzenleme (✏️) ve silme (🗑️) butonları ile kolay oturum yönetimi.
-   **Dinamik Modallar:** Oturum silme ve ad değiştirme için modern modal pencereler.

----------

## 🗃️ Teknik Detaylar

-   **FastAPI** ile RESTful API uç noktaları (`GET`, `POST`, `DELETE`, `PATCH`).
-   **Streamlit** ile hızlı prototipleme ve sesli etkileşim.
-   **RAG (Retrieval-Augmented Generation)** mimarisi kullanılarak PDF içeriğinden otomatik yanıt üretimi.

----------

## 📌 Kullanım Senaryoları

-   **Futbol severler** ve **antrenörler** için hızlı bilgi kaynağı.
-   **Eğitim** ve **öğrenme** amaçlı soru-cevap uygulaması.
-   **Etkileşimli ve eğlenceli** içerik üretimi.

----------

## 📞 İletişim ve Destek

Proje ile ilgili herhangi bir sorunuz veya öneriniz için:

-   **Mahmut Kerem Erden** - [k.erden03@gmail.com](mailto:k.erden03@gmail.com)

