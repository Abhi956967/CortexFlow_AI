import re
import time
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content

logger = logging.getLogger("cortexflow")

CODING_SYSTEM_PROMPT = """You are CortexFlow AI Senior Software Architect and Coding Agent.

Classify the user intent into one of:
1. CODE_GENERATION (User asks to build a website, app, script, API, or project)
2. CODE_REVIEW / DEBUG / EXPLAIN (User provides code and asks to review, debug, explain, optimize)

=========================
INTENT: CODE_GENERATION
=========================
If generating a web project or UI:
- Default Stack: HTML, CSS, JavaScript (Single Page modern responsive layout with Tailwind/modern CSS variables and smooth interactions).
- Return ONLY the files formatted strictly as:

FILE: index.html
```html
<!DOCTYPE html>
...
```

FILE: style.css
```css
...
```

FILE: script.js
```javascript
...
```

If generating a Python/Backend script or other language:
FILE: main.py
```python
...
```

- NO other conversational markdown or pleasantries when generating project files.
- Ensure all code is production-grade, bug-free, and complete without placeholders like '// implement here'.

=========================
INTENT: CODE_REVIEW / DEBUG
=========================
If user asks to review, debug, explain, optimize:
Return structured Markdown only:
# 🔍 Code Analysis & Review
## 1. What This Code Does
## 2. Issues & Vulnerabilities Found
## 3. Recommended Improvements & Best Practices
## 4. Optimized Code Snippet
"""

def clean_code(code_str: str) -> str:
    # Remove surrounding ```lang ... ``` fences if present
    code_str = re.sub(r"^```[\w-]*\n?", "", code_str.strip())
    code_str = re.sub(r"```$", "", code_str.strip())
    return code_str.strip()

async def coding_node(state: AgentState) -> AgentState:
    llm = get_model("coding")
    prompt = state.get("prompt", "")

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": CODING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        content = extract_text_content(response.content).strip()

        # Parse files if generated
        files = []
        file_matches = list(re.finditer(r"FILE:\s*([^\n]+)\n([\s\S]*?)(?=\nFILE:\s*[^\n]+\n|$)", content))

        if file_matches:
            for match in file_matches:
                filename = match.group(1).strip()
                code_content = clean_code(match.group(2))
                files.append({
                    "name": filename,
                    "content": code_content
                })

        artifacts = []
        if files:
            artifacts.append({
                "id": str(int(time.time() * 1000)),
                "type": "project",
                "title": prompt[:40] + ("..." if len(prompt) > 40 else ""),
                "files": files,
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            answer = f"### 🚀 Project Generated Successfully\nGenerated **{len(files)}** files: " + ", ".join([f"`{f['name']}`" for f in files]) + "\n\nYou can preview, edit and run the generated code in the Artifact panel."
        else:
            answer = content

        return {
            **state,
            "response": answer,
            "artifacts": artifacts,
            "agent": "coding"
        }
    except Exception as e:
        logger.error(f"Coding agent error: {e}")
        return {
            **state,
            "response": f"Failed to process coding request: {str(e)}",
            "agent": "coding"
        }
