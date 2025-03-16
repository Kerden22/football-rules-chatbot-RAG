# çalıştırmak için : streamlit run bot.py 

import streamlit as st
import speech_recognition as sr
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

# .env dosyasını yükle
load_dotenv()

# Streamlit başlık
st.title("⚽ Futbol Kuralları Chatbot'u 🎤")

# PDF'yi ve vektör veritabanını sadece bir kez yükle
if "vectorstore" not in st.session_state:
    with st.spinner("📖 PDF yükleniyor ve işleniyor..."):
        loader = PyPDFLoader("FutbolKuralları.pdf")
        data = loader.load()
        
        # PDF'yi tek bir metin haline getir
        all_text = "\n".join([page.page_content for page in data])

        # Metni chunk'lara bölme işlemi
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_text(all_text)

        # Google Gemini Embedding modelini başlat
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # ChromaDB'yi başlat ve embedding işlemi yap
        vectorstore = Chroma.from_texts(texts=docs, embedding=embeddings, persist_directory="./chroma_db")

        # ChromaDB tekrar yükleme
        vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

        # Yalnızca ilk çalıştırmada yükleyelim
        st.session_state.vectorstore = vectorstore

# 📌 Retriever oluştur (benzerlik araması yapacak)
retriever = st.session_state.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

# Google Gemini LLM'yi başlat
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.3,
    max_tokens=500
)

# Sistem Prompt'u 
system_prompt = (
    "Sen bir yardımcı asistansın ve yalnızca futbol kuralları hakkında sorulara cevap veriyorsun. "
    "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
    "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
    "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
    "{context}"
)

# Prompt Şablonu
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}")
    ]
)

# Question-Answer zincirini oluştur
question_answer_chain = create_stuff_documents_chain(llm, prompt)

# Retriever + LLM kombinasyonu ile RAG zincirini oluştur
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# Sohbet geçmişini göster
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# SES ALGILAMA FONKSİYONU (Mikrofondan giriş alma)
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Dinleniyor...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio, language="tr-TR")
        except:
            return None

# Mikrofon Butonunu Sabitleyen CSS
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] div:has(> div.stChatInputContainer) {
            position: fixed;
            bottom: 0;
            width: 100%;
            z-index: 100;
            background: #1e1e1e; /* Arka planı sabit koyu renk */
            padding: 10px;
            display: flex;
            justify-content: space-between;
        }

        #mic-btn {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            margin-right: 10px;
        }

        #mic-btn:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

# Mikrofon Butonu Sabit Konumda
col1, col2 = st.columns([1, 8])
with col1:
    mic_clicked = st.button("🎤", key="mic-btn")

# Kullanıcının Yazılı Girişi
query = st.chat_input("⚽ Futbol kuralları hakkında bir soru sor:")

# Eğer Mikrofon Butonuna Basılırsa Sesle Soru Sor
if mic_clicked:
    query = recognize_speech()
    if query is None:
        st.error("⚠️ Ses algılanamadı, lütfen tekrar deneyin.")

# Eğer Kullanıcıdan Giriş Varsa Chatbota Gönder
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.spinner("Yanıt hazırlanıyor..."):
        response = rag_chain.invoke({"input": query})  # Chatbot'a gönder
        answer = response["answer"]

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)
