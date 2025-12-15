# Athena_AI
ATHENA is a RAG-based PDF learning assistant that lets users upload documents, ask questions, and receive clear explanations grounded only in the source content. It supports page-level citations, note creation, note appending, and PDF export through an interactive Streamlit UI.

✨ Key Features

📤 Upload PDFs via API or UI
🔍 Semantic search using FAISS
🧠 Context-aware answers powered by OpenAI LLMs
📝 Create & append notes from AI-generated answers
📚 View saved notes with source references
📄 Export notes as PDF
🧾 Page-level source tracking (not raw chunks)

🧠 How It Works (RAG Pipeline)

PDF Ingestion
Extracts text page-wise (OCR fallback supported)
Splits text into overlapping chunks
Stores embeddings in FAISS with metadata (source, pages)

Retrieval
User question → vector search in FAISS
Top relevant chunks retrieved

Generation
LLM answers using only retrieved context
No hallucination, no copy-paste
Notes System
Save answers as new notes
Append answers to existing notes
Persisted using SQLite

🛠 Tech Stack

Frontend: Streamlit
Backend: FastAPI
Vector Store: FAISS
Embeddings: OpenAI (text-embedding-3-small)
LLM: OpenAI Chat Models
Database: SQLite (notes storage)
PDF Processing: pdfplumber, pytesseract
Language: Python

📂 Project Structure
rag-pdf/
│
├── streamlit_app.py        # UI (chat, upload, notes, export)
├── upload_ingest_faiss.py  # PDF upload + FAISS indexing
├── rag_chat.py             # RAG logic (retrieve + generate)
├── run_index_sync.py       # Manual indexing script
├── export_note_pdf.py      # Notes → PDF exporter
├── uploads/                # Uploaded PDFs
├── faiss_store/            # FAISS index
├── notes.db                # SQLite notes database

🚀 How to Run
1. Set API Key
setx OPENAI_API_KEY "your_api_key_here"
2. Start Backend
python -m uvicorn upload_ingest_faiss:app --reload
3. Start UI
python -m streamlit run streamlit_app.py

🎯 Use Cases
Studying from textbooks or lecture notes
Research paper Q&A
Exam revision with saved explanations
Personal knowledge base creation
