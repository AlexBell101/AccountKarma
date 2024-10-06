import streamlit as st
import pandas as pd
import difflib

# Set page config for the Streamlit app
st.set_page_config(page_title="Account Karma", layout="wide")

# Custom CSS for a cleaner look
st.markdown(
    """
    <style>
    /* Custom style for light theme */
    html, body, [class*="css"]  {
        background-color: #FFFFFF;  /* White background */
        color: #000000;  /* Black text */
        font-family: 'Roboto', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships. Leverage custom rules based on country, domain, opportunity counts, and more.")

# Function to process the account data and add relationship columns
def process_accounts(df):
    if 'Domain' not in df.columns or 'Country' not in df.columns:
        st.error("Required columns 'Domain' or 'Country' not found in the file.")
        return df
    
    df['Account Type'] = "Parent"  # Default to parent; will adjust below
    df['Proposed Parent Account ID'] = None

    for idx, row in df.iterrows():
        domain = row['Domain']
        country = row['Country']
        
        if pd.notna(domain):
            same_domain_df = df[df['Domain'] == domain]
            if len(same_domain_df) > 1:
                same_domain_df = same_domain_df.sort_values(by=['Number of Open Opportunities', 'Number of Closed Opportunities'], ascending=False)
                parent_account = same_domain_df.iloc[0]
                
                for i, child_row in same_domain_df.iterrows():
                    if child_row['Account Name'] != parent_account['Account Name']:
                        df.at[i, 'Account Type'] = 'Child'
                        df.at[i, 'Proposed Parent Account ID'] = parent_account['Parent Account ID']
                    else:
                        df.at[i, 'Account Type'] = 'Parent'

        if domain.endswith('.de') and country == 'Germany':
            com_domain = domain.replace('.de', '.com')
            if com_domain in df['Domain'].values:
                com_account = df[df['Domain'] == com_domain].iloc[0]
                df.at[idx, 'Account Type'] = 'Child'
                df.at[idx, 'Proposed Parent Account ID'] = com_account['Parent Account ID']

    return df

# File uploader and initial DataFrame handling
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file is not None:
    # Check if the file has headers or not
    use_custom_headers = st.checkbox("Does the file have headers?", value=True)
    
    try:
        if use_custom_headers:
            df = pd.read_csv(uploaded_file, encoding='utf-8', error_bad_lines=False, warn_bad_lines=True)
        else:
            df = pd.read_csv(uploaded_file, header=None, encoding='utf-8', error_bad_lines=False, warn_bad_lines=True)
            column_names = ['Account Name', 'Country', 'Domain', 'Website', 'Number of Closed Opportunities', 'Number of Open Opportunities', 'Existing Parent Flag', 'Parent Account ID']
            df.columns = column_names

        st.write("### Data Preview (Before Processing):")
        st.dataframe(df.head())
        
        apply_country_domain_rule = st.checkbox("Apply country and domain-based rules?")
        
        if st.button("Process Data"):
            processed_df = process_accounts(df)
            st.write("### Data Preview (After Processing):")
            st.dataframe(processed_df.head())
            
            csv_data = processed_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Processed CSV", data=csv_data, file_name='processed_accounts.csv', mime='text/csv')

    except UnicodeDecodeError:
        st.error("There was an error reading the CSV file due to encoding issues. Ensure the file is UTF-8 encoded and properly formatted.")
    except pd.errors.ParserError as e:
        st.error(f"Parsing error occurred: {str(e)}. Please check the file format and content.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.write("Please upload a file to proceed.")
