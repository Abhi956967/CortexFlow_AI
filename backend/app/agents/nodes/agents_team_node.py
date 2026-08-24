import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content

logger = logging.getLogger("cortexflow")

AGENTS_TEAM_SYSTEM = """You are CortexAI Autonomous Multi-Agent Swarm Orchestrator.
When a user asks for a complex task, simulate a collaborative deliberation between 3 specialized autonomous agents:

1. 🎯 **Agent Alpha (Strategic Planner & Architect)**:
   - Breaks down the problem into structured phases and blueprints.
2. ⚡ **Agent Beta (Lead Specialist & Implementation Engineer)**:
   - Delivers concrete, deep-dive execution steps, algorithms, and code/solutions.
3. 🛡️ **Agent Gamma (Quality Critic & Security Auditor)**:
   - Analyzes edge cases, performance bottlenecks, and security vulnerabilities.

Format your output clearly with distinct agent headings, culminating in a **Final Synthesized Action Plan**.
"""

async def agents_team_node(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "")
    llm = get_model("agents_team")

    try:
        res = await llm.ainvoke([
            {"role": "system", "content": AGENTS_TEAM_SYSTEM},
            {"role": "user", "content": prompt}
        ])
        content = extract_text_content(res.content)
        return {
            **state,
            "response": content,
            "agent": "agents_team"
        }
    except Exception as e:
        logger.error(f"Agents Team node error: {e}")
        return {
            **state,
            "response": f"### 🤖 Multi-Agent Team\n\nFailed to orchestrate agent team: {str(e)}",
            "agent": "agents_team"
        }
