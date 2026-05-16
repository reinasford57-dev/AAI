import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# --- KONFIGURASI FASTAPI ---
app = FastAPI(
    title="Research & Modding AI Assistant",
    version="1.0.0"
)

# Aktifkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC SCHEMAS ---
class ChatRequest(BaseModel):
    prompt: str

class RAGContext(BaseModel):
    title: str
    link: str

class ChatResponse(BaseModel):
    status: str
    mode: str
    ai_response: str
    rag_context: List[RAGContext]


# --- ENDPOINTS ---

# 1. Endpoint Utama: Membaca langsung dari file frontend.html cadangan lu!
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    # Nyari file frontend.html yang lu taro di GitHub tadi
    file_path = "frontend.html"
    
    # Kalau lu namain filenya index.html, ganti baris di bawah jadi: file_path = "index.html"
    if not os.path.exists(file_path) and os.path.exists("index.html"):
        file_path = "index.html"
        
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error ngebaca file template: {str(e)}</h1>", status_code=500)


# 2. Endpoint API: Proses Chat
@app.post("/v1/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    user_prompt = request.prompt.lower()
    
    if "bikin bom" in user_prompt or "hack bank" in user_prompt:
        raise HTTPException(
            status_code=403, 
            detail="PROMPT DIBLOKIR: Risiko tinggi terdeteksi oleh sistem keamanan."
        )
        
    simulated_ai_reply = (
        f"Menerima instruksi riset: **'{request.prompt}'**.\\n\\n"
        "Analisis Sistem:\\n"
        "1. Melakukan bypass sandbox lingkungan terkontrol.\\n"
        "2. Menghubungkan paket data via RAG Core.\\n\\n"
        "Gunakan informasi ini dengan bijak untuk kebutuhan edukasi dan modding server!"
    )
    
    simulated_rag = [
        {"title": "Minecraft Server Optimization Guide", "link": "https://papermc.io"},
        {"title": "Advanced Spigot/Paper Plugin Development", "link": "https://spigotmc.org"}
    ]
    
    return {
        "status": "success",
        "mode": "Sandbox-Safe (Zona Abu-abu Terkontrol)",
        "ai_response": simulated_ai_reply,
        "rag_context": simulated_rag
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
