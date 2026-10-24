import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from utils.data_processor import preprocess_and_save, get_dataset_summary

# ==========================================
# Page Configuration & Styling
# ==========================================
st.set_page_config(
    page_title="AI Data Analyst Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .sample-pill {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 6px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# Sidebar Configuration
# ==========================================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg",
        width=40,
    )
    st.title("Agent Settings")
    st.markdown("Configure LLM backend, model provider, and dataset options.")

    st.subheader("1. LLM Provider")
    provider = st.radio(
        "Choose Model Provider:",
        options=["OpenAI", "Google Gemini"],
        index=0,
        help="Select which AI foundation model powers your data analysis queries.",
    )

    if provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        selected_model = st.selectbox("Select OpenAI Model:", model_options, index=0)

        env_openai_key = os.getenv("OPENAI_API_KEY", "")
        openai_key = st.text_input(
            "OpenAI API Key:",
            value=env_openai_key,
            type="password",
            help="Your API key stays safe in memory and is never permanently stored.",
        )
        if openai_key:
            st.session_state.openai_key = openai_key
            st.success("OpenAI API Key active")
        else:
            st.warning("Please provide your OpenAI API key to proceed.")

    else:  # Google Gemini
        model_options = [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
        ]
        selected_model = st.selectbox("Select Gemini Model:", model_options, index=0)

        env_gemini_key = os.getenv("GEMINI_API_KEY", "")
        gemini_key = st.text_input(
            "Gemini API Key:",
            value=env_gemini_key,
            type="password",
            help="Your API key stays safe in memory and is never permanently stored.",
        )
        if gemini_key:
            st.session_state.gemini_key = gemini_key
            st.success("Gemini API Key active")
        else:
            st.warning("Please provide your Gemini API key to proceed.")

    st.divider()
    st.subheader("2. Quick Demo Dataset")
    use_demo = st.button("📂 Load Sales Sample Dataset", use_container_width=True)
    if use_demo:
        sample_path = os.path.join(
            os.path.dirname(__file__), "sample_data", "sales_performance_data.csv"
        )
        if os.path.exists(sample_path):
            st.session_state.demo_dataset_path = sample_path
            st.session_state.is_demo_loaded = True
            st.success("Loaded 'sales_performance_data.csv'!")
        else:
            st.error("Sample dataset file not found.")

    st.markdown("---")
    st.caption("Built with [Agno](https://agno.com) • [DuckDB](https://duckdb.org) • Streamlit")

# ==========================================
# Main Layout & Header
# ==========================================
st.markdown('<div class="main-header">📊 Autonomous AI Data Analyst Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Query structured CSV and Excel datasets with natural language. Powered by DuckDB OLAP and Agno Multi-Tool Agents.</div>',
    unsafe_allow_html=True,
)

# File uploader
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel dataset to begin analysis:",
    type=["csv", "xlsx", "xls"],
    help="Upload sales records, marketing metrics, financial ledgers, or customer datasets.",
)

# Active data source determination
active_source = None
if uploaded_file is not None:
    active_source = uploaded_file
    st.session_state.is_demo_loaded = False
elif st.session_state.get("is_demo_loaded", False) and "demo_dataset_path" in st.session_state:
    active_source = st.session_state.demo_dataset_path

# Check credentials readiness
has_credentials = (
    (provider == "OpenAI" and "openai_key" in st.session_state and st.session_state.openai_key)
    or (provider == "Google Gemini" and "gemini_key" in st.session_state and st.session_state.gemini_key)
)

