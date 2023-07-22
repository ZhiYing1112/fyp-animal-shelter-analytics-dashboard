# Import all the necessary libraries
import streamlit as st
import pandas as pd
import xgboost as xgb
import time
import re
from dateutil import parser


def upload_file_and_check_variables():
    
    uploaded_file = st.file_uploader('Choose and submit a single file (.csv and .xlsx is accepted only)',
                                      type=['csv', 'xlsx'], 
                                      accept_multiple_files=False)

    if uploaded_file is not None:
        try:
            if uploaded_file.type == 'application/vnd.ms-excel':  # Check if the file is an XLSX file
                data = pd.read_excel(uploaded_file)
            else:
                data = pd.read_csv(uploaded_file)

            # Check if relevant variables are present in the dataset
            relevant_vars = ['animal_id', 'animal_type', 'age', 'breed', 'colour', 'gender', 'outcome_type', 'intake_type', 'intake_date_time', 'outcome_date_time']
            
            missing_vars = [var for var in relevant_vars if var not in data.columns]

            if len(missing_vars) == 0:
                st.success('Great! Your dataset has all the relevant variables for this program.')
                return data
            
            else:
                st.error(f'The following relevant variables are missing in the dataset: {", ".join(missing_vars)}. Please try again.')

        except Exception as e:
            st.error('Error: Unable to read the uploaded file. Please make sure it is a valid CSV or Excel file.')
            st.error(e)
    else:
        st.warning('Please upload a file to continue.')


# Create a function that accesses the data from the session state and preprocesses it

def data_preprocessing(data):
    
        initial_cleaning_data = initial_preprocessing(data)
        transformed_data = data_transformation(initial_cleaning_data)

        # Simulate data preprocessing progress with a loop
        progress_bar = st.progress(0)
        status_text = st.empty()
        for percent_complete in range(1, 101):
            progress_bar.progress(percent_complete)
            status_text.text(f"Preprocessing data: {percent_complete}% Complete")
            # Add a short sleep to simulate processing time
            time.sleep(0.1)
    
        # After preprocessing is complete, update the progress bar and status text
        progress_bar.empty()
        status_text.text("Data preprocessing complete!")
        return transformed_data


# Initial data preprocessing: missing data, data type, duplicates, filter, sort.
def initial_preprocessing(data):
    
    # Change data type of intake_date_time and outcome_date_time to datetime
    data['intake_date_time'] = pd.to_datetime(data['intake_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))
    data['outcome_date_time'] = pd.to_datetime(data['outcome_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))

    # Sort data by animal_id and intake_date_time
    data = data.sort_values(by=['animal_id', 'intake_date_time', 'outcome_date_time'], ascending=[True, False, False])
    
    # If there are duplicated animal_id, keep the first row and drop the rest
    data = data.drop_duplicates(subset=['animal_id'], keep='first')

    # Check for missing data, if more than 30% then drop the column, if less than 30% then impute with mode or median
    missing_data = data.isnull().sum().sort_values(ascending=False)

    if missing_data.any():
        missing_data_percent = (missing_data / data.shape[0]) * 100
        missing_data_table = pd.concat([missing_data, missing_data_percent], axis=1)
        missing_data_table = missing_data_table.rename(columns={0: 'Missing Values', 1: '% of Total Values'})

        # if the percentage of missing data is more than 30%, drop the column
        if missing_data_table['% of Total Values'].any() >= 30:
            data = data.drop(missing_data_table[missing_data_table['% of Total Values'] >= 30].index, axis=1)
        else:
            # Impute missing data with mode or median
            for col in data.columns:
                if data[col].isnull().sum() > 0:
                    if data[col].dtype == 'object':
                        data[col] = data[col].fillna(data[col].mode()[0])
                    else:
                        data[col] = data[col].fillna(data[col].median())
    
    # Check if there are any mismatch between outcome_date_time and intake_date_time
    # If outcome_date_time is earlier than intake_date_time, then drop the row
    data = data.drop(data[data['outcome_date_time'] < data['intake_date_time']].index, axis=0)

    # Filter the data to only have animal_type dog and cat
    data = data[data['animal_type'].str.lower().isin(['dog', 'cat'])]

    # Reset the index
    data = data.reset_index(drop=True)

    return data

# create a function to transform the data
def data_transformation(data):
    # Create days_in_shelter
    data['days_in_shelter'] = (data['outcome_date_time'] - data['intake_date_time']).dt.days
    # Filter days_in_shelter maximum is 365 days
    data = data[data['days_in_shelter'] <= 365]

    # Create intake and outcome month and year
    data['outcome_month'] = data['outcome_date_time'].dt.month
    data['outcome_year'] = data['outcome_date_time'].dt.year

    # Create age_group
    # Check if age is numeric or categorical
    if data['age'].dtype == 'object':
        # remove special characters and leading or trailing spaces
        data['age'] = data['age'].apply(lambda x: re.sub(r'[^a-zA-Z0-9 ]', '', str(x)))
        data['age'] = data['age'].str.strip()

        age_days = data['age'].apply(lambda x: int(x.split()[0])*365 
                                                       if 'year' in x else (int(x.split()[0])*30 
                                                                            if 'month' in x else int(x.split()[0])))
        age_years = age_days//365
        data['age'] = age_years 
        data['age_group'] = age_years.apply(age_group)
    else:
        data['age_group'] = data['age'].apply(age_group)

    
    # Cleaning gender

    # Cleaning breed

    # Cleaning colour

    # Cleaning outcome_type

    return data


def age_group(age):
    if age <= 1:
        return 'puppy/kitten'
    elif age <= 3:
        return 'adolescent'
    elif age <= 7:
        return 'adulthood'
    elif age <= 10:
        return 'senior'
    else:
        return 'super senior'
    
# st.info('Click the button below to upload and preprocess the data.')
#                 # Display the "Upload" button only when the file is valid
#                 if st.button('Upload and Preprocess Data'):
#                     # Perform data preprocessing with a progress bar
#                     cleaned_data = data_preprocessing(data)


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

