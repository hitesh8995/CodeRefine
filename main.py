import os
import sys
import json
import asyncio
import uvicorn
import subprocess
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key or "gsk_placeholder")

app = FastAPI(title="CodeRefine X Ultimate")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class RequestModel(BaseModel):
    code: str
    language: str
    mode: str = "standard"

class AnalysisResponse(BaseModel):
    summary: str
    quality_score: dict
    issues: List[dict]
    rewritten_code: str
    dry_run: str
    teacher_tips: List[str]

# --- AI ENGINE ---
def get_ai_analysis(code, language, mode):
    prompt = (
        f"Analyze this {language} code. Mode: {mode}. "
        "Return strictly valid JSON. Double quotes only. "
        "Structure: {"
        "\"summary\": \"Brief overview\", "
        "\"quality_score\": {\"maintainability\": 0-100, \"security\": 0-100, \"overall\": 0-100}, "
        "\"issues\": [{\"severity\": \"Critical|High|Medium|Low\", \"line\": 1, \"type\": \"Bug|Security\", \"message\": \"Short description\", \"fix\": \"Hint for teaching mode\"}], "
        "\"rewritten_code\": \"Optimized code. Use \\n for newlines.\", "
        "\"dry_run\": \"Step-by-step logic explanation. Use \\n for newlines.\", "
        "\"teacher_tips\": [\"Concept 1\", \"Concept 2\"]"
        "}"
    )
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a code compiler. Return raw JSON."}, {"role": "user", "content": f"{prompt}\n\n{code}"}],
            model="llama-3.3-70b-versatile", temperature=0.1, response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"summary": f"Error: {e}", "issues": [], "rewritten_code": code, "dry_run": "AI unavailable.", "teacher_tips": [], "quality_score": {"overall": 0}}

# --- ENDPOINTS ---

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: RequestModel):
    return get_ai_analysis(req.code, req.language, req.mode)

# --- WEBSOCKET EXECUTION (THE FIX) ---
@app.websocket("/ws/execute")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    process = None
    
    try:
        # 1. Receive Code
        data = await websocket.receive_json()
        code = data.get("code", "")
        language = data.get("language", "python")

        # 2. Setup Temp File
        filename = "temp_script.js" if language.lower() == "javascript" else "temp_script.py"
        run_cmd = ["node", filename] if language.lower() == "javascript" else [sys.executable, "-u", filename] # -u for unbuffered python
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        # 3. Start Process
        process = subprocess.Popen(
            run_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0 # Unbuffered I/O
        )

        # 4. Async Readers
        async def read_stream(stream, channel):
            while True:
                output = await asyncio.to_thread(stream.read, 1) # Read char-by-char for real-time feel
                if not output: break
                await websocket.send_json({"type": channel, "data": output})

        # 5. Async Writer (Input)
        async def input_loop():
            while True:
                try:
                    user_input = await websocket.receive_text()
                    if process.poll() is not None: break
                    process.stdin.write(user_input + "\n")
                    process.stdin.flush()
                except: break

        await asyncio.gather(
            read_stream(process.stdout, "stdout"),
            read_stream(process.stderr, "stderr"),
            input_loop()
        )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "stderr", "data": f"Error: {str(e)}"})
    finally:
        if process: process.kill()
        try: os.remove(filename) 
        except: pass

# --- SERVE FRONTEND ---
@app.get("/")
async def serve_spa():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)