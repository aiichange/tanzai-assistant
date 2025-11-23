import os, uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from .prompts import SYSTEM_DEFAULT, TEMPLATES
from .deps import get_mongo, now, HF_MODEL   # ✅ import HF_MODEL too
from .rag import ingest_pdf, query_rag
from .websearch import web_search
from .sandbox import run_python
from .llm import chat_ollama, chat_hf, USE_OLLAMA

load_dotenv()
app = FastAPI(title="AI Platform API")

# ---------- Schemas ----------
class Message(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None   # "ollama/llama3.1:8b" or "hf/zephyr-7b-alpha"
    use_rag: bool = False
    use_web: bool = False

# ---------- Root ----------
@app.get("/")
def root():
    return {"message": "Welcome to AI Platform API 🚀"}

# ---------- Health ----------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- Tools ----------
@app.post("/tools/file_search/ingest")
async def tool_ingest(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    path = f"/tmp/{file_id}_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    stats = ingest_pdf(path, file_id)
    return {"ok": True, **stats}

@app.post("/tools/file_search/query")
def tool_query(q: str = Form(...), k: int = Form(4)):
    return {"ok": True, "hits": query_rag(q, k)}

@app.post("/tools/web_search")
def tool_web(q: str = Form(...), k: int = Form(5)):
    return {"ok": True, "results": web_search(q, max_results=k)}

@app.post("/tools/code_interpreter")
def tool_code(code: str = Form(...)):
    return {"ok": True, "result": run_python(code)}

# ---------- Chat ----------
@app.post("/chat")
async def chat(req: ChatRequest):
    mongo = get_mongo()

    # Tool augmentation (RAG / Web search)
    augmented = req.messages[:]
    if req.use_rag:
        q = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        ctx = query_rag(q, 4)
        ctx_text = "\n\n".join([f"[p{c['meta']['page']}] {c['text']}" for c in ctx])
        augmented = [Message(role="system", content=SYSTEM_DEFAULT)] + augmented + [
            Message(role="tool", content=f"RAG Context:\n{ctx_text}")
        ]
    if req.use_web:
        q = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        hits = web_search(q, 5)
        web_text = "\n".join([f"- {h['title']} :: {h['href']}" for h in hits])
        augmented = [Message(role="system", content=SYSTEM_DEFAULT)] + augmented + [
            Message(role="tool", content=f"Web Results:\n{web_text}")
        ]

    # ---------- Decide backend ----------
    content = ""
    try:
        if USE_OLLAMA:
            # Try Ollama first
            content = await chat_ollama([m.model_dump() for m in augmented])
        else:
            raise RuntimeError("Ollama disabled or unavailable")
    except Exception as e:
        # Fallback to Hugging Face (local Zephyr by default)
        print(f"[Chat] Ollama failed → falling back to HF: {e}")
        sys = next((m.content for m in augmented if m.role == "system"), SYSTEM_DEFAULT)
        user = next((m.content for m in reversed(augmented) if m.role == "user"), "")
        tools = "\n".join([m.content for m in augmented if m.role == "tool"])

        prompt = f"""{sys}

Conversation so far:
{tools}

User: {user}
Assistant:"""

        # ✅ Use local Zephyr model from .env / deps
        model = req.model or HF_MODEL
        content = chat_hf(prompt, model=model)

    # ---------- Log to Mongo ----------
    mongo.messages.insert_one({
        "conversation_id": "demo",
        "ts": now(),
        "request": [m.model_dump() for m in req.messages],
        "response": content
    })

    return {"ok": True, "answer": content}
