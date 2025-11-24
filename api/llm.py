import os, httpx
import torch  # ✅ NEW: for GPU detection
from transformers import pipeline, set_seed, AutoModelForCausalLM, AutoTokenizer

# ---------- Config ----------
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
HF_MODEL = os.getenv("HF_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Allow .env toggle, default true
USE_OLLAMA_ENV = os.getenv("USE_OLLAMA", "true").lower() == "true"

# Cache multiple HF pipelines by model
_hf_pipes = {}


# ---------- Helpers ----------
def ollama_available() -> bool:
    """Check if Ollama server is up and reachable."""
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def use_ollama() -> bool:
    """Decide whether to use Ollama or HF pipeline."""
    return USE_OLLAMA_ENV and ollama_available()


def _hf(model_name: str = HF_MODEL):
    """Lazy-load Hugging Face pipeline with caching (downloads from HF Hub)."""
    if model_name in _hf_pipes:
        return _hf_pipes[model_name]

    # Download tokenizer & model from Hugging Face Hub
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # ✅ Use GPU if available, otherwise CPU
    device = 0 if torch.cuda.is_available() else -1
    print(f"Device set to use {'cuda:0' if device == 0 else 'cpu'}")

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,  # ✅ now respects GPU/CPU
    )
    set_seed(42)
    _hf_pipes[model_name] = pipe
    return pipe


# ---------- Chat APIs ----------
async def chat_ollama(messages, model="llama3.1:8b-instruct-q4_K_M", stream=False):
    """Send messages to Ollama if available."""
    async with httpx.AsyncClient(timeout=120) as client:
        payload = {"model": model, "messages": messages, "stream": stream}
        r = await client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")


def chat_hf(prompt: str, model: str = HF_MODEL, max_new_tokens=256):
    """Fallback to Hugging Face model (HF_MODEL from env by default)."""
    pipe = _hf(model)
    out = pipe(
        prompt,
        num_return_sequences=1,
        max_new_tokens=max_new_tokens  # ✅ only this
        # no truncation here
    )
    return out[0]["generated_text"]


# ---------- Global Switch ----------
USE_OLLAMA = use_ollama()
print(f"[LLM] USE_OLLAMA = {USE_OLLAMA}, HF_MODEL = {HF_MODEL}, OLLAMA_BASE = {OLLAMA_BASE}")
