import streamlit as st
import pandas as pd
import chardet  # to detect file encoding
import numpy as np
from fuzzywuzzy import fuzz

# Set the page config
st.set_page_config(page_title="Account Karma", layout="centered")

st.title("Account Karma")

# File uploader and initial DataFrame
uploaded_file = st.file_uploader("Upload your account data", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    try:
        # Detect file encoding
        raw_data = uploaded_file.read()
        result = chardet.detect(raw_data)
        file_encoding = result['encoding']
        
        # Reload the file with correct encoding using pandas
        st.write(f"Detected file encoding: {file_encoding}")
        uploaded_file.seek(0)  # Reset file pointer after reading it for encoding detection
        df = pd.read_csv(uploaded_file, encoding=file_encoding)

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
        closed_opps_col = st.selectbox("Select the column for Closed Opportunities:", df.columns)
        open_opps_col = st.selectbox("Select the column for Open Opportunities:", df.columns)

        # Ensure that the columns selected exist in the dataset
        if account_name_col and domain_col and country_col:
            st.write("You selected the following columns:")
            st.write(f"Account Name: {account_name_col}")
            st.write(f"Domain: {domain_col}")
            st.write(f"Country: {country_col}")

            # Add columns for Account Type and Proposed Parent Account ID
            df['Account Type'] = np.nan
            df['Proposed Parent Account ID'] = np.nan

            # Process the accounts based on the rules
            for idx, row in df.iterrows():
                domain = row[domain_col]
                country = row[country_col]
                account_name = row[account_name_col]
                closed_opps = row[closed_opps_col]
                open_opps = row[open_opps_col]

                # Rule 1: If domain exists for both and the country is the same, make the .com domain the parent if both exist
                if pd.notna(domain):
                    possible_parent_domains = [domain.replace('.' + domain.split('.')[-1], '.com')]
                    for parent_domain in possible_parent_domains:
                        if parent_domain in df[domain_col].values:
                            com_account = df[df[domain_col] == parent_domain].iloc[0]
                            df.at[idx, 'Account Type'] = 'Child'
                            df.at[idx, 'Proposed Parent Account ID'] = com_account['Account ID']
                            break

                # Rule 2: If the account name is similar and one has no domain, mark the one without a domain as a duplicate
                for other_idx, other_row in df.iterrows():
                    if idx != other_idx:
                        other_domain = other_row[domain_col]
                        similarity = fuzz.partial_ratio(account_name, other_row[account_name_col])
                        if similarity > 80:  # Threshold for account name similarity
                            if pd.isna(domain) and pd.notna(other_domain):
                                df.at[idx, 'Account Type'] = 'Duplicate'
                                break

                # Rule 3: In a tie, use the number of closed or open opportunities to determine the parent
                if pd.isna(df.at[idx, 'Account Type']):
                    if pd.notna(open_opps) and pd.notna(closed_opps):
                        max_open_opps_idx = df[open_opps_col].idxmax()
                        max_closed_opps_idx = df[closed_opps_col].idxmax()
                        if idx == max_open_opps_idx or idx == max_closed_opps_idx:
                            df.at[idx, 'Account Type'] = 'Parent'
                        else:
                            df.at[idx, 'Account Type'] = 'Child'

            # Display the processed data
            st.write("### Processed Data:")
            st.dataframe(df[[account_name_col, domain_col, country_col, 'Account Type', 'Proposed Parent Account ID']].head())

            # Download button for the processed file
            processed_file = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Processed Data", data=processed_file, file_name="processed_accounts.csv", mime="text/csv")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {str(e)}")
else:
    st.write("Please upload a CSV file to proceed.")
