import streamlit as st
import pandas as pd
import tldextract
from io import BytesIO

# Set up the page
st.set_page_config(page_title="Account Karma", layout="centered")

# UI setup for the app
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships. Leverage custom rules based on country, domain, opportunity counts, and more.")

# Function to read CSV file with encoding handling
def read_csv_with_encoding(uploaded_file):
    try:
        # Attempt to read the file with UTF-8 encoding
        return pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading it with ISO-8859-1 (Latin-1) encoding
        return pd.read_csv(uploaded_file, encoding='ISO-8859-1')

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

# Process the file
if uploaded_file is not None:
    try:
        # Load the CSV file with encoding handling
        df = read_csv_with_encoding(uploaded_file)

        # Display data preview
        st.write("### Data Preview (Before Cleanup):")
        st.dataframe(df.head())

        # Ensure necessary columns are in the dataset
        required_columns = ['Domain', 'Country', 'Account Name', 'Number of Open Opportunities', 'Number of Closed Opportunities', 'Parent Account ID']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Required column '{col}' is missing from the dataset.")
                st.stop()

        # Initialize necessary columns for processing
        df['Account Type'] = "Parent"  # Default assumption for all accounts
        df['Proposed Parent Account ID'] = None

        # Define the account processing function
        def process_accounts(df):
            for idx, row in df.iterrows():
                domain = row['Domain']
                country = row['Country']

                if pd.notna(domain):
                    # Extract base domain and TLD
                    extracted_domain = tldextract.extract(domain)
                    base_domain = f"{extracted_domain.domain}.{extracted_domain.suffix}"

                    # If the domain is not .com, check if the .com version exists
                    if extracted_domain.suffix != "com":
                        com_domain = f"{extracted_domain.domain}.com"

                        if com_domain in df['Domain'].values:
                            # The .com version is treated as the parent
                            com_account = df[df['Domain'] == com_domain].iloc[0]
                            df.at[idx, 'Account Type'] = 'Child'
                            df.at[idx, 'Proposed Parent Account ID'] = com_account['Parent Account ID']

                # Handle accounts with the same domain but different names
                same_domain_df = df[df['Domain'] == domain]

                # Sort based on open and closed opportunities for tie-breaking
                if len(same_domain_df) > 1:
                    same_domain_df = same_domain_df.sort_values(by=['Number of Open Opportunities', 'Number of Closed Opportunities'], ascending=False)
                    parent_account = same_domain_df.iloc[0]

                    for i, child_row in same_domain_df.iterrows():
                        if child_row['Account Name'] != parent_account['Account Name']:
                            df.at[i, 'Account Type'] = 'Child'
                            df.at[i, 'Proposed Parent Account ID'] = parent_account['Parent Account ID']
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
            st.download_button(label="Download CSV", data=csv, file_name="processed_accounts.csv", mime='text/csv')
        elif output_format == 'Excel':
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            processed_df.to_excel(writer, index=False)
            writer.save()
            st.download_button(label="Download Excel", data=output.getvalue(), file_name="processed_accounts.xlsx", mime='application/vnd.ms-excel')
        elif output_format == 'TXT':
            txt = processed_df.to_csv(index=False, sep="\t").encode('utf-8')
            st.download_button(label="Download TXT", data=txt, file_name="processed_accounts.txt", mime='text/plain')

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

else:
    st.info("Please upload a CSV file to proceed.")
