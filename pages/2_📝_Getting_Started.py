import streamlit as st
import pandas as pd
import data_functions as dip
import base64

st.set_page_config(
    page_title="Getting Started",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# This part is about the file upload and data preprocessing part
st.title('Getting Started 🐾')
st.write('This page will guide you through the process of uploading your animal shelter dataset, and making sure it is ready for analysis and prediction.')
# I want to show the relevant variables in a table

sample_dataset = dip.load_dataset_from_repo()

# Display the button to download the dataset in the sidebar
st.sidebar.markdown("### Sample Dataset:")
st.sidebar.write("Try out this app with the sample dataset 👇")
if sample_dataset is not None:
    csv = sample_dataset.to_csv(index=False)
    if st.sidebar.download_button("Download Sample Dataset", data=csv, key="download", help="Click to download the sample dataset.", file_name="sample_dataset.csv" ):
        st.sidebar.success('File downloaded successfully.')

st.subheader('Relevant Variables')
st.info('Note: Your dataset need to have the following variables, and make sure you rename the columns accordingly. ')

# show the relevant variables in a table
# Dictionary containing variable names as keys and their descriptions as values
variable_descriptions = {
    'animal_id': 'Unique ID of the animal',
    'animal_type': 'Type of animal (dog and cat only)',
    'age': 'Age of the animal in years',
    'breed': 'Breed of the animal',
    'colour': 'Color of the animal',
    'gender': 'Gender of the animal (e.g., male, female)',
    'intact_status': 'Intact status of the animal (e.g., intact, neutered, spayed)',
    'intake_type': 'Type of intake (e.g., stray, owner surrender, etc.)',
    'intake_date_time': 'Date of intake of the animal',
    'outcome_date_time': 'Date of outcome (e.g., adoption date, transfer date, etc.)',
    'outcome_type': 'Type of outcome (e.g., adoption, transfer, etc.)'
}

# Create a list of dictionaries for each row in the table
table_data = [{'Column Name': var, 'Description': desc} for var, desc in variable_descriptions.items()]

# Display the table
st.table(table_data)


st.subheader('Upload your animal shelter dataset')
uploaded_data = dip.upload_file_and_check_variables()
if uploaded_data is not None:
    st.write('Number of rows: ', uploaded_data.shape[0], ',  Number of columns: ', uploaded_data.shape[1])
    st.write('Column names: ', ', '.join(uploaded_data.columns))
    st.subheader('Data Preprocessing')

    if st.button('Click to clean the data'):
        cleaned_data = dip.data_preprocessing(uploaded_data)
        st.dataframe(cleaned_data.head(5))
        st.success('Data cleaning completed! 🎉')
        st.markdown('<p style="color:#2FA4FF;font-size:20px;">Navigate yourself to the dashboard to view data insights ✨📊</p>', unsafe_allow_html=True)
        st.session_state['cleaned_data'] = cleaned_data

    