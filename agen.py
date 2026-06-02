import streamlit as st
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any
import asyncio

# Crawling
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import requests
from bs4 import BeautifulSoup
import re

# LLM
from groq import Groq

# For Playwright support in Crawl4AI
import nest_asyncio
nest_asyncio.apply()

st.set_page_config(page_title="AI QA Agent - Test Case Generator", layout="wide")
st.title("🧪 AI QA Automation Architect")
st.markdown("**Fully automated website testing agent** — Crawl → Analyze → Generate Test Cases → Export")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("Configuration")
    
    target_url = st.text_input("Target URL", value="https://example.com", placeholder="https://example.com")
    
    col1, col2 = st.columns(2)
    with col1:
        max_depth = st.number_input("Max Depth", min_value=1, max_value=3, value=2)
    with col2:
        llm_provider = st.selectbox("LLM Provider", ["groq"], disabled=True)
    
    username = st.text_input("Username (optional)", value="")
    password = st.text_input("Password (optional)", value="", type="password")
    
    focus_modules = st.multiselect(
        "Modules to Focus",
        ["Authentication", "Forms", "Navigation", "Search", "Checkout", "Dashboard", "API"],
        default=[]
    )
    
    if st.button("🚀 Start Analysis", type="primary"):
        st.session_state.run_analysis = True
        st.session_state.target_url = target_url
        st.session_state.max_depth = max_depth
        st.session_state.auth = {"username": username, "password": password} if username else None
        st.session_state.focus_modules = focus_modules

# ====================== LLM CLIENT ======================
@st.cache_resource
def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

client = get_groq_client()

def call_llm(prompt: str, temperature=0.3) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # or llama3-70b-8192
            messages=[{"role": "system", "content": "You are a senior QA automation architect."},
                      {"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=8000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"LLM Error: {e}")
        return ""

# ====================== CRAWLING ======================
async def crawl_website(url: str, max_depth: int):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            max_depth=max_depth,
            include_links=True,
            include_raw_html=False,
            verbose=True,
        )
        return result

def extract_sitemap(crawl_result):
    # Simplified for demo
    pages = []
    if hasattr(crawl_result, 'urls'):
        for url in crawl_result.urls[:15]:  # Limit for performance
            pages.append({
                "title": f"Page at {url}",
                "url": url,
                "interactive_elements": ["buttons", "forms", "links"],
                "tech_stack": "Unknown"
            })
    return {"pages": pages, "base_url": crawl_result.url if hasattr(crawl_result, 'url') else ""}

# ====================== TEST CASE GENERATION ======================
def generate_test_cases(sitemap: Dict, scope: Dict) -> List[Dict]:
    prompt = f"""
You are a senior QA engineer. Generate comprehensive test cases based on the following:

Sitemap: {json.dumps(sitemap, indent=2)}
Scope: {json.dumps(scope, indent=2)}

Rules:
- Minimum 5 test cases per major page/module
- At least 30% Negative test cases
- At least 20% Boundary test cases
- Use exact format with fields: Test Case ID, Test Suite, Title, Preconditions, Test Steps, Test Data, Expected Result, Priority, Test Type, Automation Candidate
- Make every step atomic and executable
- Use concrete test data

Return valid JSON array of test case objects.
"""

    response = call_llm(prompt, temperature=0.2)
    try:
        # Extract JSON
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            st.warning("LLM did not return clean JSON. Using fallback.")
            return []
    except:
        st.error("Failed to parse test cases JSON")
        return []

# ====================== MAIN PIPELINE ======================
if st.session_state.get('run_analysis', False):
    with st.spinner("Crawling website..."):
        try:
            crawl_result = asyncio.run(crawl_website(st.session_state.target_url, st.session_state.max_depth))
            sitemap = extract_sitemap(crawl_result)
            st.success(f"Crawled {len(sitemap.get('pages', []))} pages")
            st.json(sitemap, expanded=False)
        except Exception as e:
            st.error(f"Crawling failed: {e}")
            sitemap = {"pages": []}

    # Scope Analysis
    with st.spinner("Analyzing scope..."):
        scope_prompt = f"Analyze this sitemap and create scope JSON with modules, risk levels, test types: {json.dumps(sitemap)}"
        scope_text = call_llm(scope_prompt)
        try:
            scope = json.loads(scope_text)
        except:
            scope = {"modules": ["General"], "risk_levels": {}}

        st.subheader("📋 Scope Analysis")
        st.json(scope, expanded=False)

    # Test Case Generation
    with st.spinner("Generating test cases using Groq Llama-3.3-70B..."):
        test_cases = generate_test_cases(sitemap, scope)
        
        if test_cases:
            st.success(f"✅ Generated {len(test_cases)} test cases")
            
            df = st.dataframe(
                [{k: v for k, v in tc.items() if k not in ['Actual Result', 'Status']} for tc in test_cases],
                use_container_width=True
            )
            
            # Export
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV Export (Jira Xray compatible)
                csv_data = []
                headers = ["Issue Type", "Summary", "Description", "Priority", "Labels", "Test Type", "Step", "Step Data", "Step Result"]
                csv_data.append(headers)
                
                for tc in test_cases:
                    row = [
                        "Test",
                        tc.get("Test Case Title", ""),
                        f"Pre: {tc.get('Preconditions', '')}\nSteps:\n{tc.get('Test Steps', '')}",
                        tc.get("Priority", "Medium"),
                        "AI_Generated",
                        tc.get("Test Type", "Functional"),
                        "1",  # Simplified
                        tc.get("Test Data", ""),
                        tc.get("Expected Result", "")
                    ]
                    csv_data.append(row)
                
                csv_str = "\n".join([",".join([str(item).replace(",", ";") for item in row]) for row in csv_data])
                
                st.download_button(
                    "📥 Download CSV (Jira Xray)",
                    csv_str,
                    file_name=f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # JSON Export (TestRail compatible)
                json_export = {
                    "project_id": 1,
                    "suite_id": 1,
                    "cases": test_cases
                }
                st.download_button(
                    "📥 Download JSON (TestRail)",
                    json.dumps(json_export, indent=2),
                    file_name=f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )

            # Show sample test cases
            st.subheader("Sample Test Cases")
            for tc in test_cases[:5]:
                with st.expander(tc.get("Test Case Title", "Untitled")):
                    st.write(tc)

st.info("💡 **Pro Tip**: Get your free Groq API key from https://console.groq.com and set it as `GROQ_API_KEY` environment variable.")
