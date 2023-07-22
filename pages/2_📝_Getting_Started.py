import streamlit as st
import pandas as pd
import data_import_preprocessing as dip

# This part is about the file upload and data preprocessing part
st.header('Getting Started 🐾')
st.write('This page will guide you through the process of uploading your animal shelter dataset, and making sure it is ready for analysis and prediction.')
# I want to show the relevant variables in a table
st.subheader('Relevant Variables')
st.info('Your dataset need to have the following variables, and make sure you rename the columns accordingly. ')

# show the relevant variables in a table
# Dictionary containing variable names as keys and their descriptions as values
variable_descriptions = {
    'animal_id': 'Unique ID of the animal',
    'animal_type': 'Type of animal (dog and cat only)',
    'age': 'Age of the animal in years',
    'breed': 'Breed of the animal',
    'colour': 'Color of the animal',
    'gender': 'Gender of the animal (e.g., male, female)',
    'intake_type': 'Type of intake (e.g., stray, owner surrender, etc.)',
    'intake_date_time': 'Date of intake of the animal',
    'outcome_date_time': 'Date of outcome (e.g., adoption date, transfer date, etc.)',
    'days_in_shelter': 'Number of days the animal was in the shelter',
    'outcome_type': 'Type of outcome (e.g., adoption, transfer, etc.)'
}

# Create a list of dictionaries for each row in the table
table_data = [{'Column Name': var, 'Description': desc} for var, desc in variable_descriptions.items()]

# Display the table
st.table(table_data)


st.subheader('Upload your animal shelter dataset')
cleaned_data = dip.upload_file_and_check_variables()
if cleaned_data is not None:
    st.write('Number of rows: ', cleaned_data.shape[0], ',  Number of columns: ', cleaned_data.shape[1])
    st.write('Column names: ', ', '.join(cleaned_data.columns))

st.subheader('Data Preprocessing')
dip.data_preprocessing(cleaned_data)

# st.dataframe(cleaned_data.head(5))
# if uploaded_data is not None:
#     st.write('Preview of the uploaded dataset:')
#     st.write('Number of rows: ', uploaded_data.shape[0], ',  Number of columns: ', uploaded_data.shape[1])
#     st.dataframe(uploaded_data.head(10))
    
    