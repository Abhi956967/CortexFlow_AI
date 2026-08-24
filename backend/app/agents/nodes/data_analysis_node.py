import logging
import io
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content

logger = logging.getLogger("cortexflow")

DATA_ANALYSIS_SYSTEM = """You are an elite Data Scientist and Business Intelligence Specialist.
Your job is to analyze data, datasets, tables, CSVs, or user numerical queries with utmost precision.

Requirements:
1. Provide an **Executive Summary** of key findings and trends.
2. Present **Key Metrics & Statistics** in a clean Markdown Table.
3. Highlight **Actionable Insights & Anomalies**.
4. Suggest **Strategic Recommendations**.
5. When appropriate, provide structured sample data representations or ASCII/Markdown charts.
"""

async def data_analysis_node(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "")
    file_info = state.get("file")
    llm = get_model("data_analysis")

    data_context = ""
    if file_info and file_info.get("bytes"):
        filename = file_info.get("filename", "")
        raw_bytes = file_info.get("bytes", b"")
        try:
            # If text/csv/tsv file
            content_sample = raw_bytes[:10000].decode("utf-8", errors="ignore")
            data_context = f"\n\n[Attached Dataset: {filename}]\n```text\n{content_sample}\n```\n"
        except Exception as e:
            logger.warning(f"Could not parse file preview for data analysis: {e}")

    full_query = f"{prompt}{data_context}" if data_context else prompt

    try:
        res = await llm.ainvoke([
            {"role": "system", "content": DATA_ANALYSIS_SYSTEM},
            {"role": "user", "content": full_query}
        ])
        content = extract_text_content(res.content)
        return {
            **state,
            "response": content,
            "agent": "data_analysis"
        }
    except Exception as e:
        logger.error(f"Data Analysis node error: {e}")
        return {
            **state,
            "response": f"### 📊 Data Analysis\n\nUnable to process the dataset: {str(e)}",
            "agent": "data_analysis"
        }
