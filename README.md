# ATHENA — Document-Grounded Learning System

ATHENA is a Retrieval-Augmented Generation (RAG) system that enables users to learn directly from their own documents.
It supports PDF ingestion, semantic search, context-grounded answers, and a persistent notes system.

---

## Overview

ATHENA transforms static documents into an interactive learning system.

Instead of generating generic responses, it:

* Retrieves relevant content from uploaded PDFs
* Generates answers strictly grounded in source material
* Tracks sources at the page level
* Allows users to create and manage structured notes

---

## Problem

Most AI tools:

* Provide generic, non-contextual answers
* Do not retain user-specific knowledge
* Lack support for structured revision

ATHENA addresses this by combining **retrieval, grounding, and persistence** into a single system.

---

## System Architecture

```text
PDF Upload
   ↓
Text Extraction (page-wise + OCR fallback)
   ↓
Chunking (overlapping segments with page metadata)
   ↓
Embedding (OpenAI)
   ↓
FAISS Index (persistent storage)
   ↓
Query → Retrieval (top-k chunks)
   ↓
LLM (context-grounded generation)
   ↓
Answer + Page-Level Sources
   ↓
Notes System (SQLite)
```

---

## Core Features

### 1. Document-Grounded Q&A

* Answers are generated **only from retrieved document context**
* Reduces hallucination by enforcing strict grounding

---

### 2. Persistent Vector Index

* FAISS index stored on disk
* Enables reuse across sessions without reprocessing

---

### 3. Page-Level Source Tracking

* Each answer includes references mapped to document pages
* Improves transparency and traceability

---

### 4. Notes System (Persistent)

* Create notes from AI-generated answers
* Append to existing notes
* Stored in SQLite with timestamps

---

### 5. PDF Export

* Notes can be exported as structured PDFs
* Includes content, sources, and metadata

---

### 6. Background Processing

* Large PDFs indexed asynchronously
* Prevents blocking API requests

---

### 7. OCR Fallback

* Supports scanned PDFs using Tesseract OCR
* Ensures robustness for real-world documents

---

## Tech Stack

**Backend**

* FastAPI
* FAISS (vector search)
* OpenAI Embeddings + LLM
* SQLite (notes storage)

**Frontend**

* Streamlit

**Document Processing**

* pdfplumber
* pytesseract

---

## Key Engineering Decisions

### 1. Retrieval-Augmented Generation (RAG)

Chosen over fine-tuning to:

* Avoid retraining costs
* Support dynamic document updates
* Ensure answers remain grounded in source material

---

### 2. Page-Aware Chunking

Chunks retain page metadata to:

* Enable accurate citations
* Improve user trust in responses

---

### 3. Persistent Indexing

FAISS index stored locally to:

* Avoid recomputation
* Improve performance across sessions

---

### 4. Failure Handling

* Embedding failures are logged
* Unprocessed data stored for retry
* Prevents silent system failure

---

## Limitations

* Single-user FAISS index (no user isolation)
* No rate limiting or request throttling
* Embedding latency for large documents
* Limited scalability without distributed vector storage

---

## Future Improvements

* Multi-user architecture with isolated vector stores
* Replace FAISS with scalable vector DB (Pinecone / Weaviate)
* Add rate limiting and caching
* Introduce background workers (Celery / Redis)
* Improve answer evaluation and ranking

---

## How to Run

### 1. Set API Key

```bash
setx OPENAI_API_KEY "your_api_key_here"
```

### 2. Start Backend

```bash
python -m uvicorn upload_ingest_faiss:app --reload
```

### 3. Start UI

```bash
streamlit run streamlit_app.py
```

---

## Example Output

```json
{
  "answer": "Concept explained using document context...",
  "sources": [
    {
      "source": "OperatingSystems.pdf",
      "pages": [12, 13]
    }
  ]
}
```

---

## Summary

ATHENA is a **document-first AI system** that combines:

* Retrieval-based reasoning
* Context-grounded generation
* Persistent knowledge storage

It demonstrates practical system design beyond basic LLM usage, focusing on **reliability, traceability, and user-centric learning**.
