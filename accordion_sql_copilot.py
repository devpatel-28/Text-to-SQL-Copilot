
import streamlit as st
import pandas as pd
import sqlite3
from groq import Groq

st.set_page_config(page_title="Text-to-SQL Copilot", layout="wide")

with st.sidebar:
    st.header("Settings")
    st.markdown("Get your free API key at [console.groq.com](https://console.groq.com/)")
    api_key = st.text_input("Enter Groq API Key", type="password")
    st.markdown("---")
    st.markdown("Your Excel data is securely converted into a temporary in-memory SQL database.")

st.title("Text-to-SQL Copilot")
st.markdown("Upload your portfolio or financial dataset to generate insights.")

uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        conn = sqlite3.connect(':memory:')
        table_name = "business_data"
        df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        st.success("Data loaded successfully.")
        
        with st.expander("Preview Data"):
            st.dataframe(df.head())

        schema = pd.io.sql.get_schema(df, table_name)
        
        question = st.text_input("Ask a question about this data (e.g., 'Show me top 5 rows by revenue')")
        
        if st.button("Generate SQL & Run"):
            if not api_key:
                st.error("Please enter your Groq API key in the sidebar.")
            elif not question:
                st.warning("Please type a question.")
            else:
                client = Groq(api_key=api_key)
                prompt = f'''
                You are a senior data analyst. 
                I have a SQLite table named '{table_name}'.
                Here is the schema:
                {schema}
                
                Write a valid SQLite query to answer this question: "{question}"
                Return ONLY the raw SQL code. No markdown formatting, no explanation, no quotes.
                '''
                
                with st.spinner("Generating query..."):
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-70b-8192",
                        temperature=0
                    )
                    
                    generated_sql = response.choices[0].message.content.strip()
                    if generated_sql.startswith("```sql"): generated_sql = generated_sql[6:-3].strip()
                    elif generated_sql.startswith("```"): generated_sql = generated_sql[3:-3].strip()
                        
                    st.code(generated_sql, language="sql")
                    
                    try:
                        result_df = pd.read_sql_query(generated_sql, conn)
                        st.subheader("Query Results")
                        st.dataframe(result_df)
                        
                        csv = result_df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download Results as CSV", data=csv, file_name='query_results.csv', mime='text/csv')
                    except Exception as sql_error:
                        st.error(f"SQL Execution Error: {sql_error}")
                        
    except Exception as e:
        st.error(f"Error processing file: {e}")
