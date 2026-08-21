import io
import time
import logging
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from app.agents.tools.qdrant_rag import index_documents_to_qdrant, search_qdrant_context

logger = logging.getLogger("cortexflow")

RAG_SYSTEM_PROMPT = """You are CortexFlow AI Document Intelligence Assistant.
Rules:
- Answer the user's question STRICTLY based on the provided document context passages.
- If the answer cannot be found in the provided context, clearly state: "I could not find this information in the uploaded document."
- Use Markdown formatting (bullet points, clear paragraphs) to structure your response.
"""

async def rag_node(state: AgentState) -> AgentState:
    file_info = state.get("file")
    prompt = state.get("prompt", "Summarize this document.")
    llm = get_model("pdf-rag")

    if not file_info:
        return {
            **state,
            "response": "No document provided for analysis. Please upload a PDF file.",
            "agent": "pdf_rag"
        }

    try:
        file_bytes = file_info.get("bytes")
        # 1. Extract text from PDF
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        extracted_text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text += f"\n[Page {i+1}]\n{page_text}"

        if not extracted_text.strip():
            return {
                **state,
                "response": "The uploaded PDF appears to be empty or contains scanned images without text.",
                "agent": "pdf_rag"
            }

        # 2. Chunk text
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(extracted_text)
        docs = [Document(page_content=chunk, metadata={"source": file_info.get("filename", "uploaded_doc")}) for chunk in chunks]

        # 3. Index to Qdrant
        collection_name = f"doc_{int(time.time())}"
        vector_store = await index_documents_to_qdrant(collection_name, docs)

        # 4. Similarity Search
        context = await search_qdrant_context(vector_store, prompt, k=5)

        # 5. LLM Grounded Answer
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
            "response": f"Failed to process document RAG: {str(e)}",
            "agent": "pdf_rag"
        }
