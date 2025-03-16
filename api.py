# çalıştırmak için : uvicorn api:app --reload    http://localhost:8000/

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request

#  Çevre değişkenlerini yükle
load_dotenv()

#  FastAPI uygulamasını başlat
app = FastAPI()

#  Static ve Template dosyalarını bağla
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#  Ana sayfa (HTML arayüzü)
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#  ChromaDB ve LLM modelini yükleme
if "vectorstore" not in globals():
    print("📖 PDF yükleniyor ve işleniyor...")
    
    #  Google Gemini Embedding modelini başlat
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    #  ChromaDB'yi başlat ve yükle
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

    #  Retriever oluştur 
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    #  Google Gemini LLM'yi başlat
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0.3,
        max_tokens=500
    )

    #  Sistem Prompt'u
    system_prompt = (
        "Sen bir yardımcı asistansın ve yalnızca futbol kuralları hakkında sorulara cevap veriyorsun. "
        "Yanıtlarını yalnızca verilen bağlam içeriğinden oluştur. "
        "Eğer sorunun cevabını bilmiyorsan, 'Bu konuda yardımcı olamıyorum.' de. "
        "Cevaplarını en fazla üç cümle ile ver ve doğru bilgi içerdiğinden emin ol.\n\n"
        "{context}"
    )

    #  Prompt Şablonu
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}")
        ]
    )

    #  Question-Answer zincirini oluştur
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    #  Retriever + LLM kombinasyonu ile RAG zincirini oluştur
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

#  Kullanıcıdan gelen sorguyu tanımlamak için bir model oluştur
class QueryRequest(BaseModel):
    question: str

#  Chatbot için bir API endpoint'i oluştur
@app.post("/ask")
def ask_question(request: QueryRequest):
    query = request.question
    print(f"📨 Soru alındı: {query}")

    # Yanıtı oluştur
    response = rag_chain.invoke({"input": query})
    answer = response["answer"]

    print(f"🤖 Yanıt: {answer}")
    return {"question": query, "answer": answer}
