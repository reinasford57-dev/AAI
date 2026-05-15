import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- KONFIGURASI FASTAPI ---
app = FastAPI(
    title="Research & Modding AI Assistant",
    description="Backend + Frontend terintegrasi untuk Hugging Face Spaces",
    version="1.0.0"
)

# Aktifkan CORS agar aman saat testing lokal maupun production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_origins_regex=".*",
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


# --- KODE FRONTEND (HTML DARI BLACKBOX) ---
# Gua tanam langsung di sini pakai HTMLResponse biar lu gak perlu ribet manage folder static di Hugging Face
HTML_FRONTEND = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>⚡ Research & Modding AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace;
            height: 100vh; display: flex; flex-direction: column; max-width: 800px;
            margin: 0 auto; border: 1px solid #1f1f1f; border-radius: 8px;
            overflow: hidden; box-shadow: 0 0 20px rgba(0, 255, 65, 0.1);
        }
        .header {
            background: #111; padding: 12px 16px; display: flex;
            align-items: center; justify-content: space-between;
            border-bottom: 1px solid #1f1f1f; flex-shrink: 0;
        }
        .header .title { font-size: 1.1rem; color: #00ff41; text-shadow: 0 0 8px rgba(0,255,65,0.6); letter-spacing: 1px; }
        .status { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #aaa; }
        .status-dot { width: 8px; height: 8px; background: #00ff41; border-radius: 50%; box-shadow: 0 0 8px #00ff41; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }
        .chat-container {
            flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column;
            gap: 12px; background: #0d0d0d; scroll-behavior: smooth; -webkit-overflow-scrolling: touch; overscroll-behavior: contain;
        }
        .bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; word-wrap: break-word; animation: fadeIn 0.2s ease; white-space: pre-wrap; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .user { align-self: flex-end; background: #1f3a1f; border: 1px solid #00ff41; color: #e0ffe0; box-shadow: 0 0 12px rgba(0,255,65,0.2); }
        .bot { align-self: flex-start; background: #1a1a1a; border: 1px solid #333; color: #d0d0d0; }
        .bot strong, .bot b { color: #00ff41 !important; font-weight: bold; text-shadow: 0 0 3px rgba(0,255,65,0.5); }
        .bot .references { margin-top: 10px; padding-top: 8px; border-top: 1px solid #333; font-size: 0.75rem; color: #aaa; }
        .references a { color: #00ffff; text-decoration: none; display: block; margin-bottom: 3px; word-break: break-all; line-height: 1.3; }
        .references a:hover { text-decoration: underline; text-shadow: 0 0 5px cyan; }
        .error-bubble { align-self: center; background: #300; border: 1px solid #ff3131; color: #ff8888; box-shadow: 0 0 18px rgba(255,49,49,0.5); text-align: center; white-space: pre-wrap; }
        .input-area { background: #111; padding: 12px 16px; border-top: 1px solid #1f1f1f; display: flex; gap: 8px; flex-shrink: 0; position: sticky; bottom: 0; padding-bottom: env(safe-area-inset-bottom); transition: padding 0.3s ease; }
        #promptInput { flex: 1; background: #1a1a1a; border: 1px solid #333; border-radius: 20px; padding: 10px 16px; color: #e0e0e0; font-family: inherit; font-size: 0.95rem; outline: none; transition: border 0.2s, box-shadow 0.2s; resize: none; }
        #promptInput:focus { border-color: #00ff41; box-shadow: 0 0 10px rgba(0,255,65,0.2); }
        #sendBtn { background: #00ff41; border: none; border-radius: 50%; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #0a0a0a; font-size: 1.4rem; font-weight: bold; transition: background 0.2s, box-shadow 0.2s; flex-shrink: 0; touch-action: manipulation; }
        #sendBtn:hover, #sendBtn:active { background: #00e639; box-shadow: 0 0 15px #00ff41; }
        #sendBtn:disabled { background: #555; color: #222; cursor: not-allowed; box-shadow: none; }
        .chat-container::-webkit-scrollbar { width: 5px; }
        .chat-container::-webkit-scrollbar-track { background: #0a0a0a; }
        .chat-container::-webkit-scrollbar-thumb { background: #00ff41; border-radius: 10px; }
        .loading-dots { display: inline-flex; gap: 4px; }
        .loading-dots span { width: 6px; height: 6px; background: #00ff41; border-radius: 50%; animation: loading 1.4s infinite ease-in-out both; }
        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes loading { 0%, 80%, 100% { transform: scale(0); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }
    </style>
</head>
<body>
    <div class="header">
        <span class="title">⚡ Research & Modding AI</span>
        <div class="status">
            <span class="status-dot"></span>
            <span id="statusText">Ready</span>
        </div>
    </div>
    <div class="chat-container" id="chatBox">
        <div class="bubble bot" style="align-self: center; font-size: 0.85rem; opacity: 0.7;">
            Selamat datang! Tanyakan apa saja tentang research & modding.
        </div>
    </div>
    <div class="input-area">
        <input type="text" id="promptInput" placeholder="Enter your research prompt..." autocomplete="off" maxlength="2000" />
        <button id="sendBtn" title="Send">➤</button>
    </div>
    <script>
        (function() {
            const API_URL = '/v1/chat';
            const chatBox = document.getElementById('chatBox');
            const promptInput = document.getElementById('promptInput');
            const sendBtn = document.getElementById('sendBtn');
            const statusText = document.getElementById('statusText');

            function renderMarkdownSafe(text) {
                let safe = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
                safe = safe.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                safe = safe.replace(/\\n/g, '<br>');
                return safe;
            }

            function addBubble(role, content, rag_context = null, isError = false) {
                const div = document.createElement('div');
                div.className = `bubble ${role}`;
                if (isError) div.classList.add('error-bubble');
                let html = renderMarkdownSafe(content);
                if (rag_context && Array.isArray(rag_context) && rag_context.length > 0) {
                    html += '<div class="references">📚 <strong>RAG Context:</strong>';
                    rag_context.forEach(ctx => {
                        const title = (ctx.title || 'Source').substring(0, 80) + '...';
                        const link = ctx.link || '#';
                        html += `<a href="${link}" target="_blank" rel="noopener noreferrer">${title}</a>`;
                    });
                    html += '</div>';
                }
                div.innerHTML = html;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
                return div;
            }

            function setStatus(status, dotColor = '#00ff41') {
                statusText.textContent = status;
                document.querySelector('.status-dot').style.background = dotColor;
            }

            async function sendMessage() {
                const prompt = promptInput.value.trim();
                if (!prompt) return;

                addBubble('user', prompt);
                promptInput.value = '';
                sendBtn.disabled = true;
                promptInput.disabled = true;
                setStatus('AI Thinking...', '#ffff00');
                const loadingBubble = addBubble('bot', '⏳ Processing with multi-LLM...');
                
                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    
                    loadingBubble.remove();
                    
                    if (!response.ok) {
                        if (response.status === 403) {
                            const errorData = await response.json();
                            addBubble('bot', `🚫 ${errorData.detail || 'High risk blocked'}`, null, true);
                            setStatus('Blocked', '#ff3131');
                        } else {
                            throw new Error(`Server error: ${response.status}`);
                        }
                    } else {
                        const data = await response.json();
                        const aiResponse = data.ai_response || 'No AI response.';
                        const ragContext = data.rag_context || [];
                        addBubble('bot', aiResponse, ragContext);
                        setStatus('Ready', '#00ff41');
                    }
                } catch (error) {
                    loadingBubble.remove();
                    addBubble('bot', `⚠️ Network error: ${error.message}`, null, true);
                    setStatus('Error', '#ff3131');
                } finally {
                    sendBtn.disabled = false;
                    promptInput.disabled = false;
                    promptInput.focus();
                }
            }

            sendBtn.addEventListener('click', sendMessage);
            promptInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
            });
            promptInput.addEventListener('focus', () => {
                setTimeout(() => chatBox.scrollTop = chatBox.scrollHeight, 100);
            });
            promptInput.focus();
        })();
    </script>
</body>
</html>
"""

# --- ENDPOINTS ---

# 1. Endpoint Utama: Menampilkan UI Cyberpunk
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return HTMLResponse(content=HTML_FRONTEND, status_code=200)

# 2. Endpoint API: Proses Chat (Sudah disinkronkan dengan variabel Frontend baru)
@app.post("/v1/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    user_prompt = request.prompt.lower()
    
    # --- SIMULASI SISTEM RISK ASSESSMENT & BLOCK FILTER ---
    # Jika mendeteksi kata yang melanggar hukum berat/bahaya nyata
    if "bikin bom" in user_prompt or "hack bank" in user_prompt:
        raise HTTPException(
            status_code=403, 
            detail="PROMPT DIBLOKIR: Risiko tinggi terdeteksi oleh sistem keamanan."
        )
        
    # --- SIMULASI RESPONS AI & DATA REFERENSI (RAG) ---
    # Di sinilah logika multi-LLM (DeepSeek/Gemini) & Web Search lu ditaruh nanti
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
        "ai_response": simulated_ai_reply, # <--- COCOK DENGAN FRONTEND
        "rag_context": simulated_rag       # <--- COCOK DENGAN FRONTEND
    }

if __name__ == "__main__":
    import uvicorn
    # Jalankan lokal untuk test: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)