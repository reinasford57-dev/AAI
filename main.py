import os
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai

from app.core.analyzer import risk_classifier
from app.services.search import search_web

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

# Konfigurasi Gemini API key
GEMINI_API_KEY = os.getenv("AIzaSyB6wjrMBXNyXFg8AkT_JUsFGqpJPWNhT9M")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")
genai.configure(api_key=GEMINI_API_KEY)

# Gunakan model yang ringan dan gratis tier friendly
MODEL_NAME = 'gemini-1.5-flash'  # 1.5 Flash cepat, murah, context 1M token

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
        "Kamu adalah asisten riset teknologi dan keamanan siber yang informatif dan akurat. "
        "Jawablah pertanyaan pengguna dengan penjelasan yang mendalam, dan natural. "
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

    full_prompt = (
        f"{system_instruction}\n\n"
        f"Pertanyaan Pengguna: {prompt}\n\n"
        f"{context_block}\n\n"
        "Jawaban:"
    )

    # 5. Panggil Gemini
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=600,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )

        ai_answer = response.text.strip()

        # Bersihkan jika ada artefak aneh (jarang terjadi di Gemini)
        ai_answer = ai_answer.replace("\\n", "\n")  # jaga-jaga

        return {
            "response": ai_answer,
            "references": references
        }

    except Exception as e:
        # Jika error, log lengkap dan kirim pesan error yang jelas
        print(f"Gemini API error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Maaf, layanan AI sedang tidak bisa memproses permintaan. Silakan coba lagi.",
                "error": str(e)
            }
    )
