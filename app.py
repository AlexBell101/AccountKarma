import streamlit as st
import pandas as pd
import difflib

# Streamlit app setup
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships.")

# File upload widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# Function to process the accounts with opportunity-based tie-breaking logic
def process_accounts(df):
    # Ensure columns exist
    required_columns = ['Account Name', 'Domain', 'Billing Country', '# of Closed Opportunities', '# of Open Opportunities']
    if not all(col in df.columns for col in required_columns):
        st.error(f"Required columns missing: {required_columns}")
        return None
    
    # Initialize new columns
    df['Account Type'] = ''
    df['Proposed Parent Account ID'] = ''

    # Iterate through accounts and apply rules
    for idx, row in df.iterrows():
        domain = row['Domain']
        country = row['Billing Country']
        name = row['Account Name']
        open_opps = row['# of Open Opportunities']
        closed_opps = row['# of Closed Opportunities']
        
        # Rule 1: If there is a matching domain within the same country, one becomes a parent
        if pd.notna(domain):
            same_domain = df[(df['Domain'] == domain) & (df['Billing Country'] == country)]
            if len(same_domain) > 1:
                # Tie-breaker by opportunities
                same_domain = same_domain.sort_values(by=['# of Open Opportunities', '# of Closed Opportunities'], ascending=False)
                parent_idx = same_domain.index[0]  # First one with most opportunities becomes the parent
                df.at[parent_idx, 'Account Type'] = 'Parent'
                df.loc[same_domain.index[1:], 'Account Type'] = 'Child'
                df.loc[same_domain.index[1:], 'Proposed Parent Account ID'] = df.at[parent_idx, 'Account ID']
        
        # Rule 2: Duplicate if the name is the same or similar but no domain
        if pd.isna(domain):
            similar_names = difflib.get_close_matches(name, df['Account Name'].tolist(), n=2, cutoff=0.85)
            if len(similar_names) > 1:
                df.at[idx, 'Account Type'] = 'Duplicate'

    return df

# Function to handle large file upload using chunks
def read_large_csv(file):
    try:
        return pd.read_csv(file)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return None

# Process the file if it's uploaded
if uploaded_file is not None:
    try:
        df = read_large_csv(uploaded_file)
        
        if df is not None:
            st.write("### Data Preview")
            st.dataframe(df.head())
            
            account_name_col = st.selectbox("Select the column for Account Name", df.columns)
            domain_col = st.selectbox("Select the column for Domain", df.columns)
            country_col = st.selectbox("Select the column for Billing Country", df.columns)

            # Process the dataset with the rules
            processed_df = process_accounts(df)

            if processed_df is not None:
                st.write("### Processed Data")
                st.dataframe(processed_df.head())

                # Allow the user to download the processed file
                csv = processed_df.to_csv(index=False)
                st.download_button(label="Download Processed Data", data=csv, file_name="processed_accounts.csv", mime="text/csv")
    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

# Requirements file example:
# streamlit
# pandas
# difflib
