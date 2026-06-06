import streamlit as st
import os
import re
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool

load_dotenv()

st.set_page_config(
    page_title="CrewAI QA Agent — Java Selenium TestNG",
    page_icon="🧪",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');
:root {
    --bg: #0d0f12; --surface: #141720; --accent: #00e5a0; --accent2: #5b6af0;
}
html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: var(--bg) !important; color: #e0e0e0 !important; }
#MainMenu, footer, header { visibility: hidden; }
.hero { text-align: center; padding: 2rem; border-bottom: 1px solid #2a2f45; }
.hero h1 { font-size: 2.6rem; background: linear-gradient(135deg, #00e5a0, #5b6af0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.card { background: #141720; border: 1px solid #2a2f45; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; }
.code-block { background: #0a0c0f; border-left: 4px solid #5b6af0; padding: 1rem; border-radius: 8px; font-family: 'JetBrains Mono', monospace; overflow-x: auto; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🧪 CrewAI QA Agent</h1>
    <p>Multi-Agent System • Java + Selenium + TestNG • Production Grade</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    groq_api_key = st.text_input(
        "Groq API Key", type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        placeholder="gsk_..."
    )
    model = st.selectbox(
        "LLM Model",
        ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"],
        index=0
    )
    st.markdown("---")
    include_waits  = st.checkbox("Include WebDriverWait", value=True)
    include_testng = st.checkbox("Use TestNG", value=True)
    max_elements   = st.slider("Analysis Depth", 15, 50, 25)
    # FIX 8 ── expose RPM control so users can stay within Groq free-tier limits
    max_rpm = st.slider("Max Requests/Min (Groq rate limit)", 5, 30, 10)


# ── URL validation helper ──────────────────────────────────────────────────────
def is_valid_url(url: str) -> bool:
    """FIX 5 ── validate URL format before sending to agents."""
    pattern = re.compile(
        r'^(https?://)'                      # scheme required
        r'([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,})'  # domain
        r'(:\d+)?'                            # optional port
        r'(/[^\s]*)?$'                        # optional path
    )
    return bool(pattern.match(url.strip()))


# ── Agent factory ──────────────────────────────────────────────────────────────
# FIX 1 ── removed @st.cache_resource so agents are always rebuilt with the
#           current API key / model selection from the sidebar. Caching here
#           meant a new key entered mid-session was silently ignored.
def create_crew_agents(api_key: str, model_name: str, rpm: int):
    os.environ["GROQ_API_KEY"] = api_key
    scrape_tool = ScrapeWebsiteTool()

    groq_llm = LLM(
        model=f"groq/{model_name}",
        api_key=api_key,
        max_rpm=rpm,       # FIX 8 ── respect Groq free-tier rate limits
    )

    element_finder = Agent(
        role="Senior QA Automation Engineer - Locator Expert",
        goal="Discover and prioritize the best locators (ID > Name > CSS > XPath) for all interactive elements.",
        backstory="12+ years in automation. Expert in robust locator strategies for dynamic UIs.",
        tools=[scrape_tool],
        verbose=True,
        llm=groq_llm,
    )

    test_architect = Agent(
        role="Selenium Test Architect",
        goal="Generate clean, maintainable Java Selenium + TestNG tests using Page Object Model.",
        backstory="Expert in writing production-grade test automation frameworks.",
        verbose=True,
        llm=groq_llm,
    )

    qa_reviewer = Agent(
        role="QA Lead Reviewer",
        goal="Review and improve test quality, reliability, and best practices.",
        backstory="Strict QA leader focused on maintainability and robustness.",
        verbose=True,
        llm=groq_llm,
    )

    return element_finder, test_architect, qa_reviewer


# ── Main UI ────────────────────────────────────────────────────────────────────
url_input = st.text_input("🌐 Enter Website URL", placeholder="https://example.com/login")

# FIX 6 ── removed the unused col2 column; a single centred button is cleaner
run_btn = st.button("🚀 Run CrewAI QA Agents", use_container_width=True, type="primary")

if run_btn:
    # ── Input guards ───────────────────────────────────────────────────────────
    if not groq_api_key:
        st.error("Please provide your Groq API Key in the sidebar.")
        st.stop()

    # FIX 5 ── validate URL before calling the crew
    if not url_input or not is_valid_url(url_input):
        st.error("Please enter a valid URL starting with http:// or https://")
        st.stop()

    # ── Build agents ───────────────────────────────────────────────────────────
    with st.spinner("🔄 Initialising CrewAI Agents..."):
        element_finder, test_architect, qa_reviewer = create_crew_agents(
            groq_api_key, model, max_rpm
        )

    # FIX 2 & 7 ── define all tasks together, BEFORE kickoff; spinners around
    #              task *definition* (not execution) were misleading — moved the
    #              single progress spinner to wrap the actual crew.kickoff() call.
    #              Also removed the redundant inputs={"url": url_input} from
    #              kickoff() because the URL is already embedded in task
    #              descriptions. Passing it as a template variable only helps
    #              when descriptions use {url} placeholders.
    wait_instruction = (
        "Include explicit WebDriverWait commands."
        if include_waits else
        "Do not prioritise explicit waits."
    )
    testng_instruction = (
        "Use TestNG annotations: @Test, @BeforeMethod, @AfterMethod, and TestNG Assertions."
        if include_testng else
        "Write using standard JUnit 5 / Java main framework."
    )

    task1 = Task(
        description=(
            f"Scrape and analyse {url_input}. "
            f"Provide detailed element analysis with best locators. "
            f"Analyse up to {max_elements} critical elements."
        ),
        agent=element_finder,
        expected_output="Structured element analysis with recommended locators.",
    )

    task2 = Task(
        description=(
            f"Generate complete Java Selenium code for {url_input}. "
            "Use the Page Object Model (POM) architecture. "
            "Include separate code blocks for the Page class and the Test class. "
            "Cover positive paths, negative test assertions, and boundary checks. "
            f"{wait_instruction} "
            f"{testng_instruction}"
        ),
        agent=test_architect,
        context=[task1],           # task1 output is passed as context
        expected_output="Full Java code structured into Page Object and Test classes.",
    )

    task3 = Task(
        description=(
            "Review the generated Java infrastructure for syntax accuracy, "
            "formatting cleanliness, locator robustness, and architectural soundness. "
            "Output the finalised, production-ready source text."
        ),
        agent=qa_reviewer,
        context=[task2],           # task2 output is passed as context
        expected_output="Final polished Java Selenium TestNG production-ready source code.",
    )

    crew = Crew(
        agents=[element_finder, test_architect, qa_reviewer],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=True,
    )

    # ── Execute ────────────────────────────────────────────────────────────────
    with st.spinner("🤖 Running Multi-Agent Crew… (30–90 seconds depending on page complexity)"):
        try:
            # FIX 7 ── no inputs={} here; URL is already in task descriptions
            result = crew.kickoff()

            st.success("✅ CrewAI Agents Completed Successfully!")

            # FIX 3 ── use result.raw for clean string access instead of str(result)
            #          which can include CrewOutput repr noise
            output_text = result.raw if hasattr(result, "raw") else str(result)

            tab1, tab2 = st.tabs(["📋 Full Output", "☕ Java Test Code"])

            with tab1:
                st.markdown("### Agent Execution Result")
                st.text_area("Output", value=output_text, height=450)

            with tab2:
                st.markdown("### Final Java + Selenium Framework Package")
                st.code(output_text, language="java")
                st.download_button(
                    label="⬇️ Download Java Test Files",
                    data=output_text,
                    file_name="Selenium_TestNG_Tests.java",
                    mime="text/plain",
                )

        except Exception as e:
            st.error(f"CrewAI execution error: {e}")
            st.info(
                "💡 If you hit a Groq rate limit (429), lower **Max Requests/Min** "
                "in the sidebar and try again."
            )

else:
    st.info("Enter a URL and click **Run CrewAI QA Agents** to start the multi-agent workflow.")

st.caption("Built with CrewAI • Groq • Java Selenium TestNG")
