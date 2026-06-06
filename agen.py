"""
Multi-Agent QA Code Generator v2
----------------------------------
Upgraded with genuine agent patterns:
  ✅ ReAct loop  (Reason → Act → Observe → Repeat)
  ✅ Agent memory  (shared state dict passed through pipeline)
  ✅ Tool use  (scraper, validator, code scorer — called by agents)
  ✅ Feedback loop  (Agent 3 scores code; loops back to Agent 2 if score < 7)
  ✅ Thought traces  (each agent shows Thought / Action / Observation)
  ✅ Orchestrator agent  (decides flow, not hardcoded)
  ✅ Max iteration cap  (prevents infinite loops)

No CrewAI · No LangChain · No paid APIs · Groq free tier only
"""

import streamlit as st
import requests
import time
import re
import json
from bs4 import BeautifulSoup
from groq import Groq

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QA Agent System v2",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Bricolage+Grotesque:wght@400;600;800&display=swap');

:root {
  --bg: #080a0f;
  --surface: #0f1219;
  --card: #141820;
  --border: #1e2535;
  --border-bright: #2d3650;
  --green: #00ff9d;
  --blue: #4d79ff;
  --orange: #ff8c42;
  --red: #ff4d6d;
  --yellow: #ffd166;
  --text: #d4daf0;
  --muted: #5a6380;
}

html, body, [class*="css"] {
  font-family: 'Bricolage Grotesque', sans-serif;
  background: var(--bg) !important;
  color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero {
  padding: 2.5rem 1rem 2rem;
  text-align: center;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
  position: relative;
}
.hero::before {
  content: '';
  position: absolute;
  top: 0; left: 50%;
  transform: translateX(-50%);
  width: 600px; height: 200px;
  background: radial-gradient(ellipse at center, rgba(77,121,255,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.hero-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .72rem;
  color: var(--blue);
  letter-spacing: .2em;
  text-transform: uppercase;
  margin-bottom: .6rem;
}
.hero h1 {
  font-size: 2.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #00ff9d 0%, #4d79ff 50%, #ff8c42 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 .5rem;
  line-height: 1.1;
}
.hero p { color: var(--muted); font-size: .95rem; margin: 0; }

/* ── Agent pipeline overview ── */
.pipeline {
  display: flex;
  align-items: center;
  gap: .5rem;
  justify-content: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.pipe-node {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: .5rem 1rem;
  font-size: .8rem;
  color: var(--text);
}
.pipe-arrow { color: var(--muted); font-size: 1.2rem; }
.pipe-loop {
  background: rgba(255,140,66,.08);
  border-color: var(--orange);
  color: var(--orange);
}

/* ── ReAct trace card ── */
.react-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--blue);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  margin-bottom: .8rem;
  font-size: .85rem;
}
.react-card.done  { border-left-color: var(--green); }
.react-card.loop  { border-left-color: var(--orange); }
.react-card.error { border-left-color: var(--red); }
.react-card.orch  { border-left-color: var(--yellow); }

.agent-name {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .75rem;
  font-weight: 600;
  letter-spacing: .1em;
  text-transform: uppercase;
  margin-bottom: .6rem;
}
.agent-name.green  { color: var(--green); }
.agent-name.blue   { color: var(--blue); }
.agent-name.orange { color: var(--orange); }
.agent-name.yellow { color: var(--yellow); }
.agent-name.red    { color: var(--red); }

.trace-row { margin-bottom: .4rem; }
.trace-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .72rem;
  color: var(--muted);
  display: inline-block;
  width: 90px;
}
.trace-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .78rem;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}
.trace-val.green  { color: var(--green); }
.trace-val.orange { color: var(--orange); }
.trace-val.red    { color: var(--red); }

/* ── Memory panel ── */
.memory-panel {
  background: rgba(77,121,255,.05);
  border: 1px solid rgba(77,121,255,.2);
  border-radius: 8px;
  padding: .8rem 1rem;
  margin-bottom: 1rem;
  font-family: 'IBM Plex Mono', monospace;
  font-size: .75rem;
  color: #7a8cb5;
}
.memory-panel b { color: var(--blue); }

