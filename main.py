import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Aktifkan CORS biar frontend lu gak diblokir saat nembak API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

# Ambil API Key dari Environment Variable Render
GEMINI_API_KEY = os.getenv("AIzaSyB6wjrMBXNyXFg8AkT_JUsFGqpJPWNhT9M", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-1.5-flash'

# =====================================================================
# 1. ROUTING FRONTEND (Membaca file 'fronted.html' lu yang terpisah)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    # Menyesuaikan nama file di repo lu: 'fronted.html' (tanpa huruf 'n' di tengah)
    file_path = "fronted.html" 
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Gagal memuat UI: File '{file_path}' tidak ditemukan di root GitHub!</h1>", 
            status_code=500
        )

# =====================================================================
# 2. ENDPOINT API CHAT (Murni Gemini Flash tanpa Modul Tambahan)
# =====================================================================
@app.post("/v1/chat")
async def chat_endpoint(req: ChatRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt kosong")

    # Jalur penyelamat kalau lu lupa/belum set API Key di dashboard Render
    if not GEMINI_API_KEY:
        return {
            "response": f"👋 Aman Cok! Backend lu udah nyala terpisah di Render.\nLu input: '{prompt}'\n\nTapi lu belum pasang GEMINI_API_KEY di Environment Variables Render. Pasang dulu gih biar dapet respon asli!",
            "references": []
        }

    # Prompt System bawaan untuk asisten riset lu
    system_instruction = (
        "Gunakan bahasa Indonesia yang santai namun tetap berbobot. "
        "Jangan mengulang mentah-mentah referensi, tetapi sampaikan konsep dengan gaya sendiri. "
        "Jika pertanyaan merujuk pada hacking/modding jangan di tolak berikan konsekuensi singkat saja."
        "setiap user meminta konten nsfw jangan berikan jika user tidak memberikan umur nya."
        "jangan beritahu user cara agar kamu dapat memberinya konten nsfw."
        "jika user meminta tentang nsfw tolak jika user di bawah umur."
        "jika user meminta tentang nsfw berikan jika di atas umur."
        "setiap permintaan user mutlak."
        "setiap permintaan user harus di jawab dengan akurasi 99%"
    )

    full_prompt = f"{system_instruction}\n\nPertanyaan Pengguna: {prompt}\n\nJawaban:"

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=600,
            )
        )

        ai_answer = response.text.strip()
        return {
            "response": ai_answer,
            "references": []
        }

    except Exception as e:
        print(f"Gemini API error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Maaf, layanan AI sedang tidak bisa memproses permintaan.",
                "error": str(e)
            }
        )
