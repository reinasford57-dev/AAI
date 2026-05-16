        import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# Tetap pertahankan modul deteksi risiko & search dari DeepSeek
from app.core.analyzer import risk_classifier
from app.services.search import search_web

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

# --- PATCH PENYELAMAT STARTUP (TETAP AMAN WALAU KEY KOSONG) ---
GEMINI_API_KEY = os.getenv("AIzaSyB6wjrMBXNyXFg8AkT_JUsFGqpJPWNhT9M", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-1.5-flash'


# =====================================================================
# 1. ROUTING FRONTEND (Tetap Membaca File HTML Terpisah Lu!)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    # Mengarah ke file HTML terpisah lu, sesuaikan namanya (frontend.html / index.html)
    file_path = "frontend.html" 
    if not os.path.exists(file_path) and os.path.exists("index.html"):
        file_path = "index.html"
        
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Gagal memuat UI: File '{file_path}' tidak ditemukan di GitHub!</h1>", 
            status_code=500
        )


# =====================================================================
# 2. ENDPOINT API CHAT (Logika Murni DeepSeek)
# =====================================================================
@app.post("/v1/chat")
async def chat_endpoint(req: ChatRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt kosong")

    # 1. Risk classification
    risk = risk_classifier.analyze(prompt)
    if risk["status"] == "blocked":
        return JSONResponse(
            status_code=403,
            content={"detail": f"Prompt diblokir (risk score: {risk['risk_score']})"}
        )

    # 2. Ambil referensi dari web
    references = []
    try:
        references = search_web(prompt, max_results=3)
    except Exception:
        pass  # tidak ganggu alur utama

    # --- JALUR TESTING TANPA API KEY ---
    if not GEMINI_API_KEY:
        return {
            "response": f"👋 Halo Master! Koneksi aman.\n\nBackend lu berhasil jalan terpisah di Render!\nLu input: '{prompt}'\n\nSistem mendeteksi GEMINI_API_KEY belum diisi. Pasang key-nya di Render biar Gemini 1.5 Flash aktif!",
            "references": references
        }

    # 3. Bangun konteks untuk prompt Gemini
    if references:
        ref_texts = []
        for i, ref in enumerate(references, 1):
            ref_texts.append(f"{i}. Judul: {ref['title']}\n   Link: {ref['link']}\n   Cuplikan: {ref['snippet']}")
        context_block = "Referensi dari web (gunakan sebagai sumber jika relevan):\n" + "\n".join(ref_texts)
    else:
        context_block = "Tidak ada referensi web tambahan untuk pertanyaan ini."

    # 4. Prompt system + user
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

    full_prompt = f"{system_instruction}\n\nPertanyaan Pengguna: {prompt}\n\n{context_block}\n\nJawaban:"

    # 5. Panggil Gemini
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
            "references": references
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
