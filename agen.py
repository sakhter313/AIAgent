import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urlparse

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QA Agent — Element Finder & Test Generator",
    page_icon="🧪",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg: #0d0f12;
    --surface: #141720;
    --surface2: #1c2030;
    --border: #2a2f45;
    --accent: #00e5a0;
    --accent2: #5b6af0;
    --warn: #f0a05b;
    --text: #e2e8f0;
    --muted: #6b7280;
    --code-bg: #0a0c0f;
}

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

/* Hero header */
.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem;
}
.hero p {
    color: var(--muted);
    font-size: 1rem;
    margin: 0;
    font-family: 'JetBrains Mono', monospace;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, #00b87a 100%) !important;
    color: #0d0f12 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    width: 100%;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,229,160,0.3) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent2) !important;
    color: white !important;
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
}
.tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 4px;
}
.tag-p1 { background: rgba(240,80,80,0.15); color: #f05050; border: 1px solid rgba(240,80,80,0.3); }
.tag-p2 { background: rgba(240,160,91,0.15); color: var(--warn); border: 1px solid rgba(240,160,91,0.3); }
.tag-p3 { background: rgba(91,106,240,0.15); color: var(--accent2); border: 1px solid rgba(91,106,240,0.3); }
.tag-p4 { background: rgba(0,229,160,0.15); color: var(--accent); border: 1px solid rgba(0,229,160,0.3); }

/* Code blocks */
.code-block {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre;
    color: #c9d1e0;
}

/* Stat chips */
.stat-row { display: flex; gap: 12px; margin-bottom: 1rem; flex-wrap: wrap; }
.stat-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
}
.stat-chip span { color: var(--accent); font-weight: 700; }

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
}

/* Alert */
.info-box {
    background: rgba(91,106,240,0.1);
    border: 1px solid rgba(91,106,240,0.3);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    font-size: 0.85rem;
    color: #a5b0ff;
    margin-bottom: 1rem;
}

