# Import all the necessary libraries
import streamlit as st
import pandas as pd
import xgboost as xgb

def upload_file_and_check_variables():
    st.subheader('Upload your animal shelter dataset here 👇')
    uploaded_file = st.file_uploader('Choose a file (.csv and .xlsx is accepted only)', type=['csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            if uploaded_file.type == 'application/vnd.ms-excel':  # Check if the file is an XLSX file
                data = pd.read_excel(uploaded_file)
            else:
                data = pd.read_csv(uploaded_file)

            # Check if relevant variables are present in the dataset
            relevant_vars = ['animal_type', 'age', 'breed', 'color', 'gender', 'outcome_type', 'intake_type', 'intake_date', 'outcome_date']
            
            missing_vars = [var for var in relevant_vars if var not in data.columns]

            if len(missing_vars) == 0:
                st.success('File upload successful! your dataset has all the relevant variables for this program.')
                return data
            else:
                st.error(f'The following relevant variables are missing in the dataset: {", ".join(missing_vars)}.\nPlease try again.')
        except Exception as e:
            st.error('Error: Unable to read the uploaded file. Please make sure it is a valid CSV or Excel file.')
            st.error(e)
    else:
        st.warning('Please upload a file to continue.')



# 2.
# Create function to clean the data
# Once the data is cleaned, show the data in a table.

# 3.
# Create a function to import the scaler and model.joblib files and make predictions on animal adoption.

# 4.
# Then create multiple functions to calculate each of the metrics
# Use the calculated field to plot the graphs using plotly and streamlit functions and elements


# Create a title for the app
# st.write('Hello world!')

