# Import all the necessary libraries
import streamlit as st
import pandas as pd
import numpy as np
import time
import re
import plotly.express as px
import plotly.graph_objects as go
import time
from tqdm import tqdm
from joblib import load
from dateutil import parser
from sklearn.preprocessing import LabelEncoder


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
        
        final_data = transform_data(transformed_data)

        progress_bar = st.progress(0)
        status_text = st.empty()
        for percent_complete in range(1, 101):
            progress_bar.progress(percent_complete)
            status_text.text(f"Preprocessing data: {percent_complete}% Complete")
            # Add a short sleep to simulate processing time
            time.sleep(0.1)
    
        # After preprocessing is complete, update the progress bar and status text
        progress_bar.empty()

        return final_data


def change_date_data_type(data):
    # change data type
    data['intake_date_time'] = pd.to_datetime(data['intake_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))
    data['outcome_date_time'] = pd.to_datetime(data['outcome_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))

    # calculate number of intakes for each animal_id
    total_num_intakes = data['intake_type'].count()
    
    st.session_state['total_num_intakes'] = total_num_intakes
   
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

def calculate_cat_dog_metric(data):
    if st.session_state.get('total_num_intakes') is not None:
        total_num_intakes = st.session_state.get('total_num_intakes')

        # num_adoptions is when outcome_type is adoption
        total_num_adoptions = data[data['outcome_type'] == 'Adoption']['outcome_type'].count()
        # save_rate is Intake minus Euthanasia Outcomes divided by num Intake
        num_euthanasia = data[data['outcome_type'] == 'Euthanasia']['outcome_type'].count()
        save_rate = (total_num_intakes - num_euthanasia) / total_num_intakes
        # st.write('num euthanasia', num_euthanasia)
        # live_release_rate is the number of live outcomes divided by the number of intakes
        num_death_in_shelter = data[data['outcome_type'] == 'Died']['outcome_type'].count()
        # st.write('num deaths', num_death_in_shelter)
        live_release_rate = (total_num_intakes - num_death_in_shelter) / total_num_intakes

        st.session_state['total_num_adoptions'] = total_num_adoptions
        st.session_state['save_rate'] = save_rate
        # st.write('save rate', save_rate)
        st.session_state['live_release_rate'] = live_release_rate
        # st.write('live release rate', live_release_rate)

# Part 1: Initial data preprocessing: missing data, data type, duplicates, filter, sort.
def initial_preprocessing(data):

    if data is not None:

        data = change_date_data_type(data)

        data = data.sort_values(by=['animal_id', 'intake_date_time', 'outcome_date_time'], ascending=[True, False, False])
        
        # data = data.groupby('animal_id').head(1)
        
        # relevant_vars = ['animal_id', 'intake_date_time', 'breed', 'colour', 'animal_type', 'age', 'gender', 'outcome_date_time', 
        #                  'outcome_type', 'intake_type']
    
        # data = data.drop(columns=[col for col in data.columns if col not in relevant_vars])

        data = remove_missing_data(data)

        data = data.drop(data[data['outcome_date_time'] < data['intake_date_time']].index, axis=0)

        # Filter the data to only have animal_type dog and cat
        data = data[data['animal_type'].str.lower().isin(['dog', 'cat'])]

        # Reset the index
        data = data.reset_index(drop=True)

        # calculate the metrics: num_adoptions, save_rate, live_release_rate for cats and dogs only
        calculate_cat_dog_metric(data)


    return data

# Part 2: Create a function to transform the data
def data_transformation(data):
    # data = data.reset_index(drop=True)
    # Create days_in_shelter
    data['days_in_shelter'] = (data['outcome_date_time'] - data['intake_date_time']).dt.days
    # Filter days_in_shelter maximum is 365 days
    data = data[data['days_in_shelter'] <= 365]

    # Create intake and outcome month and year
    data['outcome_month'] = data['outcome_date_time'].dt.month
    data['outcome_year'] = data['outcome_date_time'].dt.year

    # Create age_group
    # Check if age is numeric or categorical
    if data['age'].str.contains(r'year|month|day', case=False).any():
        # remove special characters and leading or trailing spaces
        data['age'] = data['age'].apply(lambda x: re.sub(r'[^a-zA-Z0-9 ]', '', str(x)))
        data['age'] = data['age'].str.strip()

        age_days = data['age'].apply(lambda x: int(x.split()[0])*365 
                                                       if 'year' in x else (int(x.split()[0])*30 
                                                                            if 'month' in x else int(x.split()[0])))
        age_years = age_days//365
        data['age'] = age_years 
        data['age_group'] = age_years.apply(age_group)
        # tranform_column(data)

    else:
        # calculate the age days if the age is numeric # assuming the original value is in days
        # age_days = data['age'].apply(lambda x: int(x)*365)
        # age_years = age_days//365
        # data['age'] = age_years
        data['age_group'] = data['age'].apply(age_group)
        # tranform_column(data)
    # st.write(data.head(3))
    return data

def transform_data(data):

    data[['new_gender', 'intact_status']] = data['gender'].apply(separate_gender_and_intact_status).apply(pd.Series)

    data[['new_breed', 'is_mix_breed']] = data['breed'].apply(separate_breed).apply(pd.Series)

    # st.write('new_breed', len(data['new_breed']))
    data[['new_colour', 'is_multicolour']] = data['colour'].apply(separate_colour).apply(pd.Series)
    data['is_multicolour'] = data.apply(update_multicolour, axis=1)
    data[['is_black', 'is_white', 'is_brown', 'is_yellow', 'is_gray']] = data['colour'].apply(lambda x: separate_colour_columns(x)).apply(pd.Series)
        
    data.drop(['gender','breed', 'colour'], axis=1, inplace=True)

    data['outcome_type'] = data.pop('outcome_type')
    data['intake_type'] = data['intake_type'].str.lower()
    data['animal_type'] = data['animal_type'].str.lower()
    data['outcome_type'] = data['outcome_type'].str.lower()
    data['intake_condition'] = data['intake_condition'].str.lower()
    final_data = data.reset_index(drop=True)
    # rename the columns
    final_data.rename(columns={'new_breed': 'breed', 'new_colour': 'colour', 'new_gender': 'gender'}, inplace=True)

    return final_data

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
    
    if any(color in row['colour'].lower() for color in colour):
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



# Dashboard functions
def card_metrics(intakes, adoptions, save_rate, live_release_rate):
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(
            label="Number of Intakes",
            value= int(intakes)
        )

    kpi2.metric(
        label="Number of Adoptions",
        value= int(adoptions)
    )
    kpi3.metric(
            label="Save Rate",
            value=f"{save_rate:.2%}"
        )

    kpi4.metric(
        label="Live Release Rate",
        value=f"{live_release_rate:.2%}"
    )

def plot_graphs_sample(df):

    adoption_data = df[df['outcome_type'] == 'adoption']
    adoption_counts_year = adoption_data[['outcome_year', 'animal_type']].value_counts().reset_index(name='count')
    adoption_counts_year = adoption_counts_year.sort_values(['animal_type', 'outcome_year'])

    adoption_counts_month = adoption_data[['outcome_month', 'animal_type']].value_counts().reset_index(name='count')
    adoption_counts_month = adoption_counts_month.sort_values(['animal_type', 'outcome_month'])

    st.markdown("### Cats and Dogs Adoptions")
    fig1 = px.line(adoption_counts_year, x='outcome_year', y = 'count', color='animal_type', markers=True)
    fig1.update_layout(
        xaxis_title="",
        yaxis_title="Adoption Count"
    )

    fig2 = px.line(adoption_counts_month, x='outcome_month', y = 'count', color='animal_type', markers=True)
    fig2.update_layout(
        xaxis_title="",
        yaxis_title="Adoption Count"
    )


    st.write('')
    adoption_data['outcome_date_time'] = pd.to_datetime(adoption_data['outcome_date_time'])
    counts = adoption_data['outcome_date_time'].dt.day_name().value_counts()
    percentage = counts / counts.sum() *100
    # Create a new DataFrame with 'Day' and 'Percentage' columns
    adoption_day_df = pd.DataFrame({'Day': percentage.index, 'Percentage': percentage.values})

    # Sort the DataFrame by 'Day' in chronological order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    adoption_day_df['Day'] = pd.Categorical(adoption_day_df['Day'], categories=day_order, ordered=True)
    adoption_day_df.sort_values(by='Day', inplace=True)

    fig5 = px.bar(adoption_day_df, x='Day', y='Percentage', color='Day')
    fig5.update_layout(xaxis_title="", yaxis_title="Percentage of Adoptions (%)")

    tab1, tab2, tab3 = st.tabs(["Adoption By Year", "Adoption By Month", "Preferred Day for Adoption"])
    with tab1:
        st.plotly_chart(fig1)
    with tab2:
        st.plotly_chart(fig2)
    with tab3:
        st.plotly_chart(fig5)


    # Calculate the average length of stay by year and animal type
    avg_los_year = df.groupby(['outcome_year', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
    avg_los_year = avg_los_year.sort_values(['animal_type', 'outcome_year'])

    avg_los_month = df.groupby(['outcome_month', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
    avg_los_month = avg_los_month.sort_values(['animal_type', 'outcome_month'])

    st.markdown("### Average Length of Stay")
    fig3 = px.line(avg_los_year, x='outcome_year', y='avg_los', color='animal_type', markers=True)
    fig3.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

    fig4 = px.line(avg_los_month, x='outcome_month', y='avg_los', color='animal_type', markers=True)
    fig4.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

    tab3, tab4 = st.tabs(["LOS By Year", "LOS By Month"])
    with tab3:
        st.plotly_chart(fig3)
    with tab4:
        st.plotly_chart(fig4)
    


    st.markdown("### Intake Types")
    intake_data = df['intake_type'].value_counts()
    
    # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
    x = intake_data.index.tolist()
    y = intake_data.values.tolist()
    
    fig6 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
                                marker_colors=px.colors.diverging.Portland,
                                textinfo='label+percent')])
    st.plotly_chart(fig6)

    st.markdown("### Outcome Types")
    outcome_data = df['outcome_type'].value_counts()
    
    # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
    x = outcome_data.index.tolist()
    y = outcome_data.values.tolist()
    
    fig8 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
                                marker_colors=px.colors.diverging.Temps,
                                textinfo='label+percent')])
    st.plotly_chart(fig8)

    
    st.markdown("### Animal Characteristics Analysis")
    #### plot animal breed in LOS - which top 10 dog/cat breed has a longer LOS
    dog_data = df[df['animal_type'] == 'dog']
    cat_data = df[df['animal_type'] == 'cat']

    selected_tab = st.selectbox("Analyse Animal Breed, Gender, Colour: ", ["Top 10 Dog Breed By LOS", 
                                               "Top 10 Cat Breed By LOS", 
                                               "Top 10 Adopted Dog Breed",
                                               "Top 10 Adopted Cat Breed",
                                               "Gender Analysis",
                                               "Colour Analysis"])

    if selected_tab == "Top 10 Dog Breed By LOS":
        # sort the dog breed by average length of stay
        dog_breed_los = dog_data.groupby(['primary_breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
        dog_breed_los = dog_breed_los.sort_values(['avg_los'], ascending=False)

        # only show top 10 dog breed
        dog_breed_los = dog_breed_los.head(10)
        fig7 = px.bar(dog_breed_los, x='primary_breed', y='avg_los', color='primary_breed')
        fig7.update_layout(yaxis_title="Average Length of Stay (Days)")
        st.plotly_chart(fig7)
    
    elif selected_tab == "Top 10 Cat Breed By LOS":

        # sort the cat breed by average length of stay
        cat_breed_los = cat_data.groupby(['primary_breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
        cat_breed_los = cat_breed_los.sort_values(['avg_los'], ascending=False)

        # only show top 10 cat breed
        cat_breed_los = cat_breed_los.head(10)

        fig10 = px.bar(cat_breed_los, x='primary_breed', y='avg_los', color='primary_breed')
        fig10.update_layout(yaxis_title="Average Length of Stay (Days)")
        st.plotly_chart(fig10)
    
    elif selected_tab == "Top 10 Adopted Dog Breed":
        #### plot animal breed by adoption - which top 10 dog/cat breed has the highest adoption rate
        dog_breed_adoption = dog_data.groupby(['primary_breed'])['outcome_type'].value_counts().reset_index(name='count')
        dog_breed_adoption = dog_breed_adoption[dog_breed_adoption['outcome_type'] == 'adoption']
        dog_breed_adoption = dog_breed_adoption.sort_values(['count'], ascending=False)
        dog_breed_adoption = dog_breed_adoption.head(10)
        fig9 = px.bar(dog_breed_adoption, x='primary_breed', y='count', color='primary_breed')
        fig9.update_layout(yaxis_title="Adoption Count")
        st.plotly_chart(fig9)


    elif selected_tab == "Top 10 Adopted Cat Breed":
        cat_breed_adoption = cat_data.groupby(['primary_breed'])['outcome_type'].value_counts().reset_index(name='count')
        cat_breed_adoption = cat_breed_adoption[cat_breed_adoption['outcome_type'] == 'adoption']
        cat_breed_adoption = cat_breed_adoption.sort_values(['count'], ascending=False)
        cat_breed_adoption = cat_breed_adoption.head(10)
        fig11 = px.bar(cat_breed_adoption, x='primary_breed', y='count', color='primary_breed')
        fig11.update_layout(yaxis_title="Adoption Count")
        st.plotly_chart(fig11)
    
    elif selected_tab =="Gender Analysis":
        # Group the data by gender and calculate the counts for cat_data
        cat_gender_data = cat_data['gender'].value_counts().reset_index(name='Count')
        cat_gender_data.rename(columns={'index': 'gender'}, inplace=True)
        cat_gender_data['animal_type'] = 'cat'

        # Group the data by gender and calculate the counts for dog_data
        dog_gender_data = dog_data['gender'].value_counts().reset_index(name='Count')
        dog_gender_data.rename(columns={'index': 'gender'}, inplace=True)
        dog_gender_data['animal_type'] = 'dog'

        # Combine the data for both cat and dog
        combined_data = pd.concat([cat_gender_data, dog_gender_data])

        # Create the stacked bar chart
        fig12 = px.bar(combined_data, x='animal_type', y='Count', color='gender', barmode='stack', text='Count')

        # Update layout to set the title and axis labels
        fig12.update_layout(title='Stacked Bar Chart of Dog and Cat Gender', xaxis_title='', yaxis_title='Count')
        st.plotly_chart(fig12)
    
    elif selected_tab == "Colour Analysis":
        # Group the data by primary_colour and calculate the counts for cat_data
        cat_colour_data = cat_data['primary_colour'].value_counts().reset_index(name='Count')
        cat_colour_data = cat_colour_data.sort_values(['Count'], ascending=False)
        cat_colour_data = cat_colour_data.head(10)
        cat_colour_data.rename(columns={'index': 'primary_colour'}, inplace=True)
        cat_colour_data['animal_type'] = 'cat'


        # Group the data by primary_colour and calculate the counts for dog_data
        dog_colour_data = dog_data['primary_colour'].value_counts().reset_index(name='Count')
        dog_colour_data.rename(columns={'index': 'primary_colour'}, inplace=True)
        dog_colour_data = dog_colour_data.sort_values(['Count'], ascending=False)
        dog_colour_data = dog_colour_data.head(10)
        dog_colour_data['animal_type'] = 'dog'

        # Combine the data for both cat and dog
        combined_data = pd.concat([cat_colour_data, dog_colour_data])

        fig13 = px.bar(cat_colour_data, x='animal_type', y='Count', color='primary_colour', text='Count',
                    color_discrete_sequence=px.colors.diverging.Picnic)
        fig13.update_layout(title='Stacked Bar Chart of Cat Colour', xaxis_title = "", yaxis_title='Count')

        fig13.update_traces(textposition='inside')

        fig14 = px.bar(dog_colour_data, x='animal_type', y='Count', color='primary_colour', text='Count',
                    color_discrete_sequence=px.colors.diverging.Picnic)

        fig14.update_layout(title='Stacked Bar Chart of Dog Colour', xaxis_title = "", yaxis_title='Count')

        fig14.update_traces(textposition='inside')

        # Show the chart
        st.plotly_chart(fig13)
        st.plotly_chart(fig14)

    time.sleep(1)

def plot_graphs_cleaned_data(df):
        adoption_data = df[df['outcome_type'] == 'adoption']
        # st.write('adoption data', adoption_data.head(3))
        adoption_counts_year = adoption_data[['outcome_year', 'animal_type']].value_counts().reset_index(name='count')
        adoption_counts_year = adoption_counts_year.sort_values(['animal_type', 'outcome_year'])
        # st.write('adoption counts year', adoption_counts_year.head(3))

        adoption_counts_month = adoption_data[['outcome_month', 'animal_type']].value_counts().reset_index(name='count')
        adoption_counts_month = adoption_counts_month.sort_values(['animal_type', 'outcome_month'])

        st.markdown("### Cats and Dogs Adoptions")
        fig1 = px.line(adoption_counts_year, x='outcome_year', y = 'count', color='animal_type', markers=True)
        fig1.update_layout(
            xaxis_title="",
            yaxis_title="Adoption Count"
        )

        fig2 = px.line(adoption_counts_month, x='outcome_month', y = 'count', color='animal_type', markers=True)
        fig2.update_layout(
            xaxis_title="",
            yaxis_title="Adoption Count"
        )

        

        # adoption_data['outcome_date_time'] = pd.to_datetime(adoption_data['outcome_date_time'])
        # counts = adoption_data['outcome_date_time'].dt.day_name().value_counts()
        # percentage = counts / counts.sum() *100
        # # Create a new DataFrame with 'Day' and 'Percentage' columns
        # adoption_day_df = pd.DataFrame({'Day': percentage.index, 'Percentage': percentage.values})

        # # Sort the DataFrame by 'Day' in chronological order
        # day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        # adoption_day_df['Day'] = pd.Categorical(adoption_day_df['Day'], categories=day_order, ordered=True)
        # adoption_day_df.sort_values(by='Day', inplace=True)

        # fig5 = px.bar(adoption_day_df, x='Day', y='Percentage', color='Day')
        # fig5.update_layout(xaxis_title="", yaxis_title="Percentage of Adoptions (%)")

        tab1, tab2, tab3 = st.tabs(["Adoption By Year", "Adoption By Month", "Preferred Day for Adoption"])
        with tab1:
            st.plotly_chart(fig1)
        with tab2:
            st.plotly_chart(fig2)
        # with tab3:
        #     st.plotly_chart(fig5)

        # Plot a bar chart for breed
        dog_breed = df[df['animal_type'] == 'dog']
        cat_breed = df[df['animal_type'] == 'cat']

        dog_breed_counts = dog_breed['primary_breed'].value_counts().reset_index(name='count')
        dog_breed_counts = dog_breed_counts.sort_values(['count'], ascending=False)

        cat_breed_counts = cat_breed['primary_breed'].value_counts().reset_index(name='count')
        cat_breed_counts = cat_breed_counts.sort_values(['count'], ascending=False)

        #plot graph
        fig6 = px.bar(dog_breed_counts, x='index', y='count', color='index')
        fig6.update_layout(yaxis_title="Count")
        st.plotly_chart(fig6)

        fig7 = px.bar(cat_breed_counts, x='index', y='count', color='index')
        fig7.update_layout(yaxis_title="Count")
        st.plotly_chart(fig7)


        # # Calculate the average length of stay by year and animal type
        # avg_los_year = df.groupby(['outcome_year', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
        # avg_los_year = avg_los_year.sort_values(['animal_type', 'outcome_year'])

        # avg_los_month = df.groupby(['outcome_month', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
        # avg_los_month = avg_los_month.sort_values(['animal_type', 'outcome_month'])

        # st.markdown("### Average Length of Stay")
        # fig3 = px.line(avg_los_year, x='outcome_year', y='avg_los', color='animal_type', markers=True)
        # fig3.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

        # fig4 = px.line(avg_los_month, x='outcome_month', y='avg_los', color='animal_type', markers=True)
        # fig4.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

        # tab3, tab4 = st.tabs(["LOS By Year", "LOS By Month"])
        # with tab3:
        #     st.plotly_chart(fig3)
        # with tab4:
        #     st.plotly_chart(fig4)
        


        # st.markdown("### Intake Types")
        # intake_data = df['intake_type'].value_counts()
        
        # # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
        # x = intake_data.index.tolist()
        # y = intake_data.values.tolist()
        
        # fig6 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
        #                             marker_colors=px.colors.diverging.Portland,
        #                             textinfo='label+percent')])
        # st.plotly_chart(fig6)

        # st.markdown("### Outcome Types")
        # outcome_data = df['outcome_type'].value_counts()
        
        # # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
        # x = outcome_data.index.tolist()
        # y = outcome_data.values.tolist()
        
        # fig8 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
        #                             marker_colors=px.colors.diverging.Temps,
        #                             textinfo='label+percent')])
        # st.plotly_chart(fig8)

        
        # st.markdown("### Animal Characteristics Analysis")
        # #### plot animal breed in LOS - which top 10 dog/cat breed has a longer LOS
        # dog_data = df[df['animal_type'] == 'dog']
        # cat_data = df[df['animal_type'] == 'cat']

        # selected_tab = st.selectbox("Analyse Animal Breed, Gender, Colour: ", ["Top 10 Dog Breed By LOS", 
        #                                                                        "Top 10 Cat Breed By LOS", 
        #                                                                        "Top 10 Adopted Dog Breed",
        #                                                                        "Top 10 Adopted Cat Breed",
        #                                                                        "Gender Analysis",
        #                                                                        "Colour Analysis"])

        # if selected_tab == "Top 10 Dog Breed By LOS":
        #     # sort the dog breed by average length of stay
        #     dog_breed_los = dog_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
        #     dog_breed_los = dog_breed_los.sort_values(['avg_los'], ascending=False)

        #     # only show top 10 dog breed
        #     dog_breed_los = dog_breed_los.head(10)
        #     fig7 = px.bar(dog_breed_los, x='breed', y='avg_los', color='breed')
        #     fig7.update_layout(yaxis_title="Average Length of Stay (Days)")
        #     st.plotly_chart(fig7)
        
        # elif selected_tab == "Top 10 Cat Breed By LOS":

        #     # sort the cat breed by average length of stay
        #     cat_breed_los = cat_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
        #     cat_breed_los = cat_breed_los.sort_values(['avg_los'], ascending=False)

        #     # only show top 10 cat breed
        #     cat_breed_los = cat_breed_los.head(10)

        #     fig10 = px.bar(cat_breed_los, x='breed', y='avg_los', color='breed')
        #     fig10.update_layout(yaxis_title="Average Length of Stay (Days)")
        #     st.plotly_chart(fig10)
        
        # elif selected_tab == "Top 10 Adopted Dog Breed":
        #     #### plot animal breed by adoption - which top 10 dog/cat breed has the highest adoption rate
        #     dog_breed_adoption = dog_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
        #     dog_breed_adoption = dog_breed_adoption[dog_breed_adoption['outcome_type'] == 'adoption']
        #     dog_breed_adoption = dog_breed_adoption.sort_values(['count'], ascending=False)
        #     dog_breed_adoption = dog_breed_adoption.head(10)
        #     fig9 = px.bar(dog_breed_adoption, x='breed', y='count', color='breed')
        #     fig9.update_layout(yaxis_title="Adoption Count")
        #     st.plotly_chart(fig9)


        # elif selected_tab == "Top 10 Adopted Cat Breed":
        #     cat_breed_adoption = cat_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
        #     cat_breed_adoption = cat_breed_adoption[cat_breed_adoption['outcome_type'] == 'adoption']
        #     cat_breed_adoption = cat_breed_adoption.sort_values(['count'], ascending=False)
        #     cat_breed_adoption = cat_breed_adoption.head(10)
        #     fig11 = px.bar(cat_breed_adoption, x='breed', y='count', color='breed')
        #     fig11.update_layout(yaxis_title="Adoption Count")
        #     st.plotly_chart(fig11)
        
        # elif selected_tab =="Gender Analysis":
        #     # Group the data by gender and calculate the counts for cat_data
        #     cat_gender_data = cat_data['gender'].value_counts().reset_index(name='Count')
        #     cat_gender_data.rename(columns={'index': 'gender'}, inplace=True)
        #     cat_gender_data['animal_type'] = 'cat'

        #     # Group the data by gender and calculate the counts for dog_data
        #     dog_gender_data = dog_data['gender'].value_counts().reset_index(name='Count')
        #     dog_gender_data.rename(columns={'index': 'gender'}, inplace=True)
        #     dog_gender_data['animal_type'] = 'dog'

        #     # Combine the data for both cat and dog
        #     combined_data = pd.concat([cat_gender_data, dog_gender_data])

        #     # Create the stacked bar chart
        #     fig12 = px.bar(combined_data, x='animal_type', y='Count', color='gender', barmode='stack', text='Count')

        #     # Update layout to set the title and axis labels
        #     fig12.update_layout(title='Stacked Bar Chart of Dog and Cat Gender', xaxis_title='', yaxis_title='Count')
        #     st.plotly_chart(fig12)
        
        # elif selected_tab == "Colour Analysis":
        #     # Group the data by primary_colour and calculate the counts for cat_data
        #     cat_colour_data = cat_data['colour'].value_counts().reset_index(name='Count')
        #     cat_colour_data = cat_colour_data.sort_values(['Count'], ascending=False)
        #     cat_colour_data = cat_colour_data.head(10)
        #     cat_colour_data.rename(columns={'index': 'colour'}, inplace=True)
        #     cat_colour_data['animal_type'] = 'cat'


        #     # Group the data by primary_colour and calculate the counts for dog_data
        #     dog_colour_data = dog_data['colour'].value_counts().reset_index(name='Count')
        #     dog_colour_data.rename(columns={'index': 'colour'}, inplace=True)
        #     dog_colour_data = dog_colour_data.sort_values(['Count'], ascending=False)
        #     dog_colour_data = dog_colour_data.head(10)
        #     dog_colour_data['animal_type'] = 'dog'

        #     # Combine the data for both cat and dog
        #     combined_data = pd.concat([cat_colour_data, dog_colour_data])

        #     fig13 = px.bar(cat_colour_data, x='animal_type', y='Count', color='colour', text='Count',
        #                 color_discrete_sequence=px.colors.diverging.Picnic)
        #     fig13.update_layout(title='Stacked Bar Chart of Cat Colour', xaxis_title = "", yaxis_title='Count')

        #     fig13.update_traces(textposition='inside')

        #     fig14 = px.bar(dog_colour_data, x='animal_type', y='Count', color='colour', text='Count',
        #                 color_discrete_sequence=px.colors.diverging.Picnic)

        #     fig14.update_layout(title='Stacked Bar Chart of Dog Colour', xaxis_title = "", yaxis_title='Count')

        #     fig14.update_traces(textposition='inside')

        #     # Show the chart
        #     st.plotly_chart(fig13)
        #     st.plotly_chart(fig14)

        time.sleep(1)


# Prediction functions
def adoption_prediction(df):
    shelter_data = st.session_state.get('cleaned_data')

    shelter_data.drop(['outcome_type'], axis=1, inplace=True)

    prediction_data = shelter_data.copy()

    # intake_condition and intact_status are not present in this dataset
    prediction_data = prediction_data[['animal_type', 'intake_type', 'is_multicolour', 'is_black', 'is_yellow', 'is_gray', 'age', 'age_group', 'gender', 'days_in_shelter', 'outcome_month', 'outcome_year', 'intake_condition', 'intact_status']]

    # rename the columns
    prediction_data = prediction_data.rename(columns={
        'intact_status': 'outcome_intact_status',
        'age_group': 'outcome_age_group'
    })

    # restructure the data
    desired_order = ['animal_type', 'intake_type', 'intake_condition', 'is_multicolour', 'is_black', 'is_yellow', 'is_gray', 'age', 'outcome_age_group', 'gender', 'outcome_intact_status', 'days_in_shelter', 'outcome_month', 'outcome_year']

    new_prediction_data = prediction_data.reindex(columns=desired_order)

    # convert object to category
    new_prediction_data, categorical_col = convert_object_to_category(new_prediction_data)
    # label encoding
    new_prediction_data = label_encoding_categorical_columns(new_prediction_data, categorical_col)

    # feature scaling
    X_norm_data = feature_scaling(new_prediction_data)

    # load the model and make prediction
    model = load('best_model_os_xgb_clf.joblib')
    # prediction = model.predict(X_norm_data)

    # shelter_data['outcome_type'] = prediction
    # # change 1 to "adoption" and 0 to "not_adoption"
    # shelter_data['outcome_type'] = shelter_data['outcome_type'].apply(lambda x: 'adoption' if x == 1 else 'not_adoption')
    
    # Make binary predictions using predict
    binary_prediction = model.predict(X_norm_data)

    # Get the adoptability scores using predict_proba
    prediction_proba = model.predict_proba(X_norm_data)

    # Get the probability of each row being classified as "adoption" (class 1)
    adoptability_scores = prediction_proba[:, 1]

    # Add the binary predictions and adoptability scores to the DataFrame
    shelter_data['binary_prediction'] = binary_prediction
    shelter_data['adoptability_score'] = adoptability_scores

    # Map binary predictions to "adoption" and "not_adoption" for the outcome_type column
    shelter_data['outcome_type'] = shelter_data['binary_prediction'].apply(lambda x: 'adoption' if x == 1 else 'not_adoption')

    # Define the mapping of month numbers to English month names
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    # Map the numeric values to their corresponding English month names
    shelter_data['outcome_month_eng'] = shelter_data['outcome_month'].map({month: month_names[month - 1] for month in shelter_data['outcome_month']})

    # Find the index of the 'outcome_month' column
    outcome_month_idx = shelter_data.columns.get_loc('outcome_month')

    # Insert the 'outcome_month_eng' column beside the 'outcome_month' column
    shelter_data.insert(outcome_month_idx + 1, 'outcome_month_eng', shelter_data.pop('outcome_month_eng'))
    # st.write(shelter_data.head(3))

    return shelter_data

def convert_object_to_category(df):
    # Create an empty list to store the column names
    category_columns = []
    
    # Iterate through each column in the DataFrame
    for col in df.columns:
        if df[col].dtype == 'object':
            # Convert object columns to category data type
            df[col] = df[col].astype('category')
            # Add the column name to the list of category columns
            category_columns.append(col)
        elif col in ['outcome_month', 'outcome_year']:
            # Convert 'outcome_month' and 'outcome_year' columns to category data type
            df[col] = df[col].astype('category')
            # Add the column name to the list of category columns
            category_columns.append(col)
    
    # Return the updated DataFrame and the list of category column names
    return df, category_columns

def label_encoding_categorical_columns(df, categorical_col_names):

    # instantiate label encoder
    lablencoder = LabelEncoder()
    for col in categorical_col_names:
        df[col] = lablencoder.fit_transform(df[col])
    return df
    
def feature_scaling(df):
    # load the scaler
    scaler = load('scaler.joblib')
    # scale the data
    scaled_data = scaler.transform(df)
    return scaled_data


# Plot Prediction functions
def plot_filtered_data(shelter_data):
    # Sidebar filters
    st.sidebar.title("Filters")

    # Sort the unique years in descending order
    unique_years = pd.Series(np.unique(shelter_data['outcome_year']))
    unique_years = unique_years.sort_values(ascending=False)

    # Add a sidebar filter for the year with "All" as default selection
    selected_year = st.sidebar.selectbox("Select Year:", ['All'] + unique_years.tolist(), index=0)

    # Get unique outcome_month and outcome_month_eng
    unique_months = shelter_data['outcome_month'].unique()

    # Sort the unique outcome_month in ascending order
    unique_months = sorted(unique_months)

    # Create a dictionary to map outcome_month to outcome_month_eng
    month_names_map = dict(shelter_data[['outcome_month', 'outcome_month_eng']].values)

    # Map the sorted outcome_month to their corresponding outcome_month_eng
    sorted_month_names = [month_names_map[month] for month in unique_months]

    # Add a "All" option to the beginning of the list
    sorted_month_names.insert(0, "All")

    # Add a sidebar filter for the month with "All" as default selection
    selected_month = st.sidebar.selectbox("Select Month:", sorted_month_names, index=0)

     # Add a sidebar filter for Animal Type with "All" as default selection
    selected_animal_type = st.sidebar.selectbox("Select Animal Type:", ['All', 'cat', 'dog'], index=0)
    # Add a sidebar filter for the adoptability score
    selected_adoptability_score = st.sidebar.slider("Select Adoptability Score: ", 0.0, 1.0, (0.5, 1.0))

    # Filter the results based on the selected filters
    filtered_results = shelter_data[
        (shelter_data['adoptability_score'] >= selected_adoptability_score[0]) &
        (shelter_data['adoptability_score'] <= selected_adoptability_score[1]) &
        (shelter_data['outcome_year'] == selected_year if selected_year != 'All' else True) &
        (shelter_data['outcome_month_eng'] == selected_month if selected_month != 'All' else True) &
        # (shelter_data['breed'] == selected_breeds if selected_breeds != 'All' else True) &
        (shelter_data['animal_type'] == selected_animal_type if selected_animal_type != 'All' else True)
    ]

    # # Display the filtered results, and use them to create graphs and visualizations
    # st.write(filtered_results)

    # Plot the filtered data
    plot_graphs_animal_prediction(filtered_results)

def plot_graphs_animal_prediction(shelter_data):

    # calculating and plot the adoption rate for cats and dogs in a bar chart
    plot_cat_dog_adoption_rate(shelter_data)
    plot_cat_dog_breed_colour(shelter_data)

def plot_cat_dog_adoption_rate(shelter_data):

    st.markdown("#### Cats and Dogs Predicted Adoption Rate")
    # Filter the data for cats and dogs separately
    cat_data = shelter_data[shelter_data['animal_type'] == 'cat']
    dog_data = shelter_data[shelter_data['animal_type'] == 'dog']

    # Count the number of adoptions and total outcomes for each animal type
    cat_total_outcomes = cat_data.shape[0]
    cat_num_adoptions = cat_data['outcome_type'].value_counts().get('adoption', 0)

    dog_total_outcomes = dog_data.shape[0]
    dog_num_adoptions = dog_data['outcome_type'].value_counts().get('adoption', 0)

    # Calculate the adoption rate for cats and dogs
    cat_adoption_rate = cat_num_adoptions / cat_total_outcomes if cat_total_outcomes > 0 else 0
    dog_adoption_rate = dog_num_adoptions / dog_total_outcomes if dog_total_outcomes > 0 else 0

    # Create a bar chart to display the adoption rates for cats and dogs
    fig = go.Figure(data=[
        go.Bar(name='Cats', x=['Cat'], y=[cat_adoption_rate], marker_color='#51EAEA',
            text=[f"{cat_adoption_rate:.2%}"], textposition='inside', textfont_size=18,
            width=0.5),  # Adjust bar width here
        go.Bar(name='Dogs', x=['Dog'], y=[dog_adoption_rate], marker_color='#0079FF',
            text=[f"{dog_adoption_rate:.2%}"], textposition='inside', textfont_size=18,
            width=0.5)  # Adjust bar width here
    ])

    # Customize the layout of the bar chart
    fig.update_layout(
        xaxis_title='',
        yaxis_title='Adoption Rate',
        yaxis_tickformat='.2%',  # Display as percentage
        yaxis_range=[0, 1],
        legend_title='Animal Type',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Add a gap between the bars
        bargap=0.1
    )

    # Show the chart
    st.plotly_chart(fig)

def plot_cat_dog_breed_colour(shelter_data):

    custom_color_scheme = ['#51EAEA', '#2D31FA', '#47B5FF', '#59C1BD', '#A0E4CB', '#CFF5E7', '#00FFDD']
    purple =['#590696', '#3120E0', '#6C00FF','#6C4AB6', '#8D72E1', '#AA77FF', '#D4ADFC']


    # plot breed and colour
    st.markdown("#### Animal Breed and Gender Analysis")

    animal_breed = shelter_data['breed'].value_counts().head(10)

    fig1 = px.bar(animal_breed, title='Breed Bar Chart', x = animal_breed.index, y = animal_breed.values, color=animal_breed.values,
                    color_continuous_scale=custom_color_scheme, labels={'x': 'Animal Breed', 'y': 'Count'})
    fig1.update_layout(showlegend=False)

    # plot cat breed
    animal_colour = shelter_data['colour'].value_counts().head(10)

    fig2 = px.bar(animal_colour, title='Colour Bar Chart',x=animal_colour.index, y=animal_colour.values, color=animal_colour.values,
                    color_continuous_scale='spectral', labels={'x': 'Animal Colour', 'y': 'Count'})
    fig2.update_layout(showlegend=False)

    mixed_breed = shelter_data['is_mix_breed'].value_counts()
    x = mixed_breed.index.tolist()
    y = mixed_breed.values.tolist()

    fig3 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
                                    marker_colors=purple,
                                    textinfo='label+percent')])
    # add chart title
    fig3.update_layout(title_text='Is Animal Mixed Breed?')


    # 
    colour_bool_counts = shelter_data[['is_multicolour', 'is_black','is_white', 'is_brown', 'is_yellow', 'is_gray' ]].value_counts()

    # Convert the index of the counts Series to a DataFrame
    counts_df = colour_bool_counts.reset_index()

    # Rename the columns
    counts_df.columns = ['is_multicolour', 'is_black', 'is_white', 'is_brown', 'is_yellow', 'is_gray', 'count']

    # Melt the DataFrame to convert the columns to rows for plotting
    counts_melted = pd.melt(counts_df, id_vars=['count'], value_vars=['is_multicolour', 'is_black', 'is_white', 'is_brown', 'is_yellow', 'is_gray'])

    # Create the stacked bar chart
    fig4 = px.bar(counts_melted, x='variable', y='count', color='value', barmode='stack', labels={'variable': 'Color', 'count': 'Count'},
                title='Stacked Bar Chart of Color Counts', color_discrete_sequence=['#51EAEA', '#0079FF'])
    
    # Customize the layout of the bar chart
    fig4.update_layout(
        xaxis_title='',
        yaxis_title='Count',
        legend_title='Color',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Add a gap between the bars
        bargap=0.1
    )

    # gender by outcome_intact_status
    # animal_gender_intact_counts = shelter_data[['gender', 'outcome_intact_status']].value_counts()

    # counts_df = animal_gender_intact_counts.reset_index()

    # Get the counts of each combination of gender and outcome_intact_status
    animal_gender = shelter_data[['gender', 'intact_status']].value_counts().reset_index(name='count')

    # Create the stacked bar chart
    fig5 = px.bar(animal_gender, x='gender', y='count', color='intact_status', barmode='stack',
                labels={'gender': 'Gender', 'count': 'Count', 'intact_status': 'Intact Status'},
                title='Stacked Bar Chart of Gender and Intact Status Counts',
                color_discrete_sequence=['#51EAEA', '#0079FF', '#FFDEB4'])

    # Customize the layout of the bar chart
    fig5.update_layout(
        legend_title='Intact Status',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Add a gap between the bars
        bargap=0.1
    )

    # Plot histogram for age by gender male and female
    fig6 = px.histogram(shelter_data, title="Histogram Age by Gender",x="age", color="gender")

    age_group_count = shelter_data['age_group'].value_counts()

    # Convert the Pandas Series to a DataFrame
    age_group_df = age_group_count.reset_index()
    age_group_df.columns = ['Age Group', 'Count']

    # Create the bar chart
    fig7 = px.bar(age_group_df, x='Age Group', y='Count', color='Count',
                color_continuous_scale=purple, labels={'x': 'Age Group', 'y': 'Count'},
                title='Age Group Bar Chart')
    
    # Define the custom color map for 'outcome_type'
    color_map = {'not_adoption': '#F11A7B', 'adoption': '#2FA4FF'}#2FA4FF

    # Create the scatter plot
    fig8 = px.scatter(shelter_data, x="age", y="days_in_shelter", color="outcome_type",
                    color_discrete_map=color_map,
                    title="Scatter Plot of Age and Length of Stay")
    
    # edit y axis title
    fig8.update_yaxes(title_text='Length of Stay (Days)')
    fig8.update_xaxes(title_text='Age (Years)')


    # plot the box plot by each intake type
    fig9 = px.box(shelter_data, y="intake_type", x="days_in_shelter", color="outcome_type",
                labels={'intake_type': 'Intake Type', 'days_in_shelter': 'Length of Stay (Days)'},
                title="Box Plot of Length of Stay by Intake Type")
    fig9.update_traces(quartilemethod="exclusive")
    # Customize the layout of the box plot
    fig9.update_layout(
        xaxis_title='Length of Stay (Days)',
        yaxis_title='Intake Type',
        legend_title='Outcome Type',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # plot average length of stay by breed to show the top 10 breeds

    # Get the average length of stay for each breed
    breed_los = shelter_data.groupby('breed')['days_in_shelter'].mean().reset_index(name='avg_los')

    # Sort the breeds by their average length of stay
    breed_los = breed_los.sort_values(by='avg_los', ascending=False)

    # Get the top 10 breeds by average length of stay
    top_10_breeds = breed_los.head(10)

    # Create the bar chart
    fig10 = px.bar(top_10_breeds, x='breed', y='avg_los', color='avg_los',
                color_continuous_scale='spectral',
                   labels={'breed': 'Breed', 'avg_los': 'ALOS (Days)'},
                title='Top 10 Breeds by Average Length of Stay')
    
    # Customize the layout of the bar chart
    fig10.update_layout(
        xaxis_title='',
        yaxis_title='Average Length of Stay (Days)'
    )


    # plot the graphs in tabs
    tab1, tab2, tab3 = st.tabs(["Breed Analysis", "Gender Analysis", "Age and LOS Analysis"])
    with tab1:
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.plotly_chart(fig3)
        st.plotly_chart(fig4)

    with tab2:
        st.plotly_chart(fig5)
        st.plotly_chart(fig6)

    with tab3:
        st.plotly_chart(fig7)
        st.plotly_chart(fig8)
        st.plotly_chart(fig9)
        st.plotly_chart(fig10)