.success-box {
    background: rgba(0,229,160,0.08);
    border: 1px solid rgba(0,229,160,0.25);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    font-size: 0.85rem;
    color: var(--accent);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧪 QA Agent</h1>
    <p>Element Finder &amp; Selenium Test Case Generator · Groq LLM · Java Output</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.markdown("---")
    st.markdown("**Model**")
    model_choice = st.selectbox("", [
        "llama-3.3-70b-versatile",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Options**")
    include_waits = st.checkbox("Include WebDriverWait", value=True)
    include_testng = st.checkbox("Include TestNG annotations", value=True)
    max_elements = st.slider("Max elements to analyse", 10, 60, 30)
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.78rem; color: #6b7280; font-family: JetBrains Mono, monospace;'>
    🔑 Get free Groq key:<br>
    <a href='https://console.groq.com' target='_blank' style='color:#00e5a0;'>console.groq.com</a>
    </div>
    """, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def scrape_page(url: str) -> dict:
    """Scrape a webpage and extract elements with their locators."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    elements = []
    tags_to_scan = ["input", "button", "a", "select", "textarea", "form",
                    "h1","h2","h3","label","img","table","nav","header","footer"]

    for tag in soup.find_all(tags_to_scan):
        el = {
            "tag": tag.name,
            "id": tag.get("id", ""),
            "name": tag.get("name", ""),
            "class": " ".join(tag.get("class", [])),
            "type": tag.get("type", ""),
            "placeholder": tag.get("placeholder", ""),
            "text": tag.get_text(strip=True)[:60],
            "href": tag.get("href", ""),
            "aria_label": tag.get("aria-label", ""),
            "data_testid": tag.get("data-testid", ""),
            "role": tag.get("role", ""),
        }
        elements.append(el)

    page_title = soup.title.string if soup.title else "Unknown"
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta_desc = meta.get("content", "")

    return {
        "title": page_title,
        "url": url,
        "meta_description": meta_desc,
        "elements": elements,
        "total_elements": len(elements),
    }


def call_groq(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Call Groq API directly via requests."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_elements_prompt(page_data: dict, max_el: int) -> tuple[str, str]:
    elements_json = json.dumps(page_data["elements"][:max_el], indent=2)
    system = (
        "You are a Senior QA Automation Engineer specialising in Selenium WebDriver with Java. "
        "You analyse web page elements and produce precise, production-ready locators."
    )
    user = f"""
Analyse the following web page elements scraped from: {page_data['url']}
Page Title: {page_data['title']}

ELEMENTS (JSON):
{elements_json}

For EACH meaningful interactive element (inputs, buttons, links, selects, textareas):
1. Give the element a descriptive name
2. Provide ALL applicable locators ranked by priority:
   - 🥇 P1 - ID (most stable)
   - 🥈 P2 - Name attribute
   - 🥉 P3 - CSS Selector
   - 🏅 P4 - XPath (relative, robust)
3. Indicate which locator to USE (the highest priority available)

Output as valid JSON array:
[
  {{
    "element_name": "Username Input Field",
    "element_type": "input",
    "locators": {{
      "id": "By.id(\\"username\\")",
      "name": "By.name(\\"username\\")",
      "css": "By.cssSelector(\\"input[name='username']\\")",
      "xpath": "By.xpath(\\"//input[@name='username']\\")"
    }},
    "recommended": "id",
    "java_variable": "usernameInput"
  }}
]

Only output valid JSON. No markdown fences, no explanation text.
"""
    return system, user


def build_testcases_prompt(page_data: dict, elements_result: str, include_waits: bool, include_testng: bool) -> tuple[str, str]:
    system = (
        "You are a Senior QA Automation Engineer. "
        "You write production-grade Selenium WebDriver test cases in Java with TestNG and Page Object Model."
    )
    waits_note = "Use WebDriverWait with ExpectedConditions for all element interactions." if include_waits else "Use Thread.sleep sparingly only where essential."
    testng_note = "Annotate with @Test, @BeforeClass, @AfterClass from TestNG." if include_testng else "Use plain Java main method."

    user = f"""
You are writing Selenium Java test cases for this website:
URL: {page_data['url']}
Page: {page_data['title']}
Description: {page_data['meta_description']}

Extracted elements (for context):
{elements_result[:2000]}

Generate comprehensive Selenium Java test cases covering:
1. Page load & title verification
2. All interactive elements (visibility, clickability)
3. Form validation (valid input, invalid input, empty fields)
4. Navigation / link tests
5. At least 2 negative test cases
6. At least 1 edge case

Rules:
- {waits_note}
- {testng_note}
- Use Page Object Model style
- Use the locators from the element analysis above
- Include meaningful assertions

Provide:
A) A PageObject Java class (e.g. LoginPage.java or HomePage.java)
B) A Test class (e.g. LoginPageTest.java)

Format as clean Java code blocks labelled clearly.
"""
    return system, user


def parse_elements_json(raw: str) -> list:
    """Try to parse LLM JSON output safely."""
    raw = raw.strip()
    # Strip markdown fences if present
    raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` \n")
    try:
        return json.loads(raw)
    except Exception:
        # Find JSON array
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return []


# ── Main UI ───────────────────────────────────────────────────────────────────
url_input = st.text_input(
    "🌐 Enter Website URL",
    placeholder="https://example.com/login",
    help="Paste any public website URL"
)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    run_btn = st.button("🚀 Run QA Agent", use_container_width=True)
with col2:
    st.markdown("")
with col3:
    st.markdown("")

if run_btn:
    if not groq_api_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar.")
        st.stop()
    if not url_input:
        st.error("⚠️ Please enter a website URL.")
        st.stop()

    # Validate URL
    parsed = urlparse(url_input)
    if not parsed.scheme or not parsed.netloc:
        st.error("⚠️ Invalid URL. Include http:// or https://")
        st.stop()

    # ── Step 1: Scrape ──────────────────────────────────────────────────────
    with st.spinner("🕷️ Scraping page elements..."):
        try:
            page_data = scrape_page(url_input)
        except Exception as e:
            st.error(f"❌ Failed to scrape URL: {e}")
            st.stop()

    st.markdown(f"""
    <div class='success-box'>
    ✅ Scraped <strong>{page_data['title']}</strong> — found <strong>{page_data['total_elements']}</strong> elements
    </div>
    """, unsafe_allow_html=True)

    # ── Step 2: Element Analysis via Groq ───────────────────────────────────
    with st.spinner("🤖 AI analysing elements & generating locators..."):
        try:
            sys_p, usr_p = build_elements_prompt(page_data, max_elements)
            elements_raw = call_groq(groq_api_key, model_choice, sys_p, usr_p)
            elements_parsed = parse_elements_json(elements_raw)
        except Exception as e:
            st.error(f"❌ Groq API error (elements): {e}")
            st.stop()

    # ── Step 3: Test Case Generation ────────────────────────────────────────
    with st.spinner("🧪 Generating Selenium Java test cases..."):
        try:
            sys_p2, usr_p2 = build_testcases_prompt(page_data, elements_raw, include_waits, include_testng)
            test_cases_raw = call_groq(groq_api_key, model_choice, sys_p2, usr_p2)
        except Exception as e:
            st.error(f"❌ Groq API error (test cases): {e}")
            st.stop()

    # ── Display Results ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='stat-row'>
        <div class='stat-chip'>Page: <span>{page_data['title'][:40]}</span></div>
        <div class='stat-chip'>Elements scraped: <span>{page_data['total_elements']}</span></div>
        <div class='stat-chip'>Analysed: <span>{len(elements_parsed) if elements_parsed else "—"}</span></div>
        <div class='stat-chip'>Model: <span>{model_choice.split("-")[0]}</span></div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Element Finder", "☕ Selenium Java Tests", "📄 Raw Scraped Data"])

    # ── Tab 1: Elements ──────────────────────────────────────────────────────
    with tab1:
        if elements_parsed:
            for el in elements_parsed:
                locs = el.get("locators", {})
                recommended = el.get("recommended", "")

                priority_map = {"id": ("P1", "tag-p1"), "name": ("P2", "tag-p2"),
                                "css": ("P3", "tag-p3"), "xpath": ("P4", "tag-p4")}
                rec_label, rec_cls = priority_map.get(recommended, ("—", "tag-p4"))

                locator_rows = ""
                for key, label_cls in priority_map.items():
                    val = locs.get(key, "")
                    if val:
                        badge = f"<span class='tag {label_cls[1]}'>{label_cls[0]}</span>"
                        star = " ⭐" if key == recommended else ""
                        locator_rows += f"<div style='margin-bottom:6px;'>{badge} <code style='font-size:0.8rem;color:#c9d1e0;'>{val}</code>{star}</div>"

                java_var = el.get("java_variable", "element")
                st.markdown(f"""
                <div class='card'>
                    <div class='card-title'>{el.get('element_type','').upper()} · {el.get('element_name','Unknown')}</div>
                    {locator_rows}
                    <div style='margin-top:8px; font-size:0.78rem; color:#6b7280; font-family:JetBrains Mono,monospace;'>
                        Java variable: <span style='color:#5b6af0;'>WebElement</span> <span style='color:#00e5a0;'>{java_var}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='card'>
                <div class='card-title'>RAW LLM OUTPUT</div>
                <div class='code-block'>{elements_raw[:3000]}</div>
            </div>
            """, unsafe_allow_html=True)

        # Download elements as JSON
        st.download_button(
            "⬇️ Download Elements JSON",
            data=json.dumps(elements_parsed, indent=2) if elements_parsed else elements_raw,
            file_name="elements_locators.json",
            mime="application/json"
        )

    # ── Tab 2: Test Cases ────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"""
        <div class='info-box'>
        💡 Generated for: <strong>{url_input}</strong> · Language: Java · Framework: Selenium + TestNG
        </div>
        """, unsafe_allow_html=True)

        # Split by Java class sections
        sections = re.split(r"(?=(?:public class|// (?:A\)|B\)|PageObject|Test Class)))", test_cases_raw)
        for section in sections:
            if section.strip():
                st.markdown(f"<div class='code-block'>{section.strip()}</div>", unsafe_allow_html=True)
                st.markdown("")

        st.download_button(
            "⬇️ Download Java Test Code",
            data=test_cases_raw,
            file_name="SeleniumTests.java",
            mime="text/plain"
        )

    # ── Tab 3: Raw Data ──────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div class='card-title'>SCRAPED ELEMENTS (RAW)</div>", unsafe_allow_html=True)
        with st.expander(f"View all {page_data['total_elements']} scraped elements"):
            st.json(page_data["elements"][:max_elements])

else:
    # Landing state
    st.markdown("""
    <div style='text-align:center; padding: 3rem 1rem; color: #6b7280;'>
        <div style='font-size:3rem; margin-bottom:1rem;'>🔎</div>
        <div style='font-family: JetBrains Mono, monospace; font-size:0.9rem; margin-bottom:0.5rem; color:#2a2f45;'>
        ─────────────────────────────────
        </div>
        <div style='font-size:0.95rem; margin-bottom:0.4rem;'>Enter a URL · Configure your Groq key · Hit Run</div>
        <div style='font-size:0.82rem; color:#4a5568;'>The agent will scrape, analyse, and generate Java Selenium tests automatically.</div>
        <div style='font-family: JetBrains Mono, monospace; font-size:0.9rem; margin-top:0.5rem; color:#2a2f45;'>
        ─────────────────────────────────
        </div>
    </div>

    <div style='display:flex; gap:1rem; margin-top:1.5rem; flex-wrap:wrap;'>
        <div class='card' style='flex:1; min-width:200px;'>
            <div class='card-title'>Step 1</div>
            <div style='font-size:0.9rem;'>🕷️ Scrapes the URL and extracts all interactive elements</div>
        </div>
        <div class='card' style='flex:1; min-width:200px;'>
            <div class='card-title'>Step 2</div>
            <div style='font-size:0.9rem;'>🤖 AI ranks locators — ID → Name → CSS → XPath</div>
        </div>
        <div class='card' style='flex:1; min-width:200px;'>
            <div class='card-title'>Step 3</div>
            <div style='font-size:0.9rem;'>☕ Generates Java Selenium + TestNG test cases with POM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
