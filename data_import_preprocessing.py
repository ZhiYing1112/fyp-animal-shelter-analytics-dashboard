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
    
    if data is not None:
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


def change_data_type_calc_metrics(data):
    # change data type
    data['animal_id'] = data['animal_id'].astype('category')
    data['breed'] = data['breed'].astype('category')
    data['colour'] = data['colour'].astype('category')
    data['animal_type'] = data['animal_type'].astype('category')
    data['gender'] = data['gender'].astype('category')
    data['outcome_type'] = data['outcome_type'].astype('category')
    data['intake_type'] = data['intake_type'].astype('category')
    data['age'] = data['age'].astype('category')
    data['intake_date_time'] = pd.to_datetime(data['intake_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))
    data['outcome_date_time'] = pd.to_datetime(data['outcome_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))

    # calculate number of intakes for each animal_id
    total_num_intakes = data['intake_type'].count()
    # num_adoptions is when outcome_type is adoption
    total_num_adoptions = data[data['outcome_type'] == 'Adoption']['outcome_type'].count()
    # intake_animal_count is the number of animals in the shelter
    intake_animal_count = data['animal_id'].nunique()
    # save_rate is Intake minus Euthanasia Outcomes divided by num Intake
    num_euthanasia = data[data['put_to_sleep'] == True]['put_to_sleep'].count()
    save_rate = (total_num_intakes - num_euthanasia) / total_num_intakes
    # live_release_rate is the number of live outcomes divided by the number of intakes
    num_death_in_shelter = data[data['died_off_shelter'] == True]['animal_id'].count()
    live_release_rate = (total_num_intakes - num_death_in_shelter) / total_num_intakes

    st.session_state['total_num_intakes'] = total_num_intakes
    st.session_state['total_num_adoptions'] = total_num_adoptions
    st.session_state['intake_animal_count'] = intake_animal_count
    st.session_state['save_rate'] = save_rate
    st.session_state['live_release_rate'] = live_release_rate

    return data

# Part 1: Initial data preprocessing: missing data, data type, duplicates, filter, sort.
def initial_preprocessing(data):

    if data is not None:
        data = change_data_type_calc_metrics(data)
    
        data = data.sort_values(by=['animal_id', 'intake_date_time', 'outcome_date_time'], ascending=[True, False, False])

        data = data.groupby('animal_id').head(1)
        
        relevant_vars = ['animal_id', 'intake_date_time', 'breed', 'colour', 'animal_type', 'age', 'gender', 'outcome_date_time', 
                         'outcome_type', 'intake_type']
    
        data = data.drop(columns=[col for col in data.columns if col not in relevant_vars])
        data = remove_missing_data(data)

        data = data.drop(data[data['outcome_date_time'] < data['intake_date_time']].index, axis=0)

        # Filter the data to only have animal_type dog and cat
        data = data[data['animal_type'].str.lower().isin(['dog', 'cat'])]

        # Reset the index
        data = data.reset_index(drop=True)

    return data


def remove_missing_data(data):

    # Check for missing data, if more than 30% then drop the column, if less than 30% then impute with mode or median
    for col in data.columns:
        if data[col].isnull().sum() > 0.3 * len(data):
            data.drop(col, axis=1, inplace=True)
        else:
            # drop the rows with missing data
            data.dropna(axis=0, inplace=True)

    return data

# Part 2: Create a function to transform the data
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
    # if data['gender'] contains any string of neutered, spayed, or intact then only perform this function
    if data['gender'].str.contains(r'neutered|spayed|intact', case=False).any():
        data[['new_gender', 'intact_status']] = data['gender'].apply(separate_gender_and_intact_status).apply(pd.Series)

    else:
        # Cleaning breed
        data[['new_breed', 'is_mix_breed']] = data['breed'].apply(separate_breed).apply(pd.Series)

        # Cleaning colour
        data[['new_colour', 'is_multicolour']] = data['colour'].apply(separate_colour).apply(pd.Series)
        data['is_multicolour'] = data.apply(update_multicolour, axis=1)
        data[['is_black', 'is_white', 'is_brown', 'is_yellow', 'is_gray']] = data['colour'].apply(lambda x: separate_colour_columns(x)).apply(pd.Series)

        # Drop the original columns
        data.drop(['gender', 'breed', 'colour'], axis=1, inplace=True)

        # Move the outcome type column to the last column
        data['outcome_type'] = data.pop('outcome_type')

        # lower case all the columns
        data['intake_type'] = data['intake_type'].str.lower()
        data['animal_type'] = data['animal_type'].str.lower()
        data['outcome_type'] = data['outcome_type'].str.lower()

    return data

def separate_gender_and_intact_status(value):
    value = value.lower()
    gender = 'unknown'  # Initialize the gender variable with a default value

    if 'neutered' in value:
        value = value.split(' ')[0]
        gender = 'male'
        intact_status = 'neutered'
    elif 'spayed' in value:
        value = value.split(' ')[0]
        gender = 'female'
        intact_status = 'spayed'
    elif 'intact' in value:
        value = value.split(' ')[1]
        intact_status = 'intact'
        if value == 'male':
            gender = 'male'
        elif value == 'female':
            gender = 'female'
        else:
            intact_status = 'unknown'
    else:
        intact_status = 'unknown'

    return gender, intact_status

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

def separate_breed(value):
    value = value.lower()
    
    if 'mix' in value:
        value = value.split(' mix')[0]
        is_mix_breed = 'yes'
    elif '/' in value:
        value = value.split('/')[0]
        is_mix_breed = 'yes'
    else:
        value = value
        is_mix_breed = 'no'
    
    return value, is_mix_breed

def separate_colour(value):
    value = value.lower()
    
    if '/' in value:
        value = value.split('/')[0]
        is_multicolour = 'yes'
    elif 'tricolor' in value:
        value = value.split('/')[0]
        is_multicolour = 'yes'
    else:
        value = value
        is_multicolour = 'no'
    
    return value, is_multicolour

def update_multicolour(row):
    colour = ['agouti', 'point', 'tick', 'calico', 'brindle', 'torbie', 'tortie', 'sable', 'merle']
    
    if any(color in row['primary_colour'].lower() for color in colour):
        return 'yes'
    else:
        return row['is_multicolour']

def separate_colour_columns(colour):
    colour = colour.lower()
    
    is_black = 'yes' if 'black' in colour else 'no'
    is_white = 'yes' if 'white' in colour else 'no'
    is_brown = 'yes' if any(color in colour for color in ['brown', 'liver', 'chocolate', 'ruddy', 'red']) else 'no'
    is_yellow = 'yes' if any(color in colour for color in ['yellow', 'apricot', 'cream', 'buff', 'fawn', 'gold', 'tan']) else 'no'
    is_gray = 'yes' if any(color in colour for color in ['gray', 'blue', 'silver', 'lynx', 'lilac']) else 'no'
    
    return is_black, is_white, is_brown, is_yellow, is_gray





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

