import os
import requests
import base64
import uuid  # uuid importunu ekledik
import docx  # DOCX işlemleri için python-docx gereklidir

def translate_to_english(text: str) -> str:
    """
    Basit bir çeviri örneği
    """
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "tr|en"}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("responseData", {}).get("translatedText", text)
        return text
    except Exception as e:
        print("Translation error:", e)
        return text

def generate_image(prompt: str) -> str:
    """
    Stability AI API kullanarak, öncelikle prompt'u İngilizceye çevirip, 
    Stable Diffusion üzerinden görsel üretir.
    """
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
    if not STABILITY_API_KEY:
        raise Exception("STABILITY_API_KEY is not set in .env")
    
    # Prompt'u çeviriyoruz
    english_prompt = translate_to_english(prompt)
    
    try:
        response = requests.post(
            url="https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
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

def generate_music(prompt: str) -> str:
    """
    Hugging Face MusicGen API kullanarak müzik üretir.
    """
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    MUSICGEN_MODEL_ID = "facebook/musicgen-small"
    
    if not HUGGINGFACE_API_KEY:
        raise Exception("HUGGINGFACE_API_KEY is not set in .env")
    
    api_url = f"https://api-inference.huggingface.co/models/{MUSICGEN_MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Müzik üretim hatası: {response.text}")
    audio_bytes = response.content
    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    return b64_audio

def process_uploaded_file(uploaded_file) -> str:
    """
    Yüklenen dosyanın türüne göre (PDF, TXT, DOCX) metni çıkartır.
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
        text = "\n".join([page.page_content for page in data])
        return text
    elif filename.endswith(".txt"):
        content = uploaded_file.file.read()
        try:
            text = content.decode("utf-8")
        except Exception:
            text = content.decode("iso-8859-9")
        return text
    elif filename.endswith(".docx"):
        temp_path = f"temp_{uuid.uuid4().hex}.docx"
        with open(temp_path, "wb") as f:
            content = uploaded_file.file.read()
            f.write(content)
        doc = docx.Document(temp_path)
        os.remove(temp_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    else:
        raise Exception("Desteklenmeyen dosya türü. Lütfen PDF, TXT veya DOCX yükleyin.")

def build_rag_chain(document_text: str):
    """
    Verilen doküman metnine göre dinamik bir Retrieval Chain (RAG zinciri) oluşturur.
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
    vectorstore = Chroma.from_texts(docs, embeddings)  # persist_directory yok: dinamik olarak oluşturuluyor
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
