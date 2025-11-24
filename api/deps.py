import os, time
from dotenv import load_dotenv
from pymongo import MongoClient
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "ai_platform")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma")

# Local Hugging Face model path (fallback if not in .env)
HF_MODEL = os.getenv("HF_MODEL", r"C:/Users/er_si/models/zephyr-7b-alpha")

# Caches
_embed_model_cache = None
_chroma_client_cache = None
_mongo_cache = None
_llm_model_cache = None
_llm_tokenizer_cache = None


def get_mongo():
    """Return cached MongoDB connection."""
    global _mongo_cache
    # ✅ Avoid truthiness on Database object; compare explicitly to None
    if _mongo_cache is not None:
        return _mongo_cache

    _mongo_cache = MongoClient(MONGODB_URI)[MONGO_DB]
    return _mongo_cache


def get_embedder():
    """Return cached SentenceTransformer embedder."""
    global _embed_model_cache
    if _embed_model_cache is not None:
        return _embed_model_cache

    _embed_model_cache = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embed_model_cache


def get_chroma():
    """Return cached ChromaDB client."""
    global _chroma_client_cache
    if _chroma_client_cache is not None:
        return _chroma_client_cache

    _chroma_client_cache = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client_cache


def get_llm():
    """
    Return cached Hugging Face LLM + tokenizer.
    Forces local-only load to prevent re-downloading.
    """
    global _llm_model_cache, _llm_tokenizer_cache
    if _llm_model_cache is not None and _llm_tokenizer_cache is not None:
        return _llm_model_cache, _llm_tokenizer_cache

    print(f"[LLM] Loading local model from: {HF_MODEL}")

    # ✅ Explicitly load tokenizer + model locally
    _llm_tokenizer_cache = AutoTokenizer.from_pretrained(HF_MODEL, local_files_only=True)
    _llm_model_cache = AutoModelForCausalLM.from_pretrained(HF_MODEL, local_files_only=True)

    return _llm_model_cache, _llm_tokenizer_cache


def now() -> float:
    """Return current timestamp."""
    return time.time()
