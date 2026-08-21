import sys
import io

# Ensure UTF-8 output on Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
from app.agents.supervisor import multi_agent_graph

async def run_tests():
    print("[TEST] Running Multi-Agent Graph Test Suite...")

    # Test 1: Coding request
    print("\n--- Test 1: Coding Agent ---")
    state1 = {
        "prompt": "Create a simple Python function to calculate fibonacci numbers",
        "agent": "coding"
    }
    res1 = await multi_agent_graph.ainvoke(state1)
    print(f"Agent used: {res1.get('agent')}")
    print(f"Response snippet:\n{res1.get('response')[:200]}...")

    # Test 2: PPT Request
    print("\n--- Test 2: PPT Agent ---")
    state2 = {
        "prompt": "Generate a presentation on AI in Healthcare",
        "agent": "ppt"
    }
    res2 = await multi_agent_graph.ainvoke(state2)
    print(f"Agent used: {res2.get('agent')}")
    print(f"Response snippet:\n{res2.get('response')[:200]}...")

    # Test 3: PDF Document Generation
    print("\n--- Test 3: PDF Agent ---")
    state3 = {
        "prompt": "Generate a project report for Cloud Architecture",
        "agent": "pdf"
    }
    res3 = await multi_agent_graph.ainvoke(state3)
    print(f"Agent used: {res3.get('agent')}")
    print(f"Response snippet:\n{res3.get('response')[:200]}...")

    print("\n[SUCCESS] All Multi-Agent Workflow Tests Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
