# streamlit_app.py
import streamlit as st
import tempfile
import requests
import os

from rag_chat import (
    answer_question,
    create_note,
    append_to_note,
    list_notes
)

from export_note_pdf import generate_note_pdf

API_UPLOAD_URL = "http://127.0.0.1:8000/upload"

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="ATHENA — RAG Learning Assistant",
    layout="wide"
)

st.title("📘 ATHENA — RAG Learning Assistant")

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

if "selected_note" not in st.session_state:
    st.session_state.selected_note = None

# -------------------------------------------------
# Sidebar — PDF Upload
# -------------------------------------------------
st.sidebar.header("📄 Upload PDF")

uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file:
    with st.spinner("Uploading & indexing..."):
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        try:
            res = requests.post(API_UPLOAD_URL, files=files, timeout=120)
            if res.status_code == 200:
                st.sidebar.success("PDF uploaded & indexed")
            else:
                st.sidebar.error(res.text)
        except Exception as e:
            st.sidebar.error(str(e))

# -------------------------------------------------
# Sidebar — Notes
# -------------------------------------------------
st.sidebar.header("📝 Saved Notes")

notes = list_notes()

if notes:
    for nid, title, content, sources, created, updated in notes:
        if st.sidebar.button(f"📌 {title}", key=f"note_{nid}"):
            st.session_state.selected_note = nid
else:
    st.sidebar.info("No notes yet")

# -------------------------------------------------
# Layout
# -------------------------------------------------
col1, col2 = st.columns([3, 2])

# -------------------------------------------------
# Question & Answer
# -------------------------------------------------
with col1:
    st.subheader("Ask from your uploaded PDFs")

    question = st.text_input(
        "Your question",
        placeholder="e.g. Explain EDA in simple terms"
    )

    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question")
        else:
            with st.spinner("Thinking..."):
                answer, sources = answer_question(question)

                st.session_state.last_answer = answer
                st.session_state.last_sources = sources

                st.markdown("### ✅ Answer")
                st.write(answer)

                

# -------------------------------------------------
# Notes actions
# -------------------------------------------------
with col2:
    st.subheader("🧠 Save this answer")

    if st.session_state.last_answer:

        mode = st.radio(
            "Choose action",
            ["Create new note", "Append to existing note"]
        )

        if mode == "Create new note":
            note_title = st.text_input(
                "Note title",
                placeholder="EDA basics"
            )

            if st.button("➕ Save new note"):
                if not note_title.strip():
                    st.warning("Title required")
                else:
                    create_note(
                        title=note_title,
                        content=st.session_state.last_answer,
                        sources=", ".join(
                            {s["source"] for s in st.session_state.last_sources}
                        )
                    )
                    st.success("Note saved")

        else:
            if notes:
                note_map = {
                    f"{nid}: {title}": nid
                    for nid, title, *_ in notes
                }

                selected = st.selectbox(
                    "Select note",
                    list(note_map.keys())
                )

                if st.button("➕ Append"):
                    append_to_note(
                        note_id=note_map[selected],
                        new_content=st.session_state.last_answer,
                        new_sources=", ".join(
                            {s["source"] for s in st.session_state.last_sources}
                        )
                    )
                    st.success("Note updated")
            else:
                st.info("No notes to append")

# -------------------------------------------------
# View selected note
# -------------------------------------------------
if st.session_state.selected_note:
    st.markdown("---")
    st.subheader("📘 Note")

    note = next(n for n in notes if n[0] == st.session_state.selected_note)
    _, title, content, sources, created, updated = note

    st.markdown(f"### {title}")
    st.write(content)
    st.caption(f"Last updated: {updated}")

    # -------------------------------------------------
    # Export
    # -------------------------------------------------
    st.markdown("### 📥 Export")

    if st.button("Download as PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        generate_note_pdf(
            title=title,
            content=content,
            sources=sources,
            output_path=pdf_path
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Click to download PDF",
                f,
                file_name=f"{title.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
