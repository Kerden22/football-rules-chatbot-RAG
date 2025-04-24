import os
import requests
import base64
import uuid  
import docx 
import time

# =====================================
# 1. Çeviri Fonksiyonu
# =====================================

def translate_to_english(text: str) -> str:
    """
    Gelen Türkçe metni MyMemory API ile İngilizceye çevirir.
    """
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "tr|en"}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("responseData", {}).get("translatedText", text)
        return text  # Başarısızsa orijinal metni döndür
    except Exception as e:
        print("Translation error:", e)  # Hata bilgisini logla
        return text


# =====================================
# 2. Görsel Üretim Fonksiyonu
# =====================================

def generate_image(prompt: str) -> str:
    """
    Prompt'u önce İngilizceye çevirir, sonra Stability AI API ile görsel üretir.
    """
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
    if not STABILITY_API_KEY:
        raise Exception("STABILITY_API_KEY is not set in .env")

    english_prompt = translate_to_english(prompt)  # Prompt'u İngilizceye çevir

    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
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
            raise Exception(f"Stability API hatası: {response.text}")
        image_base64 = response.json()["artifacts"][0]["base64"]
        return image_base64
    except Exception as e:
        raise Exception(f"Resim üretim hatası: {e}")


# =====================================
# 3. Müzik Üretim Fonksiyonu
# =====================================

def generate_music(prompt: str) -> str:
    """
    Türkçe prompt'u İngilizceye çevirir ve GoAPI DiffRhythm ile müzik üretir.
    Üretilen ses dosyasını indirip base64 string olarak döner.
    """
    english_prompt = translate_to_english(prompt)

    GOAPI_API_KEY = os.getenv("GOAPI_API_KEY", "")
    if not GOAPI_API_KEY:
        raise Exception("GOAPI_API_KEY is not set in .env")

    TASK_URL = "https://api.goapi.ai/api/v1/task"
    headers = {"X-API-Key": GOAPI_API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": "Qubico/diffrhythm",
        "task_type": "txt2audio-base",
        "input": {
            "lyrics": "",                
            "style_prompt": english_prompt,
            "duration": 30               
        }
    }

    print("🎶 Şarkı üretme isteği gönderiliyor...")
    post_response = requests.post(TASK_URL, headers=headers, json=payload)
    if post_response.status_code != 200:
        raise Exception(f"API isteği başarısız: {post_response.status_code}, {post_response.text}")

    task_id = post_response.json()["data"]["task_id"]
    print(f"✅ Task ID: {task_id}")

    get_url = f"{TASK_URL}/{task_id}"
    max_tries = 24                      # 24 * 5s = 120s maksimum bekleme
    for _ in range(max_tries):
        time.sleep(5)                   # 5 saniye ara ver
        get_response = requests.get(get_url, headers=headers)
        if get_response.status_code != 200:
            print(f"❌ Sorgulama hatası: {get_response.status_code}")
            continue
        data = get_response.json()["data"]
        status = data.get("status", "unknown")
        print(f"Durum: {status}")
        if status == "completed":
            audio_url = data["output"]["audio_url"]
            print("✅ Müzik üretildi! Audio URL alındı.")
            break
    else:
        raise Exception("Müzik üretimi zaman aşımına uğradı.")

    audio_response = requests.get(audio_url)
    if audio_response.status_code != 200:
        raise Exception("Audio dosyası indirilemedi.")

    b64_audio = base64.b64encode(audio_response.content).decode("utf-8")
    return b64_audio


# =====================================
# 4. Yüklenen Dosyayı İşleme Fonksiyonu
# =====================================

def process_uploaded_file(uploaded_file) -> str:
    """
    Yüklenen PDF, TXT veya DOCX dosyasından metni çıkarır.
    """
    filename = uploaded_file.filename.lower()
    if filename.endswith(".pdf"):
        temp_path = f"temp_{uuid.uuid4().hex}.pdf"
        with open(temp_path, "wb") as f:
            content = uploaded_file.file.read()
            f.write(content)
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(temp_path)
        data = loader.load()
        os.remove(temp_path)
        return "\n".join(page.page_content for page in data)

    elif filename.endswith(".txt"):
        content = uploaded_file.file.read()
        try:
            return content.decode("utf-8")
        except Exception:
            return content.decode("iso-8859-9")  # Fallback kodlama

    elif filename.endswith(".docx"):
        temp_path = f"temp_{uuid.uuid4().hex}.docx"
        with open(temp_path, "wb") as f:
            content = uploaded_file.file.read()
            f.write(content)
        doc = docx.Document(temp_path)
        os.remove(temp_path)
        return "\n".join(para.text for para in doc.paragraphs)

    else:
        raise Exception("Desteklenmeyen dosya türü. Lütfen PDF, TXT veya DOCX yükleyin.")


# =====================================
# 5. Dinamik RAG Zinciri Oluşturma
# =====================================

def build_rag_chain(document_text: str):
    """
    Verilen metni kullanarak dinamik bir Retrieval-Augmented Generation zinciri oluşturur.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter  
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain.chains import create_retrieval_chain
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.chains.combine_documents import create_stuff_documents_chain

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_text(document_text)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma.from_texts(docs, embeddings)  # persist_directory verilmedi: geçici yapı
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    system_prompt = (
        "Sen bir yardımcı asistansın ve yalnızca yüklenen doküman içeriğine dayalı sorulara cevap veriyorsun. "
        "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
        "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
        "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
        "{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3, max_tokens=500)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    dynamic_rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return dynamic_rag_chain
