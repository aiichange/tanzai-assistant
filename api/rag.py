import os, uuid
from typing import List
from pypdf import PdfReader
from .deps import get_chroma, get_embedder

COLLECTION = "docs_default"

def _chunk_text(text: str, chunk=900, overlap=150) -> List[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+chunk])
        i += (chunk - overlap)
    return out

def ingest_pdf(path: str, file_id: str):
    reader = PdfReader(path)
    pages_text = [p.extract_text() or "" for p in reader.pages]
    chunks, metadatas, ids = [], [], []

    for page_idx, page in enumerate(pages_text):
        for ci, chunk in enumerate(_chunk_text(page)):
            cid = f"{file_id}-{page_idx}-{ci}"
            chunks.append(chunk)
            metadatas.append({"file_id": file_id, "page": page_idx})
            ids.append(cid)

    chroma = get_chroma()
    coll = chroma.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    embedder = get_embedder()
    vectors = embedder.encode(chunks, normalize_embeddings=True).tolist()
    coll.add(documents=chunks, metadatas=metadatas, ids=ids, embeddings=vectors)
    return {"file_id": file_id, "chunks": len(chunks)}

def query_rag(q: str, k: int = 4):
    chroma = get_chroma()
    coll = chroma.get_or_create_collection(COLLECTION)
    embedder = get_embedder()
    qv = embedder.encode([q], normalize_embeddings=True).tolist()
    res = coll.query(query_embeddings=qv, n_results=k)
    docs = [
        {"text": d, "meta": m}
        for d, m in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0])
    ]
    return docs
