import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

# 📌 .env dosyasını yükle
load_dotenv()

# 📌 Streamlit başlık
st.title("⚽ Futbol Kuralları Chatbot'u")

# 📌 **PDF'yi ve vektör veritabanını sadece bir kez yükle**
if "vectorstore" not in st.session_state:
    with st.spinner("📖 PDF yükleniyor ve işleniyor... (Sadece ilk seferde)"):
        loader = PyPDFLoader("FutbolKuralları.pdf")
        data = loader.load()
        
        # 📌 PDF'yi tek bir metin haline getir
        all_text = "\n".join([page.page_content for page in data])

        # 📌 Metni chunk'lara bölme işlemi
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_text(all_text)

        # 📌 Google Gemini Embedding modelini başlat
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # 📌 ChromaDB'yi başlat ve embedding işlemi yap
        vectorstore = Chroma.from_texts(texts=docs, embedding=embeddings, persist_directory="./chroma_db")

        # 📌 ChromaDB tekrar yükleme
        vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

        # **Yalnızca ilk çalıştırmada yükleyelim**
        st.session_state.vectorstore = vectorstore

# 📌 Retriever oluştur (benzerlik araması yapacak)
retriever = st.session_state.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

# 📌 Google Gemini LLM'yi başlat
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.3,
    max_tokens=500
)

# 📌 Sistem Prompt'u
system_prompt = (
    "Sen bir yardımcı asistansın ve yalnızca futbol kuralları hakkında sorulara cevap veriyorsun. "
    "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
    "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
    "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
    "{context}"
)

# 📌 Prompt Şablonu
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}")
    ]
)

# 📌 Question-Answer zincirini oluştur
question_answer_chain = create_stuff_documents_chain(llm, prompt)

# 📌 Retriever + LLM kombinasyonu ile RAG zincirini oluştur
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# 📌 Sohbet geçmişini göster
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 📌 Kullanıcıdan giriş al
query = st.chat_input("⚽ Futbol kuralları hakkında bir soru sor:")

if query:
    # Kullanıcının mesajını ekranda göster
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.spinner("Yanıt hazırlanıyor..."):
        response = rag_chain.invoke({"input": query})
        answer = response["answer"]

        # Asistanın cevabını ekranda göster
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)
