import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

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

# BENAR: baca dari env, jangan hardcode key
GEMINI_API_KEY = os.getenv("AIzaSyB6wjrMBXNyXFg8AkT_JUsFGqpJPWNhT9M")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-1.5-flash'

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    try:
        with open("fronted.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>UI file not found</h1>", status_code=500)

@app.post("/v1/chat")
async def chat_endpoint(req: ChatRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt kosong")

    # System prompt (sudah kamu edit sesuai kebutuhan)
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
        return {"response": ai_answer, "references": []}
    except Exception as e:
        print(f"Gemini API error: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": "AI error", "error": str(e)})
