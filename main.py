import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
# Library Google GenAI Resmi
from google import genai

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

# --- INITIALIZE GEMINI CLIENT ---
# Render akan otomatis membaca GEMINI_API_KEY yang kita set di dashboard tadi
api_key = os.environ.get("AIzaSyDpqMiX_IYiwp80sKa7U3LhKbJOiCIc7Ds")
client = genai.Client(api_key=api_key) if api_key else None

# --- PYDANTIC SCHEMAS (KONTRAK API TETAP UTUH) ---
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

# 1. UI Loader (Membaca file HTML cadangan lu)
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    file_path = "frontend.html"
    if not os.path.exists(file_path) and os.path.exists("fronted.html"):
        file_path = "fronted.html"
    elif not os.path.exists(file_path) and os.path.exists("index.html"):
        file_path = "index.html"
        
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error ngebaca file template: {str(e)}</h1>", status_code=500)


# 2. API Chat Terintegrasi Otak AI Sungguhan
@app.post("/v1/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    user_prompt = request.prompt
    
    # Filter Keamanan Dasar
    if "bikin bom" in user_prompt.lower() or "hack bank" in user_prompt.lower():
        raise HTTPException(
            status_code=403, 
            detail="PROMPT DIBLOKIR: Risiko tinggi terdeteksi oleh sistem keamanan."
        )
        
    # Pastikan API Key sudah terpasang
    if not client:
        return {
            "status": "fallback",
            "mode": "Offline-Sandbox",
            "ai_response": "⚠️ Master, GEMINI_API_KEY belum terpasang di Environment Variable Render! Selesaikan Langkah 2 dulu ya.",
            "rag_context": []
        }
        
    try:
        # Panggil Gemini Resmi (Model Flash sangat cepat dan hemat RAM)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_prompt,
            config={
                "system_instruction": "Kamu adalah AI asisten riset dan modding server Minecraft. Jawab dengan gaya cyberpunk, singkat, padat, gunakan bahasa Indonesia yang santai tapi solutif."
            }
        )
        # Menangkap text jawaban AI asli
        ai_real_reply = response.text
    except Exception as e:
        ai_real_reply = f"💥 Hubungan ke AI Core terputus: {str(e)}"

    # RAG Context (Tetap disimulasikan sesuai format Frontend)
    simulated_rag = [
        {"title": "Minecraft Server Optimization Guide", "link": "https://papermc.io"},
        {"title": "Advanced Spigot/Paper Plugin Development", "link": "https://spigotmc.org"}
    ]
    
    return {
        "status": "success",
        "mode": "Gemini-1.5-Flash Core (Live)",
        "ai_response": ai_real_reply,   # <--- AMAN! Tetap sinkron dengan UI
        "rag_context": simulated_rag     # <--- AMAN! Tetap sinkron dengan UI
    }
