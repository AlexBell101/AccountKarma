import streamlit as st
import pandas as pd
import chardet

# Set up Streamlit app
st.title("Account Karma")
st.write("Upload your account data and apply rules to detect duplicates and identify parent-child relationships.")

# Upload the CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

# Helper function to detect encoding
def detect_encoding(file):
    raw_data = file.read(10000)
    file.seek(0)
    result = chardet.detect(raw_data)
    return result['encoding']

if uploaded_file:
    # Detect the file encoding
    encoding = detect_encoding(uploaded_file)
    
    try:
        df = pd.read_csv(uploaded_file, encoding=encoding)
        st.success(f"File loaded successfully with encoding: {encoding}")
        
        # Display the first few rows of the dataframe
        st.write("### Data Preview")
        st.dataframe(df.head())
        
        # Allow user to select important columns
        account_name_col = st.selectbox("Select the column for Account Name", df.columns)
        domain_col = st.selectbox("Select the column for Domain", df.columns)
        country_col = st.selectbox("Select the column for Billing Country", df.columns)
        
        # Processing rules
        def process_accounts(df):
            df['Duplicate'] = False
            df['Account Type'] = 'Parent'
            df['Proposed Parent Account ID'] = None
            
            for idx, row in df.iterrows():
                account_name = row[account_name_col]
                domain = row[domain_col]
                country = row[country_col]
                
                # Rule 1: If the domain exists for both and the country is the same, one is parent
                if pd.notna(domain):
                    com_domain = domain.replace('.de', '.com')
                    if com_domain in df[domain_col].values and country == df[df[domain_col] == com_domain][country_col].values[0]:
                        parent_row = df[df[domain_col] == com_domain].iloc[0]
                        df.at[idx, 'Account Type'] = 'Child'
                        df.at[idx, 'Proposed Parent Account ID'] = parent_row['Account ID']
                
                # Rule 2: Similar names and same country, one without domain is duplicate
                similar_accounts = df[(df[account_name_col].str.contains(account_name, case=False)) & (df[country_col] == country)]
                if len(similar_accounts) > 1 and pd.isna(row[domain_col]):
                    df.at[idx, 'Duplicate'] = True
            
            return df

        processed_df = process_accounts(df)
        
        # Display processed data
        st.write("### Processed Data")
        st.dataframe(processed_df[[account_name_col, domain_col, country_col, 'Account Type', 'Proposed Parent Account ID', 'Duplicate']].head())
        
        # Download button for processed data
        csv = processed_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Processed CSV",
            data=csv,
            file_name='processed_accounts.csv',
            mime='text/csv',
        )
    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {str(e)}")

else:
    st.write("Please upload a CSV file to proceed.")
