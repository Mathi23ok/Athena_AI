# upload_ingest_faiss.py
import os
import hashlib
import tempfile
import json
import time
from typing import Generator, Dict, List

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# -----------------------
# Config & globals
# -----------------------
UPLOAD_DIR = "./uploads"
FAISS_DIR = "./faiss_store"
PENDING_DIR = "./faiss_store/pending"
LOG_FILE = "indexing_errors.log"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

MAX_BYTES = 200 * 1024 * 1024  # 200 MB upload limit
CHUNK_SIZE = 1200
OVERLAP = 200

app = FastAPI()

# -----------------------
# Utilities
# -----------------------
def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_text_page_by_page(pdf_path: str):
    """
    Yield (page_number, text) for each page.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            yield i + 1, (text or "")


def ocr_pdf(pdf_path: str) -> Generator[str, None, None]:
    images = convert_from_path(pdf_path, dpi=200)
    for img in images:
        text = pytesseract.image_to_string(img)
        yield text or ""

def chunks_from_pages(pages, chunk_size=1200, overlap=200):
    buffer = ""
    buffer_pages = set()

    for page_num, page_text in pages:
        buffer += "\n" + page_text
        buffer_pages.add(page_num)

        while len(buffer) >= chunk_size:
            yield {
                "text": buffer[:chunk_size].strip(),
                "pages": sorted(buffer_pages)
            }
            buffer = buffer[chunk_size - overlap:]
            buffer_pages = set()

    if buffer.strip():
        yield {
            "text": buffer.strip(),
            "pages": sorted(buffer_pages)
        }


def init_embedder():
    
    # Initialize OpenAI embedder if key is set
    if OpenAIEmbeddings is not None and os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    return None

def log_error(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        lf.write(f"{time.ctime()}: {msg}\n")

# -----------------------
# Core processing (indexing)
# -----------------------
def process_and_index_faiss(pdf_path: str, original_filename: str, file_hash: str) -> Dict:
    """
    Extract text, chunk, embed, and index into FAISS using LangChain.
    Saves FAISS index to disk for later loading.
    If embeddings fail (no key or quota), persist chunks to pending JSON for later processing.
    """

    # 1️⃣ Extract pages with page numbers
    pages_gen = extract_text_page_by_page(pdf_path)

    # 2️⃣ Chunk with page tracking
    chunk_objs = list(chunks_from_pages(pages_gen))

    if not chunk_objs:
        raise RuntimeError("No chunks extracted from PDF; check the PDF content / OCR.")

    # 3️⃣ Separate text + metadata
    texts = [c["text"] for c in chunk_objs]

    metadatas = [
        {
            "source": original_filename,
            "pages": c["pages"]
        }
        for c in chunk_objs
    ]

    # 4️⃣ Initialize embedder
    embedder = init_embedder()

    if embedder is None:
        pending_path = os.path.join(PENDING_DIR, f"pending_{file_hash}.json")
        with open(pending_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "filename": original_filename,
                    "file_hash": file_hash,
                    "chunks": texts,
                    "metadatas": metadatas
                },
                fh,
                ensure_ascii=False
            )
        log_error(f"No embedding key found; saved pending chunks to {pending_path}")
        return {
            "status": "pending_embeddings",
            "pending_file": pending_path,
            "chunks": len(texts)
        }

    # 5️⃣ Build FAISS
    try:
        faiss_store = FAISS.from_texts(
            texts=texts,
            embedding=embedder,
            metadatas=metadatas
        )
        faiss_store.save_local(FAISS_DIR)

        return {
            "status": "indexed",
            "chunks": len(texts),
            "faiss_dir": FAISS_DIR
        }

    except Exception as e:
        err = str(e)
        pending_path = os.path.join(PENDING_DIR, f"pending_{file_hash}.json")
        with open(pending_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "filename": original_filename,
                    "file_hash": file_hash,
                    "chunks": texts,
                    "metadatas": metadatas
                },
                fh,
                ensure_ascii=False
            )
        log_error(f"Embedding/indexing error: {err}")
        return {
            "status": "pending_embeddings",
            "reason": err,
            "pending_file": pending_path,
            "chunks": len(texts)
        }

# -----------------------
# API endpoint
# -----------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), background: BackgroundTasks = None):
    fname = file.filename
    if not fname.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir=UPLOAD_DIR)
    os.close(temp_fd)
    size = 0
    try:
        with open(temp_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    out.close()
                    os.remove(temp_path)
                    raise HTTPException(status_code=413, detail="File too large.")
                out.write(chunk)

        file_hash = sha256_of_file(temp_path)

        if background:
            background.add_task(process_and_index_faiss, temp_path, fname, file_hash)
            return {"status": "uploaded", "hash": file_hash, "message": "Indexing started in background."}
        else:
            result = process_and_index_faiss(temp_path, fname, file_hash)
            return result

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