/* ── Score badge ── */
.score-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: .78rem;
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
}
.score-high { background: rgba(0,255,157,.1); color: var(--green);  border: 1px solid var(--green); }
.score-mid  { background: rgba(255,209,102,.1); color: var(--yellow); border: 1px solid var(--yellow); }
.score-low  { background: rgba(255,77,109,.1); color: var(--red);    border: 1px solid var(--red); }

/* ── Iteration counter ── */
.iter-badge {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .72rem;
  color: var(--orange);
  background: rgba(255,140,66,.08);
  border: 1px solid rgba(255,140,66,.3);
  border-radius: 4px;
  padding: 2px 8px;
  margin-left: 8px;
}

/* ── Streamlit overrides ── */
.stButton > button {
  background: linear-gradient(135deg, #00ff9d, #4d79ff) !important;
  color: #080a0f !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Bricolage Grotesque', sans-serif !important;
}
.stTextInput > div > div > input {
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-bright) !important;
  border-radius: 8px !important;
}
.stDownloadButton > button {
  background: var(--card) !important;
  color: var(--green) !important;
  border: 1px solid var(--green) !important;
  border-radius: 8px !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .8rem !important;
}
div[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-label">ReAct · Tool Use · Feedback Loop · Memory</div>
  <h1>Multi-Agent QA System</h1>
  <p>Orchestrator + 3 Specialist Agents · Java Selenium TestNG · Groq Free Tier</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pipeline">
  <div class="pipe-node">🌐 Scraper Tool</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node" style="border-color:#ffd166;color:#ffd166;">🧠 Orchestrator</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">🔍 Element Finder</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">☕ Test Architect</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">🔎 QA Reviewer</div>
  <div class="pipe-arrow">↩</div>
  <div class="pipe-node pipe-loop">♻️ Feedback Loop</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown(
        "Get a **free** Groq API key at "
        "[console.groq.com](https://console.groq.com)"
    )
    groq_api_key = st.text_input(
        "Groq API Key", type="password",
        placeholder="gsk_...",
    )
    model = st.selectbox(
        "Model",
        ["llama-3.3-70b-versatile", "llama3-8b-8192", "gemma2-9b-it"],
        index=0,
    )
    st.markdown("---")
    include_waits  = st.checkbox("Include WebDriverWait", value=True)
    include_testng = st.checkbox("Use TestNG", value=True)
    max_elements   = st.slider("Max elements to analyse", 10, 40, 20)
    delay_secs     = st.slider("Delay between agents (s)", 2, 15, 5)
    max_iterations = st.slider(
        "Max feedback loop iterations", 1, 5, 3,
        help="Agent 3 loops back to Agent 2 if code score < 7. This caps the loop."
    )
    score_threshold = st.slider(
        "Code quality threshold (0–10)", 5, 9, 7,
        help="Agent 3 loops back to Agent 2 until score ≥ this value."
    )
    st.markdown("---")
    st.markdown("**Agent patterns active**")
    st.caption("✅ ReAct loop\n✅ Tool use\n✅ Agent memory\n✅ Feedback loop\n✅ Thought traces\n✅ Orchestrator")


# ══════════════════════════════════════════════════════════════════════════════
# TOOLS  (called by agents — this is what makes it agentic)
# ══════════════════════════════════════════════════════════════════════════════

def tool_scrape_page(url: str, limit: int) -> dict:
    """
    Tool: scrape_page
    Returns structured dict so agents can reason over it.
    """
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (QA-AgentBot/2.0)"},
            timeout=15, verify=False,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Unknown"
        h1s   = [h.get_text(strip=True) for h in soup.find_all("h1", limit=3)]
        forms = [str(f)[:200] for f in soup.find_all("form", limit=3)]
        elements = []
        for tag in soup.find_all(
            ["input", "button", "a", "select", "textarea", "label"],
            limit=limit * 2,
        ):
            attrs = {
                k: (v if isinstance(v, str) else " ".join(v))
                for k, v in tag.attrs.items()
                if k in ("id", "name", "type", "class", "href",
                         "placeholder", "aria-label", "value", "action")
            }
            elements.append({
                "tag":   tag.name,
                "text":  tag.get_text(strip=True)[:60],
                "attrs": attrs,
            })
            if len(elements) >= limit:
                break
        return {
            "status":   "success",
            "title":    title,
            "h1s":      h1s,
            "url":      url,
            "forms":    forms,
            "elements": elements,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url, "elements": []}


def tool_validate_java_syntax(code: str) -> dict:
    """
    Tool: validate_java_syntax
    Heuristic checks — no compiler needed.
    Returns issues list so Agent 3 can reason over them.
    """
    issues = []
    if "Thread.sleep" in code:
        issues.append("Thread.sleep() found — should use WebDriverWait")
    if "import org.testng" not in code and "import org.junit" not in code:
        issues.append("Missing test framework import (TestNG or JUnit)")
    if "@Test" not in code:
        issues.append("No @Test annotation found")
    if "driver.quit" not in code and "driver.close" not in code:
        issues.append("No driver teardown (driver.quit/close)")
    if "//*[" in code or "//div[" in code:
        count = code.count("//*[") + code.count("//div[")
        if count > 3:
            issues.append(f"Excessive absolute XPath usage ({count} occurrences)")
    open_b  = code.count("{")
    close_b = code.count("}")
    if open_b != close_b:
        issues.append(f"Bracket mismatch: {{ {open_b} vs }} {close_b}")
    if "package com.qa" not in code:
        issues.append("Missing package declaration")
    return {
        "issues":     issues,
        "issue_count": len(issues),
        "valid":      len(issues) == 0,
    }


def tool_score_code(code: str, issues: list) -> dict:
    """
    Tool: score_code
    Produces a deterministic base score + per-issue penalty.
    """
    score = 10
    score -= len(issues) * 1.5
    if len(code) < 500:
        score -= 2
    if "WebDriverWait" in code:
        score += 0.5
    if "PageFactory" in code or "FindBy" in code:
        score += 0.5
    score = max(0, min(10, round(score, 1)))
    return {"score": score, "max": 10}


# ══════════════════════════════════════════════════════════════════════════════
# AGENT MEMORY  (shared state — passed through the entire pipeline)
# ══════════════════════════════════════════════════════════════════════════════

def init_memory(url: str) -> dict:
    return {
        "url":            url,
        "page_data":      None,   # filled by scraper tool
        "element_analysis": None, # filled by Agent 1
        "raw_code":       None,   # filled by Agent 2
        "final_code":     None,   # filled by Agent 3
        "iterations":     0,
        "scores":         [],     # score per iteration
        "issues_history": [],     # issues per iteration
        "agent_logs":     [],     # thought traces
        "orchestrator_plan": None,
    }


def log_trace(memory: dict, agent: str, thought: str, action: str, observation: str):
    memory["agent_logs"].append({
        "agent":       agent,
        "thought":     thought,
        "action":      action,
        "observation": observation,
        "iteration":   memory["iterations"],
        "ts":          time.time(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# LLM WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

def call_llm(client: Groq, model_name: str, system: str, user: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                temperature=0.2,
                max_tokens=4096,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < retries - 1:
                wait = 20 * (attempt + 1)
                st.warning(f"⏳ Rate limit — waiting {wait}s (retry {attempt+2}/{retries})…")
                time.sleep(wait)
            else:
                raise
    return "LLM call failed."


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR AGENT  — plans the pipeline, decides if loop continues
# ══════════════════════════════════════════════════════════════════════════════

def orchestrator_plan(client, model_name, memory: dict) -> str:
    system = """You are an AI Orchestrator managing a multi-agent QA pipeline.
Your job: analyse the current memory state and output a JSON plan.
Always return ONLY valid JSON. No preamble. No markdown fences.
Schema:
{
  "plan": ["agent_1", "agent_2", "agent_3"],
  "priority": "correctness|speed|coverage",
  "notes": "brief instruction to agents"
}"""
    page_summary = f"URL: {memory['url']}, Elements found: {len(memory['page_data'].get('elements', []))}" \
        if memory['page_data'] and memory['page_data'].get('status') == 'success' \
        else f"URL: {memory['url']}, page scrape failed"

    user = f"""Current pipeline state:
- Page: {page_summary}
- Iterations so far: {memory['iterations']}
- Last score: {memory['scores'][-1] if memory['scores'] else 'none yet'}
- Open issues: {memory['issues_history'][-1] if memory['issues_history'] else 'none yet'}

Determine the execution plan."""
    raw = call_llm(client, model_name, system, user)
    try:
        raw_clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_clean).get("notes", "Standard pipeline execution.")
    except Exception:
        return "Standard pipeline execution."


def orchestrator_should_loop(client, model_name, memory: dict, score: float, threshold: float) -> bool:
    """Orchestrator decides whether to trigger another feedback loop."""
    if score >= threshold:
        return False
    if memory["iterations"] >= 3:
        return False
    system = """You are an AI Orchestrator. Answer ONLY with JSON: {"loop": true} or {"loop": false}.
Loop if: score is below threshold AND there are fixable issues AND iterations < 3."""
    user = f"""Score: {score}/{threshold} threshold. Issues: {memory['issues_history'][-1]}. Iterations: {memory['iterations']}. Should we loop?"""
    raw = call_llm(client, model_name, system, user)
    try:
        raw_clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_clean).get("loop", False)
    except Exception:
        return score < threshold


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 1 — Element Finder  (ReAct: uses scraper tool result)
# ══════════════════════════════════════════════════════════════════════════════

def agent_element_finder(client, model_name, memory: dict, max_el: int) -> str:
    # THOUGHT
    thought = f"I need to identify testable elements on {memory['url']}. I have scraper tool output in memory. I will reason over it to produce locators."

    # ACTION — reason over tool output (already in memory)
    page = memory["page_data"]
    if page["status"] == "error":
        ctx = f"Scrape failed: {page.get('error')}. Work from URL only: {memory['url']}"
    else:
        rows = []
        for el in page["elements"]:
            rows.append(f"  <{el['tag']}> text='{el['text']}' attrs={el['attrs']}")
        ctx = (
            f"Title: {page['title']}\nH1s: {', '.join(page['h1s'])}\n"
            f"URL: {page['url']}\nForms: {len(page['forms'])} found\n\n"
            f"Elements ({len(rows)}):\n" + "\n".join(rows)
        )

    system = """You are a Senior QA Automation Engineer specialising in Selenium locator strategy.
Analyse the page snapshot and output a structured list of interactive elements with the BEST locator.
Prefer: ID > name > CSS selector > XPath.
Format:
  [N] Tag: <tag> | Purpose: <what it does> | Locator: By.<TYPE>("value") | Priority: HIGH/MED/LOW
Be concise. No preamble."""

    user = f"""Analyse this page and identify up to {max_el} critical interactive elements.

PAGE SNAPSHOT:
{ctx}

List with Selenium locators. Prioritise HIGH for login/submit/search elements."""

    result = call_llm(client, model_name, system, user)

    # OBSERVATION
    obs = f"Identified {result.count('[') } elements with locator strategies."
    log_trace(memory, "Element Finder", thought, "call_llm(element_analysis)", obs)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 2 — Test Architect  (aware of previous issues if looping)
# ══════════════════════════════════════════════════════════════════════════════

def agent_test_architect(client, model_name, memory: dict,
                         wait_instr: bool, testng_instr: bool) -> str:
    iteration   = memory["iterations"]
    prev_issues = memory["issues_history"][-1] if memory["issues_history"] else []
    prev_code   = memory["raw_code"]

    # THOUGHT
    if iteration == 0:
        thought = "First pass. I will generate a complete Java POM test suite from the element analysis."
    else:
        thought = f"Iteration {iteration+1}. Previous code scored low. Issues to fix: {prev_issues}. I will regenerate addressing these specifically."

    waits_note = (
        "Use WebDriverWait(driver, Duration.ofSeconds(10)) + ExpectedConditions. NEVER Thread.sleep()."
        if wait_instr else "Implicit waits are acceptable."
    )
    testng_note = (
        "Use TestNG: import org.testng.annotations.*; import org.testng.Assert;"
        if testng_instr else
        "Use JUnit 5: import org.junit.jupiter.api.*; import static org.junit.jupiter.api.Assertions.*;"
    )

    fix_section = ""
    if prev_issues:
        fix_section = f"""
CRITICAL — FIX THESE ISSUES FROM PREVIOUS ITERATION:
{chr(10).join(f'  - {i}' for i in prev_issues)}
The previous code was rejected. Address every issue above explicitly.
"""
    if prev_code and iteration > 0:
        fix_section += f"\nPREVIOUS CODE (broken):\n{prev_code[:1500]}\n...fix it."

    system = f"""You are a Selenium Test Architect expert in Java, POM, and TestNG.
Rules:
- package com.qa.tests;
- Page class: private By fields, public action methods
- Test class: @BeforeMethod ChromeDriver setup, @AfterMethod quit
- Minimum 3 @Test methods: happy path, negative, boundary/edge
- {waits_note}
- {testng_note}
- Real code only — no placeholder comments
- Output TWO code blocks: Page class first, then Test class"""

    user = f"""Generate complete Java Selenium code for: {memory['url']}
{fix_section}
ELEMENT ANALYSIS:
{memory['element_analysis']}

REQUIREMENTS:
- {waits_note}
- {testng_note}
- Page Object Model
- All imports included"""

    result = call_llm(client, model_name, system, user)

    obs = f"Generated {len(result)} chars of Java code (iteration {iteration+1})."
    log_trace(memory, "Test Architect", thought,
              f"call_llm(generate_code, iteration={iteration+1})", obs)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 3 — QA Reviewer  (uses validator + scorer tools, triggers loop)
# ══════════════════════════════════════════════════════════════════════════════

def agent_qa_reviewer(client, model_name, memory: dict) -> tuple[str, float, list]:
    code = memory["raw_code"]

    # THOUGHT
    thought = "I will validate the code using my tools, score it, and fix any issues I find."

    # ACTION 1 — call validator tool
    validation = tool_validate_java_syntax(code)
    issues     = validation["issues"]

    # ACTION 2 — call scorer tool
    score_result = tool_score_code(code, issues)
    score        = score_result["score"]

    # OBSERVATION
    obs = f"Validator found {len(issues)} issue(s). Score: {score}/10."
    log_trace(memory, "QA Reviewer", thought,
              f"tool_validate_java_syntax() + tool_score_code()", obs)

    # ACTION 3 — LLM fix pass
    system = """You are a strict QA Lead Reviewer. Fix ALL issues in this Java Selenium code:
- Wrong/missing imports
- Thread.sleep() → WebDriverWait
- Brittle XPath → ID/CSS
- Missing TestNG annotations
- Compilation errors (brackets, types)
Output ONLY the final corrected Java code. No explanation. No markdown fences."""

    issue_list = "\n".join(f"  - {i}" for i in issues) if issues else "  - No critical issues. Improve style and robustness."

    user = f"""Review and fix this Java Selenium TestNG code for {memory['url']}.

KNOWN ISSUES TO FIX:
{issue_list}

CODE:
{code}

Output the final production-ready version:"""

    fixed_code = call_llm(client, model_name, system, user)

    # Re-validate and re-score the fixed code
    re_validation   = tool_validate_java_syntax(fixed_code)
    re_score_result = tool_score_code(fixed_code, re_validation["issues"])
    final_score     = re_score_result["score"]

    log_trace(memory, "QA Reviewer",
              "Re-validating fixed code with tools.",
              "tool_validate_java_syntax(fixed) + tool_score_code(fixed)",
              f"Final score after fix: {final_score}/10. Issues remaining: {re_validation['issues']}")

    memory["issues_history"].append(re_validation["issues"])
    memory["scores"].append(final_score)

    return fixed_code, final_score, re_validation["issues"]


# ══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def render_trace(log: dict):
    iter_badge = f'<span class="iter-badge">iter {log["iteration"]+1}</span>' if log["iteration"] > 0 else ""
    color_map = {
        "Orchestrator":   "yellow",
        "Element Finder": "blue",
        "Test Architect": "green",
        "QA Reviewer":    "orange",
    }
    color = color_map.get(log["agent"], "blue")
    st.markdown(f"""
    <div class="react-card">
      <div class="agent-name {color}">⬡ {log['agent']}{iter_badge}</div>
      <div class="trace-row">
        <span class="trace-label">THOUGHT</span>
        <span class="trace-val">{log['thought']}</span>
      </div>
      <div class="trace-row">
        <span class="trace-label">ACTION</span>
        <span class="trace-val green">{log['action']}</span>
      </div>
      <div class="trace-row">
        <span class="trace-label">OBSERVATION</span>
        <span class="trace-val">{log['observation']}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_memory_panel(memory: dict):
    st.markdown(f"""
    <div class="memory-panel">
      <b>🧠 Agent Memory</b> &nbsp;|&nbsp;
      url: {memory['url'][:50]}… &nbsp;|&nbsp;
      iterations: {memory['iterations']} &nbsp;|&nbsp;
      scores: {memory['scores']} &nbsp;|&nbsp;
      log_entries: {len(memory['agent_logs'])}
    </div>
    """, unsafe_allow_html=True)


def score_badge_html(score: float) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 5 else "score-low")
    return f'<span class="score-badge {cls}">{score}/10</span>'


def is_valid_url(url: str) -> bool:
    return bool(re.match(
        r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(:\d+)?(/[^\s]*)?$',
        url.strip()
    ))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN UI
# ══════════════════════════════════════════════════════════════════════════════

url_input = st.text_input(
    "🌐 Target Website URL",
    placeholder="https://example.com/login",
)

run_btn = st.button("🚀 Launch Agent Pipeline", use_container_width=True, type="primary")

if run_btn:
    if not groq_api_key or not groq_api_key.startswith("gsk_"):
        st.error("❌ Enter a valid Groq API key in the sidebar.")
        st.stop()
    if not url_input or not is_valid_url(url_input):
        st.error("❌ Enter a valid URL starting with https:// or http://")
        st.stop()

    client = Groq(api_key=groq_api_key)
    memory = init_memory(url_input)

    st.markdown("## 🤖 Agent Execution Log")
    trace_container = st.container()

    # ── STEP 0: Scraper Tool ──────────────────────────────────────────────────
    with st.spinner("🔍 Scraper tool running…"):
        page_data = tool_scrape_page(url_input, max_elements)
        memory["page_data"] = page_data

    log_trace(memory, "Orchestrator",
              f"Pipeline started for {url_input}. Running scraper tool first.",
              "tool_scrape_page(url)",
              f"Scraped {len(page_data.get('elements', []))} elements. Status: {page_data['status']}")

    with trace_container:
        render_memory_panel(memory)
        render_trace(memory["agent_logs"][-1])

    with st.expander("📄 Raw Page Snapshot", expanded=False):
        st.json(page_data)

    time.sleep(delay_secs)

    # ── ORCHESTRATOR PLAN ─────────────────────────────────────────────────────
    with st.spinner("🧠 Orchestrator planning pipeline…"):
        orch_notes = orchestrator_plan(client, model, memory)
        memory["orchestrator_plan"] = orch_notes
        log_trace(memory, "Orchestrator",
                  "Analysing memory state to decide execution plan.",
                  "orchestrator_plan(memory)",
                  f"Plan: {orch_notes}")

    with trace_container:
        render_trace(memory["agent_logs"][-1])

    time.sleep(delay_secs)

    # ── AGENT 1: Element Finder ───────────────────────────────────────────────
    with st.spinner("🔍 Agent 1: Analysing elements…"):
        try:
            a1_out = agent_element_finder(client, model, memory, max_elements)
            memory["element_analysis"] = a1_out
        except Exception as e:
            st.error(f"Agent 1 failed: {e}")
            st.stop()

    with trace_container:
        render_trace(memory["agent_logs"][-1])
        st.markdown(f"""
        <div class="react-card done">
          <div class="agent-name blue">✓ Element Analysis Complete</div>
          <div class="trace-val" style="margin-top:.4rem">{a1_out[:400]}{"…" if len(a1_out)>400 else ""}</div>
        </div>""", unsafe_allow_html=True)

    time.sleep(delay_secs)

    # ── FEEDBACK LOOP: Agent 2 → Agent 3 → (loop if score < threshold) ────────
    final_code  = ""
    final_score = 0.0

    for iteration in range(max_iterations):
        memory["iterations"] = iteration

        # ── Agent 2: Test Architect ───────────────────────────────────────────
        with st.spinner(f"☕ Agent 2: Writing Java code (iteration {iteration+1})…"):
            try:
                a2_out = agent_test_architect(
                    client, model, memory, include_waits, include_testng
                )
                memory["raw_code"] = a2_out
            except Exception as e:
                st.error(f"Agent 2 failed: {e}")
                st.stop()

        with trace_container:
            iter_label = f" (iter {iteration+1})" if iteration > 0 else ""
            st.markdown(f"""
            <div class="react-card {'loop' if iteration > 0 else ''}">
              <div class="agent-name green">☕ Test Architect{iter_label}</div>
              <div class="trace-val" style="margin-top:.4rem">Generated {len(a2_out)} chars of Java code.</div>
            </div>""", unsafe_allow_html=True)
            render_trace(memory["agent_logs"][-1])

        time.sleep(delay_secs)

        # ── Agent 3: QA Reviewer + Tools ─────────────────────────────────────
        with st.spinner(f"🔎 Agent 3: Reviewing + scoring (iteration {iteration+1})…"):
            try:
                fixed_code, score, issues = agent_qa_reviewer(client, model, memory)
                memory["final_code"] = fixed_code
                final_code  = fixed_code
                final_score = score
            except Exception as e:
                st.error(f"Agent 3 failed: {e}")
                st.stop()

        with trace_container:
            render_trace(memory["agent_logs"][-1])
            score_html = score_badge_html(score)
            issues_html = "<br>".join(f"• {i}" for i in issues) if issues else "✅ No issues found"
            st.markdown(f"""
            <div class="react-card {'done' if score >= score_threshold else 'loop'}">
              <div class="agent-name orange">🔎 QA Reviewer — Score: {score_html}</div>
              <div class="trace-val" style="margin-top:.4rem">{issues_html}</div>
            </div>""", unsafe_allow_html=True)
            render_memory_panel(memory)

        # ── Orchestrator decides: loop or done? ───────────────────────────────
        if score >= score_threshold:
            log_trace(memory, "Orchestrator",
                      f"Score {score} ≥ threshold {score_threshold}. Code quality accepted.",
                      "orchestrator_should_loop() → False",
                      "Pipeline complete. Exiting loop.")
            with trace_container:
                render_trace(memory["agent_logs"][-1])
                st.markdown(f"""
                <div class="react-card done">
                  <div class="agent-name yellow">✅ Orchestrator — Pipeline Complete</div>
                  <div class="trace-val green" style="margin-top:.4rem">Score {score}/10 accepted after {iteration+1} iteration(s).</div>
                </div>""", unsafe_allow_html=True)
            break
        else:
            should_loop = orchestrator_should_loop(
                client, model, memory, score, score_threshold
            )
            if should_loop and iteration < max_iterations - 1:
                log_trace(memory, "Orchestrator",
                          f"Score {score} < {score_threshold}. Triggering feedback loop.",
                          f"orchestrator_should_loop() → True (iter {iteration+2})",
                          f"Sending issues back to Agent 2: {issues}")
                with trace_container:
                    render_trace(memory["agent_logs"][-1])
                    st.markdown(f"""
                    <div class="react-card loop">
                      <div class="agent-name yellow">♻️ Orchestrator — Triggering Feedback Loop</div>
                      <div class="trace-val orange" style="margin-top:.4rem">Score {score}/10 below threshold {score_threshold}. Looping Agent 2 → Agent 3 (iteration {iteration+2}).</div>
                    </div>""", unsafe_allow_html=True)
                time.sleep(delay_secs)
            else:
                log_trace(memory, "Orchestrator",
                          f"Max iterations reached or loop not warranted. Accepting score {score}.",
                          "orchestrator_should_loop() → False (cap reached)",
                          "Exiting with best code so far.")
                with trace_container:
                    render_trace(memory["agent_logs"][-1])
                break

    # ── Final Output ──────────────────────────────────────────────────────────
    st.success(f"✅ Pipeline Complete — Final Score: {final_score}/10 — {memory['iterations']+1} iteration(s)")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "☕ Final Java Code",
        "🔍 Element Analysis",
        "🧠 Agent Memory",
        "📋 Full Trace Log",
    ])

    with tab1:
        st.markdown("### Production-Ready Java Selenium TestNG Code")
        st.code(final_code, language="java")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Java Code",
                data=final_code,
                file_name="SeleniumTestNG_Generated.java",
                mime="text/plain",
            )
        with col2:
            st.markdown(f"**Quality Score:** {score_badge_html(final_score)}", unsafe_allow_html=True)

    with tab2:
        st.markdown("### Element Analysis (Agent 1)")
        st.text_area("Elements", value=memory["element_analysis"], height=300)

    with tab3:
        st.markdown("### Agent Memory State")
        safe_memory = {k: v for k, v in memory.items() if k not in ("raw_code", "final_code", "element_analysis")}
        st.json(safe_memory)

    with tab4:
        st.markdown("### Full ReAct Trace Log")
        for log in memory["agent_logs"]:
            render_trace(log)

else:
    col1, col2, col3, col4 = st.columns(4)
    cards = [
        ("🧠", "yellow",  "Orchestrator",    "Plans the pipeline, decides if the feedback loop should continue based on score and issue analysis."),
        ("🔍", "blue",    "Element Finder",  "Uses scraper tool output. Produces locator strategy with priority tiers (HIGH/MED/LOW)."),
        ("☕", "green",   "Test Architect",  "Generates Java POM code. Re-runs with issue context on feedback loop iterations."),
        ("🔎", "orange",  "QA Reviewer",     "Calls validate + score tools. Triggers feedback loop if score < threshold."),
    ]
    for col, (icon, color, name, desc) in zip([col1, col2, col3, col4], cards):
        with col:
            st.markdown(f"""
            <div class="react-card">
              <div class="agent-name {color}">{icon} {name}</div>
              <p style="color:var(--muted);font-size:.83rem;margin:.4rem 0 0">{desc}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="react-card orch" style="margin-top:1rem">
      <div class="agent-name yellow">⬡ Active Agent Patterns</div>
      <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:.5rem">
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ ReAct Loop</span>
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ Tool Use (3 tools)</span>
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ Agent Memory</span>
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ Feedback Loop</span>
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ Thought Traces</span>
        <span style="color:#00ff9d;font-family:'IBM Plex Mono',monospace;font-size:.8rem">✅ Orchestrator</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("👆 Add your **free Groq API key** in the sidebar and enter a URL above to start.")

st.caption("Multi-Agent QA System v2 · Groq Free · BeautifulSoup · Streamlit · Zero paid dependencies")
