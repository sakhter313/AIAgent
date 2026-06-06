"""
CrewAI-style Multi-Agent QA Generator
--------------------------------------
NO crewai · NO langchain · NO OpenAI · NO paid APIs
Uses ONLY: groq (free tier) + requests + beautifulsoup4 + streamlit

Free Groq limits (as of 2025):
  llama-3.3-70b-versatile : 30 RPM, 14,400 req/day
  llama3-8b-8192          : 30 RPM, 14,400 req/day
  gemma2-9b-it            : 30 RPM, 14,400 req/day
"""

import streamlit as st
import requests
import time
import re
from bs4 import BeautifulSoup
from groq import Groq

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QA Agent — Java Selenium TestNG",
    page_icon="🧪",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root { --bg:#0d0f12; --card:#141720; --border:#2a2f45; --green:#00e5a0; --blue:#5b6af0; }
html,body,[class*="css"] { font-family:'Syne',sans-serif; background:var(--bg)!important; color:#e0e0e0!important; }
#MainMenu,footer,header { visibility:hidden; }
.hero { text-align:center; padding:2rem 1rem 1.5rem; border-bottom:1px solid var(--border); margin-bottom:1.5rem; }
.hero h1 { font-size:2.4rem; background:linear-gradient(135deg,#00e5a0,#5b6af0); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
.hero p  { color:#888; margin-top:.4rem; }
.agent-card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:.8rem; }
.agent-title { font-weight:700; color:var(--green); margin-bottom:.3rem; font-size:.95rem; }
.agent-out   { font-family:'JetBrains Mono',monospace; font-size:.82rem; color:#ccc; white-space:pre-wrap; word-break:break-word; }
.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:700; margin-left:.5rem; }
.badge-ok  { background:#0d3326; color:#00e5a0; border:1px solid #00e5a0; }
.badge-run { background:#1a1e38; color:#5b6af0; border:1px solid #5b6af0; }
.stButton>button { background:linear-gradient(135deg,#00e5a0,#5b6af0)!important; color:#0d0f12!important; font-weight:700!important; border:none!important; border-radius:8px!important; }
.stTextInput>div>div>input { background:var(--card)!important; color:#e0e0e0!important; border:1px solid var(--border)!important; }
.stDownloadButton>button { background:var(--card)!important; color:var(--green)!important; border:1px solid var(--green)!important; border-radius:8px!important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🧪 Multi-Agent QA Code Generator</h1>
  <p>3 Specialized AI Agents &bull; Java + Selenium + TestNG &bull; 100% Free — Groq Only</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown(
        "Get a **free** Groq API key at "
        "[console.groq.com](https://console.groq.com) — no credit card needed."
    )
    groq_api_key = st.text_input(
        "Groq API Key", type="password",
        value="",
        placeholder="gsk_...",
    )
    model = st.selectbox(
        "Model (all free on Groq)",
        [
            "llama-3.3-70b-versatile",   # best quality, 30 RPM free
            "llama3-8b-8192",             # fastest, good for testing
            "gemma2-9b-it",              # Google Gemma, good alternative
        ],
        index=0,
    )
    st.markdown("---")
    include_waits  = st.checkbox("Include WebDriverWait", value=True)
    include_testng = st.checkbox("Use TestNG", value=True)
    max_elements   = st.slider("Max elements to analyse", 10, 40, 20)
    delay_secs     = st.slider(
        "Delay between agents (seconds)",
        2, 15, 5,
        help="Groq free tier: 30 req/min. Increase if you get 429 errors.",
    )
    st.markdown("---")
    st.markdown("**Free tier limits**")
    st.caption("• 30 requests / minute\n• 14,400 requests / day\n• No credit card needed")


# ── Helpers ────────────────────────────────────────────────────────────────────
def is_valid_url(url: str) -> bool:
    return bool(re.match(
        r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(:\d+)?(/[^\s]*)?$',
        url.strip()
    ))


def scrape_page(url: str, limit: int) -> str:
    """Pure requests + BS4 scraper — no Selenium, works on Streamlit Cloud."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (QA-TestBot/2.0)"},
            timeout=15,
            verify=False,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "Unknown"
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1", limit=3)]

        rows = []
        for tag in soup.find_all(
            ["input", "button", "a", "select", "textarea", "label", "form"],
            limit=limit * 2,
        ):
            keep = {
                k: (v if isinstance(v, str) else " ".join(v))
                for k, v in tag.attrs.items()
                if k in ("id", "name", "type", "class", "href",
                         "placeholder", "aria-label", "value", "action")
            }
            text = tag.get_text(strip=True)[:60]
            rows.append(f"  <{tag.name}> text='{text}' attrs={keep}")
            if len(rows) >= limit:
                break

        return (
            f"Page Title : {title}\n"
            f"H1 Tags    : {', '.join(h1s) or 'none'}\n"
            f"URL        : {url}\n\n"
            f"Interactive Elements ({len(rows)} found):\n"
            + "\n".join(rows)
        )
    except Exception as e:
        return f"Scrape error: {e}\nURL: {url}\n(Agents will work from URL only)"


def call_llm(client: Groq, model_name: str, system: str, user: str, retries: int = 3) -> str:
    """
    Calls Groq API with automatic retry on rate-limit (429).
    Returns the assistant message text.
    """
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
                st.warning(f"⏳ Rate limit hit — waiting {wait}s before retry {attempt+2}/{retries}…")
                time.sleep(wait)
            else:
                raise
    return "LLM call failed after retries."


# ── Agent definitions (pure Python functions — no crewai needed) ───────────────

def agent_element_finder(client, model_name, page_context, url, max_el):
    system = """You are a Senior QA Automation Engineer specialising in Selenium locator strategy.
Your job: analyse a web page snapshot and output a structured list of interactive elements
with the BEST Selenium locator for each (prefer ID > name > CSS selector > XPath).
Format each element as:
  [N] Tag: <tag> | Purpose: <what it does> | Locator: By.<TYPE>("value")
Be concise. Do not add preamble."""

    user = f"""Analyse this page and identify up to {max_el} critical interactive elements.

PAGE SNAPSHOT:
{page_context}

List the elements with their best Selenium locators."""
    return call_llm(client, model_name, system, user)


def agent_test_architect(client, model_name, element_analysis, url,
                         wait_instr, testng_instr):
    system = """You are a Selenium Test Architect expert in Java, Page Object Model, and TestNG.
You write clean, production-ready Java code with proper imports and package declarations.
Rules:
- Always use package com.qa.tests;
- Page class: all locators as private By fields, public action methods
- Test class: @BeforeMethod sets up ChromeDriver, @AfterMethod quits driver
- At minimum 3 @Test methods: happy path, negative/validation, boundary
- No placeholder comments like "// add your logic" — write real code
- Output TWO code blocks: first the Page class, then the Test class"""

    waits_note = (
        "Use WebDriverWait(driver, Duration.ofSeconds(10)) + ExpectedConditions for every interaction. NEVER use Thread.sleep()."
        if wait_instr else
        "Implicit waits are acceptable."
    )
    testng_note = (
        "Use TestNG: import org.testng.annotations.*; import org.testng.Assert;"
        if testng_instr else
        "Use JUnit 5: import org.junit.jupiter.api.*; import static org.junit.jupiter.api.Assertions.*;"
    )

    user = f"""Generate complete Java Selenium code for: {url}

ELEMENT ANALYSIS FROM PREVIOUS AGENT:
{element_analysis}

REQUIREMENTS:
- {waits_note}
- {testng_note}
- Use Page Object Model (POM)
- Include all required imports

Output the Page class first, then the Test class."""
    return call_llm(client, model_name, system, user)


def agent_qa_reviewer(client, model_name, raw_code, url):
    system = """You are a strict QA Lead Reviewer. You review Java Selenium code and fix ALL issues:
- Missing or wrong imports
- Thread.sleep() usage → replace with WebDriverWait
- Brittle absolute XPath → replace with ID/CSS
- Missing TestNG annotations
- Compilation errors (unclosed brackets, wrong types)
- Bad locators (text that may change)
Output ONLY the final corrected Java code. No explanation. No markdown fences around the whole output — just the code."""

    user = f"""Review and fix this Java Selenium TestNG code generated for {url}.
Output the final production-ready version:

{raw_code}"""
    return call_llm(client, model_name, system, user)


# ── Main UI ────────────────────────────────────────────────────────────────────
url_input = st.text_input(
    "🌐 Target Website URL",
    placeholder="https://example.com/login",
)

run_btn = st.button("🚀 Generate Java Selenium Tests", use_container_width=True, type="primary")

if run_btn:
    # ── Guards ──────────────────────────────────────────────────────────────────
    if not groq_api_key or not groq_api_key.startswith("gsk_"):
        st.error("❌ Enter a valid Groq API key in the sidebar (starts with `gsk_`). It's free at console.groq.com")
        st.stop()
    if not url_input or not is_valid_url(url_input):
        st.error("❌ Enter a valid URL starting with https:// or http://")
        st.stop()

    client = Groq(api_key=groq_api_key)

    # ── Step 0: Scrape ─────────────────────────────────────────────────────────
    with st.spinner("🔍 Scraping page…"):
        page_context = scrape_page(url_input, max_elements)

    with st.expander("📄 Page Snapshot (what agents see)", expanded=False):
        st.code(page_context, language="text")

    # ── Agent 1 ────────────────────────────────────────────────────────────────
    st.markdown('<div class="agent-card"><div class="agent-title">🔍 Agent 1 — Element Finder <span class="badge badge-run">RUNNING</span></div></div>', unsafe_allow_html=True)
    agent1_placeholder = st.empty()

    with st.spinner("Agent 1: Analysing page elements…"):
        try:
            a1_out = agent_element_finder(client, model, page_context, url_input, max_elements)
        except Exception as e:
            st.error(f"Agent 1 failed: {e}")
            st.stop()

    agent1_placeholder.markdown(
        f'<div class="agent-card">'
        f'<div class="agent-title">🔍 Agent 1 — Element Finder <span class="badge badge-ok">✓ DONE</span></div>'
        f'<div class="agent-out">{a1_out}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    time.sleep(delay_secs)  # respect Groq rate limit between agents

    # ── Agent 2 ────────────────────────────────────────────────────────────────
    st.markdown('<div class="agent-card"><div class="agent-title">☕ Agent 2 — Test Architect <span class="badge badge-run">RUNNING</span></div></div>', unsafe_allow_html=True)
    agent2_placeholder = st.empty()

    wait_instr   = include_waits
    testng_instr = include_testng

    with st.spinner("Agent 2: Writing Java Selenium + TestNG code…"):
        try:
            a2_out = agent_test_architect(
                client, model, a1_out, url_input, wait_instr, testng_instr
            )
        except Exception as e:
            st.error(f"Agent 2 failed: {e}")
            st.stop()

    agent2_placeholder.markdown(
        f'<div class="agent-card">'
        f'<div class="agent-title">☕ Agent 2 — Test Architect <span class="badge badge-ok">✓ DONE</span></div>'
        f'<div class="agent-out">{a2_out[:800]}{"…(truncated in preview)" if len(a2_out)>800 else ""}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    time.sleep(delay_secs)

    # ── Agent 3 ────────────────────────────────────────────────────────────────
    st.markdown('<div class="agent-card"><div class="agent-title">🔎 Agent 3 — QA Reviewer <span class="badge badge-run">RUNNING</span></div></div>', unsafe_allow_html=True)
    agent3_placeholder = st.empty()

    with st.spinner("Agent 3: Reviewing and polishing code…"):
        try:
            a3_out = agent_qa_reviewer(client, model, a2_out, url_input)
        except Exception as e:
            st.error(f"Agent 3 failed: {e}")
            st.stop()

    agent3_placeholder.markdown(
        f'<div class="agent-card">'
        f'<div class="agent-title">🔎 Agent 3 — QA Reviewer <span class="badge badge-ok">✓ DONE</span></div>'
        f'<div class="agent-out">Code reviewed and polished ✓</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Output tabs ────────────────────────────────────────────────────────────
    st.success("✅ All 3 Agents Completed!")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["☕ Final Java Code", "🔍 Element Analysis", "📋 Raw Draft"])

    with tab1:
        st.markdown("### Production-Ready Java Selenium TestNG Code")
        st.code(a3_out, language="java")
        st.download_button(
            "⬇️ Download Java Code",
            data=a3_out,
            file_name="SeleniumTestNG_Generated.java",
            mime="text/plain",
        )

    with tab2:
        st.markdown("### Element Analysis (Agent 1 Output)")
        st.text_area("Elements", value=a1_out, height=300)

    with tab3:
        st.markdown("### Raw Draft Code (Agent 2 Output — before review)")
        st.code(a2_out, language="java")

else:
    # Landing state
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="agent-card">
          <div class="agent-title">🔍 Agent 1 — Element Finder</div>
          <p style="color:#888;font-size:.85rem;">Scrapes the page and identifies all interactive elements with the best Selenium locator strategy (ID → name → CSS → XPath).</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="agent-card">
          <div class="agent-title">☕ Agent 2 — Test Architect</div>
          <p style="color:#888;font-size:.85rem;">Generates complete Java Selenium + TestNG code using Page Object Model. Writes Page class + Test class with real test scenarios.</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agent-card">
          <div class="agent-title">🔎 Agent 3 — QA Reviewer</div>
          <p style="color:#888;font-size:.85rem;">Reviews the generated code for broken imports, brittle locators, missing annotations, and Thread.sleep abuse. Outputs the final polished version.</p>
        </div>""", unsafe_allow_html=True)

    st.info("👆 Add your **free Groq API key** in the sidebar and enter a URL above to start.")

st.caption("Built with Groq (free) · BeautifulSoup · Streamlit · Zero paid dependencies")
