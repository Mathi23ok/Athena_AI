# rag_chat.py
import os
import sqlite3
from typing import List, Tuple, Optional

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema import Document

FAISS_DIR = "./faiss_store"
NOTES_DB = "notes.db"

# ======================================================
# Notes database (supports NEW + APPEND)
# ======================================================

def init_notes_db():
    conn = sqlite3.connect(NOTES_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            sources TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def create_note(title: str, content: str, sources: str):
    conn = sqlite3.connect(NOTES_DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes(title, content, sources) VALUES (?, ?, ?)",
        (title, content, sources)
    )
    conn.commit()
    conn.close()

def append_to_note(note_id: int, new_content: str, new_sources: str):
    conn = sqlite3.connect(NOTES_DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT content, sources FROM notes WHERE id = ?",
        (note_id,)
    )
    old_content, old_sources = cur.fetchone()

    updated_content = old_content + "\n\n---\n\n" + new_content
    updated_sources = old_sources + ", " + new_sources

    cur.execute("""
        UPDATE notes
        SET content = ?, sources = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (updated_content, updated_sources, note_id))

    conn.commit()
    conn.close()

def list_notes():
    conn = sqlite3.connect(NOTES_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, content, sources, created_at, updated_at
        FROM notes
        ORDER BY updated_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

init_notes_db()

# ======================================================
# Load FAISS retriever
# ======================================================

def load_retriever():
    if not os.path.isdir(FAISS_DIR):
        return None

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    db = FAISS.load_local(
        FAISS_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}
    )

# ======================================================
# Core RAG Answer Logic (REAL RAG)
# ======================================================

def answer_question(
    question: str,
    chat_history: Optional[List[Tuple[str, str]]] = None
):
    retriever = load_retriever()
    if retriever is None:
        return "No documents indexed yet.", []

    # 1. Retrieve
    docs: List[Document] = retriever.get_relevant_documents(question)

    if not docs:
        return "No relevant information found in the documents.", []

    # 2. Filter & build context
    context_chunks = []
    sources = []

    for d in docs:
        text = d.page_content.strip()
        if len(text) < 80:
            continue

        context_chunks.append(text)
        sources.append({
            "source": d.metadata.get("source", "unknown"),
            "chunk": d.metadata.get("chunk", ""),
            "snippet": text[:300]
        })

    if not context_chunks:
        return "Not enough meaningful context to answer.", []

    context_text = "\n\n---\n\n".join(context_chunks)

    # 3. Prompt engineering (THIS is resume-worthy)
    prompt = f"""
You are an expert tutor.

Answer the user's question using ONLY the information in the context.
Explain in clear, natural language in simple terms with examples if possible.
give a concise, accurate answer.be kind and effective.
Do NOT copy sentences.
If the answer is missing, say so clearly.

Context:
{context_text}

Question:
{question}

Answer:
"""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.25
    )

    response = llm.invoke(prompt)
    answer = response.content.strip()

    return answer, sources