if active_source is not None:
    with st.spinner("Sanitizing and loading dataset into in-memory DuckDB..."):
        temp_path, columns, df = preprocess_and_save(active_source)

    if temp_path and columns and df is not None:
        # Display dataset KPI metrics
        summary = get_dataset_summary(df)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Rows", f"{summary['rows']:,}")
        m2.metric("Total Columns", f"{summary['columns']}")
        m3.metric("Missing Values", f"{summary['missing_percentage']}%")
        m4.metric("Numeric Fields", f"{summary['numeric_cols']}")
        m5.metric("Est. Memory", f"{summary['memory_mb']} MB")

        # Dataset inspection tabs
        tab1, tab2, tab3 = st.tabs(["📋 Data Preview", "📈 Descriptive Statistics", "🔍 Schema & Data Types"])
        with tab1:
            st.dataframe(df.head(100), use_container_width=True)
        with tab2:
            st.dataframe(df.describe(include="all").transpose(), use_container_width=True)
        with tab3:
            dtypes_df = pd.DataFrame(
                {"Column Name": df.columns, "Data Type": [str(t) for t in df.dtypes], "Non-Null Count": df.notnull().sum().values}
            )
            st.dataframe(dtypes_df, use_container_width=True)

        st.divider()

        # Query Interface
        st.subheader("💬 Ask Any Analytical Question")
        st.markdown(
            "The agent translates your question into **DuckDB SQL**, queries the in-memory engine, and computes rigorous answers with statistical insights."
        )

        # Quick Suggestion Chips
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        selected_prompt = None
        if col_s1.button("🏆 Top 5 Revenue Generators"):
            selected_prompt = "What are the top 5 records or categories by Total_Revenue?"
        if col_s2.button("📊 Regional Performance Breakdown"):
            selected_prompt = "Provide a comprehensive breakdown of revenue, average transaction value, and volume by Region."
        if col_s3.button("💳 Payment Method Comparison"):
            selected_prompt = "Compare transaction count and average satisfaction score across different payment methods."
        if col_s4.button("📉 Outlier & Anomaly Analysis"):
            selected_prompt = "Identify any notable outliers or anomalies in quantity, discounts, or revenues."

        query_input = st.text_area(
            "Enter your query:",
            value=selected_prompt if selected_prompt else "",
            placeholder="e.g., What is the total revenue by product category, and which one has the highest profit margin?",
            height=100,
        )

        submit_btn = st.button("🚀 Analyze Dataset", type="primary", use_container_width=True)

        if submit_btn:
            if not has_credentials:
                st.error(f"Please configure your {provider} API key in the sidebar before querying.")
            elif not query_input.strip():
                st.warning("Please enter a question or select a quick query chip.")
            else:
                try:
                    with st.spinner("🤖 Agent is analyzing schema, generating SQL, and computing insights..."):
                        # Initialize DuckDB tool and load table
                        duckdb_tools = DuckDbTools()
                        duckdb_tools.load_local_csv_to_table(
                            path=temp_path,
                            table="uploaded_data",
                        )

                        # Configure Model
                        if provider == "OpenAI":
                            model_instance = OpenAIChat(
                                id=selected_model,
                                api_key=st.session_state.openai_key,
                            )
                        else:
                            model_instance = Gemini(
                                id=selected_model,
                                api_key=st.session_state.gemini_key,
                            )

                        # System Prompt for the Analyst Agent
                        system_prompt = (
                            "You are an expert Data Analyst and Analytics Engineer. "
                            "You have access to the 'uploaded_data' table in DuckDB representing the user's dataset. "
                            "Use the DuckDbTools to inspect table schema and execute precise SQL queries. "
                            "Use PandasTools if custom mathematical calculations or transformations are needed. "
                            "Always present your findings clearly with: "
                            "1. Direct Answer & Executive Summary "
                            "2. Analytical Table or Metrics (using Markdown tables) "
                            "3. Key Business Insights and Trends "
                            "4. The exact SQL query executed for transparency."
                        )

                        # Initialize Agno Agent
                        analyst_agent = Agent(
                            model=model_instance,
                            tools=[duckdb_tools, PandasTools()],
                            system_message=system_prompt,
                            markdown=True,
                        )

                        response = analyst_agent.run(query_input)
                        response_content = response.content if hasattr(response, "content") else str(response)

                    # Display Response
                    st.subheader("💡 Analysis Results")
                    st.markdown(response_content)

                    # Store in conversation history
                    if "history" not in st.session_state:
                        st.session_state.history = []
                    st.session_state.history.append({"query": query_input, "answer": response_content})

                    # Download Report Option
                    st.download_button(
                        label="📥 Download Analysis Report (.md)",
                        data=f"# AI Data Analysis Report\n\n**Query:** {query_input}\n\n**Model:** {provider} ({selected_model})\n\n---\n\n{response_content}",
                        file_name="analysis_report.md",
                        mime="text/markdown",
                    )

                except Exception as e:
                    st.error(f"Analysis Error: {str(e)}")
                    st.info("Tip: Verify that your API key is valid and has sufficient quota.")

        # Show previous history if exists
        if "history" in st.session_state and len(st.session_state.history) > 1:
            with st.expander("📜 Previous Analysis History in this Session"):
                for idx, item in enumerate(reversed(st.session_state.history[:-1])):
                    st.markdown(f"**Q: {item['query']}**")
                    st.markdown(item["answer"])
                    st.divider()

    else:
        st.error("Could not process the dataset. Please ensure it is a valid CSV or Excel file.")

else:
    # Landing page view when no data is uploaded yet
    st.info("👋 Welcome! Upload a dataset above or click **'📂 Load Sales Sample Dataset'** in the sidebar to test.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            ### ⚡ In-Memory OLAP
            High-speed analytical processing with **DuckDB**. Handles aggregation, group-bys, and filtering on hundreds of thousands of rows sub-second.
            """
        )
    with col2:
        st.markdown(
            """
            ### 🧠 Dual LLM Support
            Seamlessly switch between **OpenAI GPT-4o** and **Google Gemini 2.0 / 1.5** based on preference, cost, and availability.
            """
        )
    with col3:
        st.markdown(
            """
            ### 🔒 Local & Private
            Your raw data records remain local in memory on your machine. Only schema definitions and generated queries interact with the LLM API.
            """
        )
