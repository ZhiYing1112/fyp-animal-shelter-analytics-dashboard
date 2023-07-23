# Import all the necessary libraries
import streamlit as st
import pandas as pd
import xgboost as xgb
import time
import re
import plotly.express as px
import plotly.graph_objects as go
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
        # st.write(data.head(3))
        # preprocess the data
        initial_cleaning_data = initial_preprocessing(data)
        # st.write(initial_cleaning_data.head(3))

        # transform data columns
        transformed_data = data_transformation(initial_cleaning_data)

        # testing
        # st.write('breed_test', len(transformed_data['breed']))


        # if transformed_data['gender'].str.lower().str.contains('neutered|spayed|intact').any():
        #     transformed_data[['new_gender', 'intact_status']] = transformed_data['gender'].apply(separate_gender_and_intact_status).apply(pd.Series)
        #     transformed_data.drop(['gender'], axis=1, inplace=True)

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
        status_text.text("Data preprocessing complete!")

        return final_data


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

def change_data_type_calc_metrics(data):
    # change data type
    data['intake_date_time'] = pd.to_datetime(data['intake_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))
    data['outcome_date_time'] = pd.to_datetime(data['outcome_date_time'].apply(lambda x: parser.parse(x, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x))

    # calculate number of intakes for each animal_id
    total_num_intakes = data['intake_type'].count()
    # num_adoptions is when outcome_type is adoption
    total_num_adoptions = data[data['outcome_type'] == 'Adoption']['outcome_type'].count()
    # save_rate is Intake minus Euthanasia Outcomes divided by num Intake
    num_euthanasia = data[data['outcome_type'] == 'Euthanasia']['outcome_type'].count()
    save_rate = (total_num_intakes - num_euthanasia) / total_num_intakes
    # live_release_rate is the number of live outcomes divided by the number of intakes
    num_death_in_shelter = data[data['outcome_type'] == 'Died']['outcome_type'].count()
    live_release_rate = (total_num_intakes - num_death_in_shelter) / total_num_intakes

    st.session_state['total_num_intakes'] = total_num_intakes
    st.session_state['total_num_adoptions'] = total_num_adoptions
    st.session_state['save_rate'] = save_rate
    st.session_state['live_release_rate'] = live_release_rate

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


# Part 1: Initial data preprocessing: missing data, data type, duplicates, filter, sort.
def initial_preprocessing(data):

    if data is not None:

        data = change_data_type_calc_metrics(data)

        data = data.sort_values(by=['animal_id', 'intake_date_time', 'outcome_date_time'], ascending=[True, False, False])
        
        # data = data.groupby('animal_id').head(1)
        
        # relevant_vars = ['animal_id', 'intake_date_time', 'breed', 'colour', 'animal_type', 'age', 'gender', 'outcome_date_time', 
        #                  'outcome_type', 'intake_type']
    
        # data = data.drop(columns=[col for col in data.columns if col not in relevant_vars])

        data = remove_missing_data(data)

        # data = data.drop(data[data['outcome_date_time'] < data['intake_date_time']].index, axis=0)

        # Filter the data to only have animal_type dog and cat
        data = data[data['animal_type'].str.lower().isin(['dog', 'cat'])]

        # Reset the index
        data = data.reset_index(drop=True)

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
def card_metrics(intakes, adoptions, ani_count, save_rate, live_rate):
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric(
            label="Number of Intakes",
            value= int(intakes)
        )

    kpi2.metric(
        label="Number of Adoptions",
        value= int(adoptions)
    )

    kpi3.metric(
        label="Intake Animal Count",
        value= int(ani_count)
    )

    kpi4.metric(
        label="Live Release Rate",
        value=f"{live_rate:.2%}"
    )

    kpi5.metric(
        label="Save Rate",
        value=f"{save_rate:.2%}"
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
            dog_breed_los = dog_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
            dog_breed_los = dog_breed_los.sort_values(['avg_los'], ascending=False)

            # only show top 10 dog breed
            dog_breed_los = dog_breed_los.head(10)
            fig7 = px.bar(dog_breed_los, x='breed', y='avg_los', color='breed')
            fig7.update_layout(yaxis_title="Average Length of Stay (Days)")
            st.plotly_chart(fig7)
        
        elif selected_tab == "Top 10 Cat Breed By LOS":

            # sort the cat breed by average length of stay
            cat_breed_los = cat_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
            cat_breed_los = cat_breed_los.sort_values(['avg_los'], ascending=False)

            # only show top 10 cat breed
            cat_breed_los = cat_breed_los.head(10)

            fig10 = px.bar(cat_breed_los, x='breed', y='avg_los', color='breed')
            fig10.update_layout(yaxis_title="Average Length of Stay (Days)")
            st.plotly_chart(fig10)
        
        elif selected_tab == "Top 10 Adopted Dog Breed":
            #### plot animal breed by adoption - which top 10 dog/cat breed has the highest adoption rate
            dog_breed_adoption = dog_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
            dog_breed_adoption = dog_breed_adoption[dog_breed_adoption['outcome_type'] == 'adoption']
            dog_breed_adoption = dog_breed_adoption.sort_values(['count'], ascending=False)
            dog_breed_adoption = dog_breed_adoption.head(10)
            fig9 = px.bar(dog_breed_adoption, x='breed', y='count', color='breed')
            fig9.update_layout(yaxis_title="Adoption Count")
            st.plotly_chart(fig9)


        elif selected_tab == "Top 10 Adopted Cat Breed":
            cat_breed_adoption = cat_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
            cat_breed_adoption = cat_breed_adoption[cat_breed_adoption['outcome_type'] == 'adoption']
            cat_breed_adoption = cat_breed_adoption.sort_values(['count'], ascending=False)
            cat_breed_adoption = cat_breed_adoption.head(10)
            fig11 = px.bar(cat_breed_adoption, x='breed', y='count', color='breed')
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
            cat_colour_data = cat_data['colour'].value_counts().reset_index(name='Count')
            cat_colour_data = cat_colour_data.sort_values(['Count'], ascending=False)
            cat_colour_data = cat_colour_data.head(10)
            cat_colour_data.rename(columns={'index': 'colour'}, inplace=True)
            cat_colour_data['animal_type'] = 'cat'


            # Group the data by primary_colour and calculate the counts for dog_data
            dog_colour_data = dog_data['colour'].value_counts().reset_index(name='Count')
            dog_colour_data.rename(columns={'index': 'colour'}, inplace=True)
            dog_colour_data = dog_colour_data.sort_values(['Count'], ascending=False)
            dog_colour_data = dog_colour_data.head(10)
            dog_colour_data['animal_type'] = 'dog'

            # Combine the data for both cat and dog
            combined_data = pd.concat([cat_colour_data, dog_colour_data])

            fig13 = px.bar(cat_colour_data, x='animal_type', y='Count', color='colour', text='Count',
                        color_discrete_sequence=px.colors.diverging.Picnic)
            fig13.update_layout(title='Stacked Bar Chart of Cat Colour', xaxis_title = "", yaxis_title='Count')

            fig13.update_traces(textposition='inside')

            fig14 = px.bar(dog_colour_data, x='animal_type', y='Count', color='colour', text='Count',
                        color_discrete_sequence=px.colors.diverging.Picnic)

            fig14.update_layout(title='Stacked Bar Chart of Dog Colour', xaxis_title = "", yaxis_title='Count')

            fig14.update_traces(textposition='inside')

            # Show the chart
            st.plotly_chart(fig13)
            st.plotly_chart(fig14)

        time.sleep(1)







# 3.
# Create a function to import the scaler and model.joblib files and make predictions on animal adoption.




# 4.
# Then create multiple functions to calculate each of the metrics
# Use the calculated field to plot the graphs using plotly and streamlit functions and elements


# Create a title for the app
# st.write('Hello world!')

