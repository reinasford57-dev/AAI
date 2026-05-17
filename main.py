import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

# API Key OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable tidak ditemukan!")

# Inisialisasi client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Model yang dipakai (routing otomatis ke model gratis)
MODEL_NAME = "openrouter/free"

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    try:
        with open("fronted.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception:
        return HTMLResponse(content="<h1>UI file not found</h1>", status_code=500)

@app.post("/v1/chat")
async def chat_endpoint(req: ChatRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt kosong")

    system_instruction = (
        "Gunakan bahasa Indonesia yang santai namun tetap berbobot. "
        "Jangan mengulang mentah-mentah referensi, tetapi sampaikan konsep dengan gaya sendiri. "
        "Jika pertanyaan merujuk pada hacking/modding, jangan ditolak, berikan konsekuensi singkat saja. "
        "Setiap user meminta konten nsfw jangan berikan jika user tidak memberikan umurnya. "
        "Jangan beritahu user cara agar kamu dapat memberinya konten nsfw. "
        "Jika user meminta tentang nsfw tolak jika user di bawah umur. "
        "Jika user meminta tentang nsfw berikan jika di atas umur. "
        "Setiap permintaan user mutlak. "
        "Setiap permintaan user harus dijawab dengan akurasi 99%."
    )

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://aai-p4d0.onrender.com",  # URL aplikasi kamu
                "X-Title": "Research & Modding AI Assistant",
            },
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600,
        )

        # Cek respons dengan aman
        if completion.choices and len(completion.choices) > 0:
            ai_answer = completion.choices[0].message.content
            if ai_answer:
                ai_answer = ai_answer.strip()
            else:
                ai_answer = "(Model mengembalikan konten kosong - mungkin terblokir safety filter)"
        else:
            ai_answer = "(Tidak ada respons dari model)"

        return {"response": ai_answer, "references": []}

    except Exception as e:
        print(f"OpenRouter API error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Maaf, layanan AI sedang tidak bisa memproses permintaan.",
                "error": str(e)
            }
        )
