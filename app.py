import pandas as pd
import streamlit as st

# Load CSV with fallback encoding and clean up header names
def load_csv_with_fallbacks(uploaded_file):
    try:
        # Try reading with utf-8 encoding
        df = pd.read_csv(uploaded_file, encoding='utf-8', error_bad_lines=False)
    except UnicodeDecodeError:
        # Fallback to ISO-8859-1 encoding
        df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', error_bad_lines=False)
    
    # Clean up column headers by stripping quotes and spaces
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    return df

# Function to process accounts in chunks
def process_large_file_in_chunks(uploaded_file, chunk_size=5000):
    processed_chunks = []
    
    for chunk in pd.read_csv(uploaded_file, chunksize=chunk_size):
        processed_chunk = process_accounts(chunk)
        processed_chunks.append(processed_chunk)
    
    # Concatenate all processed chunks back into a single DataFrame
    return pd.concat(processed_chunks, ignore_index=True)

# Function to process accounts and identify parent/child/duplicates
def process_accounts(df):
    df['Account Type'] = 'Parent'
    df['Proposed Parent Account ID'] = ''

    for idx, row in df.iterrows():
        domain = row.get('Domain', '')
        country = row.get('Billing Country', '')
        
        # Apply domain rules for parent-child relations
        if pd.notna(domain):
            if domain.endswith('.de') and country == 'Germany':
                com_domain = domain.replace('.de', '.com')
                if com_domain in df['Domain'].values:
                    com_account = df[df['Domain'] == com_domain].iloc[0]
                    df.at[idx, 'Account Type'] = 'Child'
                    df.at[idx, 'Proposed Parent Account ID'] = com_account['Account ID']
                    
            # Logic for determining duplicates based on name similarity and other rules
            if df.duplicated(subset=['Domain', 'Billing Country']).any():
                df['Account Type'] = 'Duplicate'
    
    return df

# Streamlit app setup
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships.")

# File upload widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Load the file with encoding handling
    df = load_csv_with_fallbacks(uploaded_file)

    # Show preview of the first few rows
    st.write("### Data Preview")
    st.dataframe(df.head())

    # Process the data in chunks and apply parent-child analysis
    st.write("Processing the data, please wait...")
    processed_df = process_large_file_in_chunks(uploaded_file)

    # Show processed data preview
    st.write("### Processed Data")
    st.dataframe(processed_df.head())

    # Download button for processed file
    csv = processed_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Processed CSV", data=csv, file_name="processed_accounts.csv", mime="text/csv")

# Requirements
# streamlit
# pandas
# xlsxwriter
