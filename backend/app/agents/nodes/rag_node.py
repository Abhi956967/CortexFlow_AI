import io
import time
import logging
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from app.agents.tools.qdrant_rag import index_and_retrieve_context

logger = logging.getLogger("cortexflow")

RAG_SYSTEM_PROMPT = """You are CortexFlow AI Document Intelligence Specialist.
Your goal is to answer the user's questions grounded accurately in the provided document passages.

Guidelines:
- Cite specific document sections or pages whenever relevant.
- Synthesize clear, well-structured Markdown responses with bold headings, key bullet points, and summaries.
- If the document does not contain the answer, accurately state what is covered and clarify the limitation.
"""

async def rag_node(state: AgentState) -> AgentState:
    file_info = state.get("file")
    prompt = state.get("prompt", "Summarize this document.")
    llm = get_model("pdf_rag")

    if not file_info:
        return {
            **state,
            "response": "No document provided for analysis. Please upload a PDF, DOCX, CSV, or TXT file.",
            "agent": "pdf_rag"
        }

    try:
        file_bytes = file_info.get("bytes", b"")
        filename = file_info.get("filename", "document").lower()
        extracted_text = ""

        # 1. Extract text based on file format
        if filename.endswith(".pdf") or "pdf" in file_info.get("content_type", ""):
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"\n[Page {i+1}]\n{page_text}"
        else:
            # Text, CSV, TSV, JSON, MD fallback
            extracted_text = file_bytes.decode("utf-8", errors="ignore")

        if not extracted_text.strip():
            return {
                **state,
                "response": "The uploaded document appears to be empty or unscannable.",
                "agent": "pdf_rag"
            }

        # 2. Chunk text
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(extracted_text)
        docs = [Document(page_content=chunk, metadata={"source": file_info.get("filename", "uploaded_doc")}) for chunk in chunks]

        # 3. Retrieve relevant context (Qdrant or In-Memory Semantic Ranker)
        context = await index_and_retrieve_context(docs, prompt, top_k=5)

        # 4. Generate Grounded LLM Response
        response = await llm.ainvoke([
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=f"Document Context:\n{context}\n\nUser Question:\n{prompt}")
        ])

        return {
            **state,
            "response": extract_text_content(response.content),
            "agent": "pdf_rag"
        }
    except Exception as e:
        logger.error(f"RAG Agent error: {e}")
        return {
            **state,
            "response": f"### 📚 Document Analysis\n\nFailed to process document: {str(e)}",
            "agent": "pdf_rag"
        }
