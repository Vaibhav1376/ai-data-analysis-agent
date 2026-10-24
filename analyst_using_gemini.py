import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from utils.data_processor import preprocess_and_save

# Page configuration
st.set_page_config(page_title="Data Analyst Agent (Gemini)", page_icon="♊", layout="wide")
st.title("📊 Data Analyst Agent — Google Gemini Edition")

# Sidebar for API keys and model selection
with st.sidebar:
    st.header("Configuration")

    # API Key Input
    env_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = st.text_input(
        "Enter your Gemini API key:",
        value=env_key,
        type="password",
    )
    if gemini_key:
        st.session_state.gemini_key = gemini_key
        st.success("API key saved!")
    else:
        st.warning("Please enter your Gemini API key to proceed.")

    # Model Selection Dropdown
    st.subheader("Select Model")
    model_options = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-lite",
    ]
    selected_model = st.selectbox("Choose a Gemini model:", model_options, index=0)
    st.session_state.selected_model = selected_model

    st.info(f"Selected: {selected_model}")

# File upload widget
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None and "gemini_key" in st.session_state and st.session_state.gemini_key:
    # Preprocess and save the uploaded file
    temp_path, columns, df = preprocess_and_save(uploaded_file)

    if temp_path and columns and df is not None:
        # Display the uploaded data as a table
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

        # Initialize the Agent with Gemini model
        data_analyst_agent = Agent(
            model=Gemini(
                id=st.session_state.selected_model,
                api_key=st.session_state.gemini_key,
            ),
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
                    with st.spinner("Processing your query with Gemini..."):
                        response = data_analyst_agent.run(user_query)
                        response_content = response.content if hasattr(response, "content") else str(response)

                    st.markdown(response_content)

                except Exception as e:
                    st.error(f"Error generating response from the agent: {e}")
                    st.error("Please verify your API key and check if data format is valid.")
elif uploaded_file is not None:
    st.warning("Please enter your Gemini API key in the sidebar to proceed.")
