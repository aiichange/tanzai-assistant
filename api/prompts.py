from typing import Dict

SYSTEM_DEFAULT = """You are a helpful AI assistant.
Follow tools' results if provided. Use concise, structured answers.
"""

TEMPLATES: Dict[str, str] = {
    "explain_topic": "Explain the topic '{topic}' in exactly {bullets} bullet points.",
    "summarize": "Summarize the following text in 5 bullets:\n\n{text}",
    "qa": "Use the context below to answer the question.\nContext:\n{context}\n\nQuestion: {question}\nAnswer:",
}
