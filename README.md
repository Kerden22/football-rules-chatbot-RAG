
# ChatAsistan: Belge & Soru Cevap

Bu proje, kullanıcıların futbol kurallarıyla ilgili sorularını veya yükledikleri kendi belgelerini baz alarak hızlı, doğru ve interaktif cevaplar alabilecekleri modern bir chatbot uygulamasıdır. Kullanıcı dostu arayüzü, gelişmiş yapay zekâ entegrasyonu ve kapsamlı oturum yönetimi sayesinde benzersiz bir kullanıcı deneyimi sunar.

----------

## 🛠️ Kullanılan Teknolojiler

-   **FastAPI** – Backend servisleri ve API yönetimi.
    
-   **LangChain & ChromaDB** – Doküman yükleme, içerik sorgulama ve vektör arama işlemleri.
    
-   **Google Gemini AI** – Bağlamsal sorgulama, yanıt oluşturma ve embedding işlemleri.
    
-   **Stability AI ve GoAPI.ai** – Görsel ve müzik içeriği üretimi.
    
-   **HTML/CSS/JavaScript** – Etkileşimli ve mobil uyumlu kullanıcı arayüzü.
    
-   **SpeechRecognition & Web Speech API** – Sesli komut ve yanıt desteği.
    
-   **SQLite** – Kullanıcı kimlik doğrulama ve geri bildirim yönetimi.
    

----------

## 📁 Proje Yapısı

```
Futbol_ChatBot
├── app
│   ├── main.py      
│   ├── auth.py                # Kullanıcı giriş ve kayıt yönetimi
│   ├── endpoint.py            # API endpointleri
│   ├── utils.py               # Yardımcı fonksiyonlar
│   ├── database.py            # Veritabanı bağlantı ve modeller
│   └── models.py              # Veritabanı modelleri
├── static
│   ├── script.js              # Frontend JavaScript kodları
│   └── styles.css             # Arayüz tasarımı
├── templates
│   ├── index.html             # Ana chatbot arayüzü
│   ├── login.html             # Kullanıcı giriş ekranı
│   └── register.html          # Kullanıcı kayıt ekranı
├── uploads                    # Kullanıcı belgelerinin saklandığı dizin
├── data                       # Kullanıcı sohbet geçmişi JSON dosyaları
├── chroma_db                  # Vektör veritabanı (ChromaDB)
├── FutbolKuralları.pdf        # Varsayılan bilgi kaynağı
├── requirements.txt           # Python bağımlılıkları
├── init_db.py                 # Database kurulumu
├── bot.py                     # Streamlit tabanlı chatbot
└── .env                       # API anahtarları ve gizli veriler
```

----------

## 🚀 Kurulum ve Kullanım

### 1. Bağımlılıkları Yükleyin

```
pip install -r requirements.txt
```

### 2. FastAPI Sunucusunu Başlatın

```
uvicorn app.main:app --reload
```

Tarayıcınızda `http://localhost:8000` adresinden uygulamaya ulaşabilirsiniz.

![Image](https://github.com/user-attachments/assets/28bbbcf8-430b-40d8-8f05-9a0e8f535e9d)

### 3. Kullanıcı İşlemleri

-   **Kayıt olun** veya **giriş yapın**.
    
-   Chatbot'a varsayılan futbol dokümanıyla veya kendi yüklediğiniz belgeler ile sorular sorun.
    

----------
### Streamlit Tabanlı Chatbot'u Başlatma
```
streamlit run bot.py
```
Sesli destekli alternatif chatbot arayüzü açılacaktır. Pdf yükleme desteği yok.

![Image](https://github.com/user-attachments/assets/cdf23fdb-5dac-4e8c-8f42-df8286f0803e)


## 🌟 Temel Özellikler

-   **Doküman İşleme:** Kullanıcı tarafından yüklenen PDF, TXT veya DOCX dosyaları işlenerek içerik üzerinden sorgu yapılır.
    
-   **Sesli Komutlar:** "Asistan" diyerek sesli soru sorabilir ve cevapları sesli olarak dinleyebilirsiniz.
    
-   **İçerik Üretimi:** "resim üret:" veya "müzik üret:" komutları ile yapay zekâ tarafından özel içerikler oluşturulur.
    
-   **Chat ve Oturum Yönetimi:** Sohbetleri düzenleyebilir, yeniden adlandırabilir ve silebilirsiniz.
    
-   **Geri Bildirim Sistemi:** Yanıtları değerlendirin ve geri bildirim sağlayarak uygulamanın gelişimine katkıda bulunun.
    
-   **Güvenli Dosya Yönetimi:** Kullanıcıların yükledikleri belgeler kullanıcı adı ve zaman etiketiyle organize edilir ve saklanır.
    

----------

## 🎨 Kullanıcı Arayüzü Özellikleri

-   **Modern ve Responsive Tasarım:** Mobil ve masaüstü cihazlar için optimize edilmiştir.
    
-   **Etkileşimli Modallar:** Hata, uyarı ve onay durumlarında modern modal pencereler.
    
-   **Dinamik Toast Bildirimleri:** Başarı ve hata durumlarında anlık bilgilendirme mesajları.


![Image](https://github.com/user-attachments/assets/c1f02dd7-2206-4003-b408-414ae970b0a5)



![Image](https://github.com/user-attachments/assets/767e8868-1fd0-43c2-8015-8ec746b21e41)
    
----------

## 🗃️ Teknik Detaylar

-   **FastAPI** tabanlı RESTful API (`GET`, `POST`, `DELETE`, `PATCH`).
    
-   **RAG (Retrieval-Augmented Generation)** mimarisi ile dinamik içerik sorgulama.
    
-   **Kullanıcı oturumu ve chat geçmişleri** JSON formatında saklanır.
    

----------

## 📌 Kullanım Senaryoları

-   Futbol meraklıları ve profesyoneller için bilgi kaynağı.
    
-   Kurumsal belgeler veya eğitim materyallerinden hızlı sorgulama.
    
-   Eğitim, öğretim ve eğlence amaçlı interaktif içerik üretimi.
    

----------

## 📞 İletişim ve Destek

Proje ile ilgili öneri ve sorularınız için:

-   **Mahmut Kerem Erden** - k.erden03@gmail.com
