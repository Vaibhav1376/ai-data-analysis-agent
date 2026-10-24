import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from utils.data_processor import preprocess_and_save

# Page configuration
st.set_page_config(page_title="Data Analyst Agent (OpenAI)", page_icon="📊", layout="wide")
st.title("📊 Data Analyst Agent — OpenAI Edition")

# Sidebar for API keys and configuration
with st.sidebar:
    st.header("Configuration")
    env_key = os.getenv("OPENAI_API_KEY", "")
    openai_key = st.text_input(
        "Enter your OpenAI API key:",
        value=env_key,
        type="password",
        help="Your OpenAI API key for GPT-4o queries.",
    )
    if openai_key:
        st.session_state.openai_key = openai_key
        st.success("API key saved!")
    else:
        st.warning("Please enter your OpenAI API key to proceed.")

    st.subheader("Model")
    model_choice = st.selectbox("OpenAI Model:", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0)

# File upload widget
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None and "openai_key" in st.session_state and st.session_state.openai_key:
    # Preprocess and save the uploaded file
    temp_path, columns, df = preprocess_and_save(uploaded_file)

    if temp_path and columns and df is not None:
        # Display the uploaded data as an interactive table
        st.write("Uploaded Data Preview:")
        st.dataframe(df.head(100))

        # Display the columns of the uploaded data
        st.write("Uploaded columns:", columns)

        # Initialize DuckDbTools
        duckdb_tools = DuckDbTools()

        # Load the CSV file into DuckDB as a table
        duckdb_tools.load_local_csv_to_table(
            path=temp_path,
            table="uploaded_data",
        )

        # Initialize the Agent with DuckDB and Pandas tools
        data_analyst_agent = Agent(
            model=OpenAIChat(id=model_choice, api_key=st.session_state.openai_key),
            tools=[duckdb_tools, PandasTools()],
            system_message=(
                "You are an expert data analyst. Use the 'uploaded_data' table in DuckDB to answer user queries. "
                "Generate SQL queries using DuckDB tools to solve the user's query. "
                "Provide clear, concise, and structured answers with Markdown tables and key insights."
            ),
            markdown=True,
        )

        # Main query input widget
        user_query = st.text_area("Ask a query about the data:")

        if st.button("Submit Query", type="primary"):
            if user_query.strip() == "":
                st.warning("Please enter a query.")
            else:
                try:
                    with st.spinner("Processing your query with OpenAI..."):
                        response = data_analyst_agent.run(user_query)
                        response_content = response.content if hasattr(response, "content") else str(response)

                    st.markdown(response_content)

                except Exception as e:
                    st.error(f"Error generating response from the agent: {e}")
                    st.error("Please verify your API key and check if data format is valid.")
elif uploaded_file is not None:
    st.warning("Please enter your OpenAI API key in the sidebar to proceed.")