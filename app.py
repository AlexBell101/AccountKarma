import pandas as pd
import streamlit as st
from io import BytesIO

# Set the page config
st.set_page_config(page_title="Account Karma", layout="centered")

# Title for the app
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships.")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

# Function to process the accounts
def process_accounts(df):
    # Ensure necessary columns exist
    required_columns = ['Account Name', 'Domain', 'Billing Country', '# of Closed Opportunities', '# of Open Opportunities']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
        return df
    
    df['Account Type'] = 'Parent'
    df['Proposed Parent Account ID'] = None
    df['Duplicate'] = False

    # Rule 1: Parent-child relationships by domain and country
    for idx, row in df.iterrows():
        domain = row['Domain']
        country = row['Billing Country']
        if pd.notna(domain):
            # Look for potential parent-child relationships based on country and domain
            parent_accounts = df[(df['Domain'].str.contains(domain, na=False)) & (df['Billing Country'] == country)]
            if len(parent_accounts) > 1:
                parent = parent_accounts.iloc[0]
                if parent['Account Name'] != row['Account Name']:
                    df.at[idx, 'Account Type'] = 'Child'
                    df.at[idx, 'Proposed Parent Account ID'] = parent['Account ID']
    
    # Rule 2: Name similarity and no domain
    for idx, row in df.iterrows():
        if pd.isna(row['Domain']):
            similar_accounts = df[(df['Account Name'].str.contains(row['Account Name'], na=False)) & (df['Billing Country'] == row['Billing Country']) & pd.notna(df['Domain'])]
            if not similar_accounts.empty:
                df.at[idx, 'Duplicate'] = True

    # Rule 3: Use opportunities as a tiebreaker
    for idx, row in df.iterrows():
        if df.at[idx, 'Account Type'] == 'Parent':
            parent_candidates = df[(df['Account Name'] == row['Account Name']) & (df['Billing Country'] == row['Billing Country'])]
            if len(parent_candidates) > 1:
                parent_candidates = parent_candidates.sort_values(by=['# of Open Opportunities', '# of Closed Opportunities'], ascending=False)
                parent = parent_candidates.iloc[0]
                if parent['Account ID'] != row['Account ID']:
                    df.at[idx, 'Account Type'] = 'Child'
                    df.at[idx, 'Proposed Parent Account ID'] = parent['Account ID']

    return df

# Check if a file was uploaded
if uploaded_file is not None:
    try:
        # Try reading the file with the appropriate encoding and skip bad lines
        df = pd.read_csv(uploaded_file, encoding='utf-8', on_bad_lines='skip', header=0)
        
        # Show a preview of the data
        st.write("### Data Preview (Before Processing):")
        st.dataframe(df.head())
        
        # Let user select columns if they aren't standard
        account_name_col = st.selectbox("Select the column for Account Name:", df.columns)
        domain_col = st.selectbox("Select the column for Domain:", df.columns)
        country_col = st.selectbox("Select the column for Country:", df.columns)
        
        # Perform the account processing
        processed_df = process_accounts(df)
        
        # Show the processed data
        st.write("### Processed Data:")
        st.dataframe(processed_df[[account_name_col, domain_col, country_col, 'Account Type', 'Proposed Parent Account ID']].head())
        
        # Allow the user to download the processed data
        csv = processed_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Processed CSV",
            data=csv,
            file_name="processed_accounts.csv",
            mime="text/csv"
        )
    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
