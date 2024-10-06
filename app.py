import streamlit as st
import pandas as pd
import io

# Set the page config before any other Streamlit code
st.set_page_config(page_title="Account Karma", layout="centered")

# Custom CSS to force light or custom theme even when the user has dark mode enabled
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        background-color: #FFFFFF;
        color: #000000;
        font-family: 'Roboto', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# UI setup for the app
st.title("🔍 Account Karma")
st.write("Upload your account data, apply rules to detect duplicates, and identify parent-child account relationships. Leverage custom rules based on country, domain, opportunity counts, and more.")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

# Function to load the CSV file
def load_csv(file):
    try:
        # Attempt to load with utf-8
        return pd.read_csv(file, encoding='utf-8', header=0)
    except UnicodeDecodeError:
        # Fallback to ISO-8859-1 if utf-8 fails
        return pd.read_csv(file, encoding='ISO-8859-1', header=0)

# Process the uploaded file
if uploaded_file:
    # Load the file with appropriate encoding handling
    df = load_csv(uploaded_file)
    
    # Display the columns and preview the data
    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())
    
    # Display the column names to confirm they are loaded correctly
    st.write("### Column Names Detected:")
    st.write(df.columns.tolist())
    
    # Now ask user to confirm the key columns
    account_name_col = st.selectbox("Select the column for Account Name:", df.columns)
    domain_col = st.selectbox("Select the column for Domain:", df.columns)
    country_col = st.selectbox("Select the column for Country:", df.columns)
    
    # Proceed with processing logic based on selected columns
    st.write(f"Selected Account Name Column: {account_name_col}")
    st.write(f"Selected Domain Column: {domain_col}")
    st.write(f"Selected Country Column: {country_col}")
    
    # Additional logic to handle duplicates, parent-child relationships, etc.
    # Replace this with your logic for processing the dataset
    st.write("Processing your data based on the selected columns...")
    
    # For example, here you could apply your parent-child detection or deduplication logic:
    # - Based on domain similarity
    # - Based on account name similarity
    # - Applying other rules
    
    # Just as an example: checking for duplicate domains
    df['Duplicate'] = df.duplicated(subset=[domain_col], keep=False)
    
    st.write("### Data after processing (example):")
    st.dataframe(df[[account_name_col, domain_col, country_col, 'Duplicate']].head())
    
    # You can now proceed with any additional processing using these columns

else:
    st.write("Please upload a file to proceed.")
