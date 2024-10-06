import streamlit as st
import pandas as pd
import tldextract
from io import BytesIO

# Set up the page
st.set_page_config(page_title="Account Karma", layout="centered")

# UI setup for the app
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships.")

# Function to read CSV file with encoding handling
def read_csv_with_encoding(uploaded_file):
    try:
        # Read the file while handling quotes properly and specifying comma as the delimiter
        return pd.read_csv(uploaded_file, encoding='utf-8', delimiter=',', quotechar='"', skipinitialspace=True)
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading it with ISO-8859-1 (Latin-1) encoding
        return pd.read_csv(uploaded_file, encoding='ISO-8859-1', delimiter=',', quotechar='"', skipinitialspace=True)

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

# Process the file if uploaded
if uploaded_file is not None:
    try:
        # Load the CSV file with encoding handling
        df = read_csv_with_encoding(uploaded_file)

        # Display data preview
        st.write("### Data Preview (Before Cleanup):")
        st.dataframe(df.head())

        # Automatic column matching logic (with user input if necessary)
        def get_column_name(column_options, default_col):
            """Prompt user to select or confirm a column name if automatic detection is incorrect."""
            return st.selectbox(f"Select the column for {default_col}:", column_options, index=column_options.index(default_col) if default_col in column_options else 0)

        # Try to guess columns automatically
        available_columns = list(df.columns)
        
        account_name_col = get_column_name(available_columns, 'Account Name')
        domain_col = get_column_name(available_columns, 'Domain')
        country_col = get_column_name(available_columns, 'Billing Country')
        website_col = get_column_name(available_columns, 'Website')
        parent_flag_col = get_column_name(available_columns, 'Is Parent Account')
        parent_id_col = get_column_name(available_columns, 'Parent Account ID')

        # Add 'Number of Open Opportunities' and 'Number of Closed Opportunities' if present
        open_opps_col = st.selectbox("Select 'Number of Open Opportunities' column (optional):", ['None'] + available_columns)
        closed_opps_col = st.selectbox("Select 'Number of Closed Opportunities' column (optional):", ['None'] + available_columns)

        # Initialize necessary columns for processing
        df['Account Type'] = "Parent"  # Default assumption for all accounts
        df['Proposed Parent Account ID'] = None

        # Define the account processing function
        def process_accounts(df):
            for idx, row in df.iterrows():
                domain = row[domain_col]
                country = row[country_col]

                if pd.notna(domain):
                    # Extract base domain and TLD
                    extracted_domain = tldextract.extract(domain)
                    base_domain = f"{extracted_domain.domain}.{extracted_domain.suffix}"

                    # If the domain is not .com, check if the .com version exists
                    if extracted_domain.suffix != "com":
                        com_domain = f"{extracted_domain.domain}.com"

                        if com_domain in df[domain_col].values:
                            # The .com version is treated as the parent
                            com_account = df[df[domain_col] == com_domain].iloc[0]
                            df.at[idx, 'Account Type'] = 'Child'
                            df.at[idx, 'Proposed Parent Account ID'] = com_account[parent_id_col]

                # Handle accounts with the same domain but different names
                same_domain_df = df[df[domain_col] == domain]

                # Sort based on open and closed opportunities for tie-breaking
                if len(same_domain_df) > 1:
                    if open_opps_col != 'None':
                        same_domain_df = same_domain_df.sort_values(by=[open_opps_col, closed_opps_col], ascending=False)
                    parent_account = same_domain_df.iloc[0]

                    for i, child_row in same_domain_df.iterrows():
                        if child_row[account_name_col] != parent_account[account_name_col]:
                            df.at[i, 'Account Type'] = 'Child'
                            df.at[i, 'Proposed Parent Account ID'] = parent_account[parent_id_col]
                        else:
                            df.at[i, 'Account Type'] = 'Parent'

            return df

        # Process the accounts
        processed_df = process_accounts(df)

        # Display processed data
        st.write("### Data Preview (After Processing):")
        st.dataframe(processed_df.head())

        # Provide download options
        output_format = st.selectbox("Select output format", ['CSV', 'Excel', 'TXT'])

        if output_format == 'CSV':
            csv = processed_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download CSV", data=csv, file_name="processed_accounts.csv", mime="text/csv")

        elif output_format == 'Excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                processed_df.to_excel(writer, index=False)
            st.download_button(label="Download Excel", data=output.getvalue(), file_name="processed_accounts.xlsx", mime="application/vnd.ms-excel")

        elif output_format == 'TXT':
            txt = processed_df.to_csv(index=False, sep="\t").encode('utf-8')
            st.download_button(label="Download TXT", data=txt, file_name="processed_accounts.txt", mime="text/plain")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
