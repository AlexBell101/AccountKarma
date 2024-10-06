import streamlit as st
import pandas as pd
import difflib

# Set the page config
st.set_page_config(page_title="Account Karma", layout="wide")

# Title and description
st.title("🔍 Account Karma")
st.write("""
Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships.
Leverage custom rules based on country, domain, opportunity counts, and more.
""")

# File upload
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# If a file is uploaded
if uploaded_file is not None:
    # Read the uploaded CSV
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())

    # Sidebar options
    st.sidebar.title("Options")

    # Rule: If domain exists for both accounts in the same country, one is the parent
    apply_country_domain_rule = st.sidebar.checkbox("Apply Country & Domain Rule")

    # Rule: Handle accounts with same or similar names but one without domain as duplicate
    apply_name_similarity_rule = st.sidebar.checkbox("Apply Name Similarity Rule")

    # Rule: Use opportunity counts as tiebreaker for duplicates
    apply_opportunity_rule = st.sidebar.checkbox("Use Opportunity Counts for Tiebreaker")

    # Define Parent account country rule
    prefer_us_parents = st.sidebar.checkbox("Prefer Parent Accounts in the United States")

    # Button to process data
    if st.sidebar.button("Process Data"):
        st.write("### Processing Results...")

        # Function to identify potential duplicates and relationships
        def process_accounts(df):
            df['Account Type'] = 'Parent'  # Default every account to parent
            df['Proposed Parent Account Id'] = None  # Initialize as None

            for index, row in df.iterrows():
                # Apply country and domain rule
                if apply_country_domain_rule and pd.notna(row['Domain']):
                    same_country = df[(df['Country'] == row['Country']) & (df['Domain'] == row['Domain'])]
                    if len(same_country) > 1:
                        # Pick the first as parent and others as child
                        df.loc[same_country.index[1:], 'Account Type'] = 'Child'
                        df.loc[same_country.index[1:], 'Proposed Parent Account Id'] = same_country.iloc[0]['Account Id']

                # Apply name similarity rule
                if apply_name_similarity_rule:
                    similar_names = difflib.get_close_matches(row['Name'], df['Name'].tolist(), n=5, cutoff=0.85)
                    if len(similar_names) > 1:
                        # Treat similar names without a domain as duplicates
                        similar_accounts = df[df['Name'].isin(similar_names)]
                        if pd.isna(row['Domain']):
                            df.loc[index, 'Account Type'] = 'Duplicate'
                            df.loc[index, 'Proposed Parent Account Id'] = similar_accounts.iloc[0]['Account Id']

                # Apply opportunity count tiebreaker rule
                if apply_opportunity_rule:
                    same_opportunity_accounts = df[(df['Country'] == row['Country']) & (df['Name'] == row['Name'])]
                    if len(same_opportunity_accounts) > 1:
                        max_opportunities_account = same_opportunity_accounts.loc[
                            same_opportunity_accounts['Number of Open Opportunities'].idxmax()
                        ]
                        df.loc[same_opportunity_accounts.index.difference([max_opportunities_account.name]), 'Account Type'] = 'Duplicate'
                        df.loc[same_opportunity_accounts.index.difference([max_opportunities_account.name]), 'Proposed Parent Account Id'] = max_opportunities_account['Account Id']

            return df

        # Process the uploaded data
        processed_df = process_accounts(df)

        # Display processed data
        st.write("### Processed Data Preview")
        st.dataframe(processed_df.head())

        # Allow user to download the processed file
        csv = processed_df.to_csv(index=False)
        st.download_button("Download Processed CSV", csv, "processed_accounts.csv", "text/csv")
