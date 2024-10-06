import streamlit as st
import datatable as dt
import pandas as pd

# Set the page config
st.set_page_config(page_title="Account Karma", layout="centered")

st.title("Account Karma")

# File uploader and initial DataFrame
uploaded_file = st.file_uploader("Upload your account data", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    try:
        # Use datatable's fread to read the file
        df_dt = dt.fread(uploaded_file)
        # Convert datatable frame to pandas DataFrame
        df = df_dt.to_pandas()

        # Preview the first few rows of the dataset
        st.write("### Data Preview (Before Cleanup):")
        st.dataframe(df.head())

        # Clean up column names
        df.columns = df.columns.str.strip().str.replace('"', '')

        # Detect and show column names
        st.write("### Detected Columns:")
        for i, col in enumerate(df.columns):
            st.write(f"{i}: {col}")

        # Let the user choose the important columns to work with
        account_name_col = st.selectbox("Select the column for Account Name:", df.columns)
        domain_col = st.selectbox("Select the column for Domain:", df.columns)
        country_col = st.selectbox("Select the column for Country:", df.columns)

        # Ensure that the columns selected exist in the dataset
        if account_name_col and domain_col and country_col:
            st.write("You selected the following columns:")
            st.write(f"Account Name: {account_name_col}")
            st.write(f"Domain: {domain_col}")
            st.write(f"Country: {country_col}")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
