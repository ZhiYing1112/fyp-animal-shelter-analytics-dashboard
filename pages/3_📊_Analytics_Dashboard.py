import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import data_functions as dip

st.set_page_config(
    page_title="Shelter Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create a title for the app
st.title('Shelter Analytics Dashboard 📊')


def main_function():

    if st.session_state.get('cleaned_data') is not None:
        total_num_intakes = st.session_state.get('total_num_intakes')
        total_num_adoptions = st.session_state.get('total_num_adoptions')
        intake_animal_count = st.session_state.get('intake_animal_count')
        save_rate = st.session_state.get('save_rate')
        live_release_rate = st.session_state.get('live_release_rate')
        shelter_data = st.session_state.get('cleaned_data')

        dip.card_metrics(total_num_intakes, total_num_adoptions, intake_animal_count, save_rate, live_release_rate)
        dip.plot_graphs_cleaned_data(shelter_data)

    else:
        st.info('Note: The below shows the sample data for demonstration purposes only. Please upload your own dataset at "📝 Getting Started" Page.')
        st.write('')
        dip.card_metrics(34578, 6790, 31092, 0.89124, 0.881378)
        dip.plot_graphs_sample(pd.read_csv('austin_sample_data.csv'))



# def card_metrics(intakes, adoptions, ani_count, save_rate, live_rate):
#     kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
#     kpi1.metric(
#             label="Number of Intakes",
#             value= int(intakes)
#         )

#     kpi2.metric(
#         label="Number of Adoptions",
#         value= int(adoptions)
#     )

#     kpi3.metric(
#         label="Intake Animal Count",
#         value= int(ani_count)
#     )

#     kpi4.metric(
#         label="Live Release Rate",
#         value=f"{live_rate:.2%}"
#     )

#     kpi5.metric(
#         label="Save Rate",
#         value=f"{save_rate:.2%}"
#     )

# def plot_graphs_sample(df):

#     adoption_data = df[df['outcome_type'] == 'adoption']
#     adoption_counts_year = adoption_data[['outcome_year', 'animal_type']].value_counts().reset_index(name='count')
#     adoption_counts_year = adoption_counts_year.sort_values(['animal_type', 'outcome_year'])

#     adoption_counts_month = adoption_data[['outcome_month', 'animal_type']].value_counts().reset_index(name='count')
#     adoption_counts_month = adoption_counts_month.sort_values(['animal_type', 'outcome_month'])

#     st.markdown("### Cats and Dogs Adoptions")
#     fig1 = px.line(adoption_counts_year, x='outcome_year', y = 'count', color='animal_type', markers=True)
#     fig1.update_layout(
#         xaxis_title="",
#         yaxis_title="Adoption Count"
#     )

#     fig2 = px.line(adoption_counts_month, x='outcome_month', y = 'count', color='animal_type', markers=True)
#     fig2.update_layout(
#         xaxis_title="",
#         yaxis_title="Adoption Count"
#     )


#     st.write('')
#     adoption_data['outcome_date_time'] = pd.to_datetime(adoption_data['outcome_date_time'])
#     counts = adoption_data['outcome_date_time'].dt.day_name().value_counts()
#     percentage = counts / counts.sum() *100
#     # Create a new DataFrame with 'Day' and 'Percentage' columns
#     adoption_day_df = pd.DataFrame({'Day': percentage.index, 'Percentage': percentage.values})

#     # Sort the DataFrame by 'Day' in chronological order
#     day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#     adoption_day_df['Day'] = pd.Categorical(adoption_day_df['Day'], categories=day_order, ordered=True)
#     adoption_day_df.sort_values(by='Day', inplace=True)

#     fig5 = px.bar(adoption_day_df, x='Day', y='Percentage', color='Day')
#     fig5.update_layout(xaxis_title="", yaxis_title="Percentage of Adoptions (%)")

#     tab1, tab2, tab3 = st.tabs(["Adoption By Year", "Adoption By Month", "Preferred Day for Adoption"])
#     with tab1:
#         st.plotly_chart(fig1)
#     with tab2:
#         st.plotly_chart(fig2)
#     with tab3:
#         st.plotly_chart(fig5)


#     # Calculate the average length of stay by year and animal type
#     avg_los_year = df.groupby(['outcome_year', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
#     avg_los_year = avg_los_year.sort_values(['animal_type', 'outcome_year'])

#     avg_los_month = df.groupby(['outcome_month', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
#     avg_los_month = avg_los_month.sort_values(['animal_type', 'outcome_month'])

#     st.markdown("### Average Length of Stay")
#     fig3 = px.line(avg_los_year, x='outcome_year', y='avg_los', color='animal_type', markers=True)
#     fig3.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

#     fig4 = px.line(avg_los_month, x='outcome_month', y='avg_los', color='animal_type', markers=True)
#     fig4.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

#     tab3, tab4 = st.tabs(["LOS By Year", "LOS By Month"])
#     with tab3:
#         st.plotly_chart(fig3)
#     with tab4:
#         st.plotly_chart(fig4)
    


#     st.markdown("### Intake Types")
#     intake_data = df['intake_type'].value_counts()
    
#     # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
#     x = intake_data.index.tolist()
#     y = intake_data.values.tolist()
    
#     fig6 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
#                                 marker_colors=px.colors.diverging.Portland,
#                                 textinfo='label+percent')])
#     st.plotly_chart(fig6)

#     st.markdown("### Outcome Types")
#     outcome_data = df['outcome_type'].value_counts()
    
#     # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
#     x = outcome_data.index.tolist()
#     y = outcome_data.values.tolist()
    
#     fig8 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
#                                 marker_colors=px.colors.diverging.Temps,
#                                 textinfo='label+percent')])
#     st.plotly_chart(fig8)

    
#     st.markdown("### Animal Characteristics Analysis")
#     #### plot animal breed in LOS - which top 10 dog/cat breed has a longer LOS
#     dog_data = df[df['animal_type'] == 'dog']
#     cat_data = df[df['animal_type'] == 'cat']

#     selected_tab = st.selectbox("Analyse Animal Breed, Gender, Colour: ", ["Top 10 Dog Breed By LOS", 
#                                                "Top 10 Cat Breed By LOS", 
#                                                "Top 10 Adopted Dog Breed",
#                                                "Top 10 Adopted Cat Breed",
#                                                "Gender Analysis",
#                                                "Colour Analysis"])

#     if selected_tab == "Top 10 Dog Breed By LOS":
#         # sort the dog breed by average length of stay
#         dog_breed_los = dog_data.groupby(['primary_breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
#         dog_breed_los = dog_breed_los.sort_values(['avg_los'], ascending=False)

#         # only show top 10 dog breed
#         dog_breed_los = dog_breed_los.head(10)
#         fig7 = px.bar(dog_breed_los, x='primary_breed', y='avg_los', color='primary_breed')
#         fig7.update_layout(yaxis_title="Average Length of Stay (Days)")
#         st.plotly_chart(fig7)
    
#     elif selected_tab == "Top 10 Cat Breed By LOS":

#         # sort the cat breed by average length of stay
#         cat_breed_los = cat_data.groupby(['primary_breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
#         cat_breed_los = cat_breed_los.sort_values(['avg_los'], ascending=False)

#         # only show top 10 cat breed
#         cat_breed_los = cat_breed_los.head(10)

#         fig10 = px.bar(cat_breed_los, x='primary_breed', y='avg_los', color='primary_breed')
#         fig10.update_layout(yaxis_title="Average Length of Stay (Days)")
#         st.plotly_chart(fig10)
    
#     elif selected_tab == "Top 10 Adopted Dog Breed":
#         #### plot animal breed by adoption - which top 10 dog/cat breed has the highest adoption rate
#         dog_breed_adoption = dog_data.groupby(['primary_breed'])['outcome_type'].value_counts().reset_index(name='count')
#         dog_breed_adoption = dog_breed_adoption[dog_breed_adoption['outcome_type'] == 'adoption']
#         dog_breed_adoption = dog_breed_adoption.sort_values(['count'], ascending=False)
#         dog_breed_adoption = dog_breed_adoption.head(10)
#         fig9 = px.bar(dog_breed_adoption, x='primary_breed', y='count', color='primary_breed')
#         fig9.update_layout(yaxis_title="Adoption Count")
#         st.plotly_chart(fig9)


#     elif selected_tab == "Top 10 Adopted Cat Breed":
#         cat_breed_adoption = cat_data.groupby(['primary_breed'])['outcome_type'].value_counts().reset_index(name='count')
#         cat_breed_adoption = cat_breed_adoption[cat_breed_adoption['outcome_type'] == 'adoption']
#         cat_breed_adoption = cat_breed_adoption.sort_values(['count'], ascending=False)
#         cat_breed_adoption = cat_breed_adoption.head(10)
#         fig11 = px.bar(cat_breed_adoption, x='primary_breed', y='count', color='primary_breed')
#         fig11.update_layout(yaxis_title="Adoption Count")
#         st.plotly_chart(fig11)
    
#     elif selected_tab =="Gender Analysis":
#         # Group the data by gender and calculate the counts for cat_data
#         cat_gender_data = cat_data['gender'].value_counts().reset_index(name='Count')
#         cat_gender_data.rename(columns={'index': 'gender'}, inplace=True)
#         cat_gender_data['animal_type'] = 'cat'

#         # Group the data by gender and calculate the counts for dog_data
#         dog_gender_data = dog_data['gender'].value_counts().reset_index(name='Count')
#         dog_gender_data.rename(columns={'index': 'gender'}, inplace=True)
#         dog_gender_data['animal_type'] = 'dog'

#         # Combine the data for both cat and dog
#         combined_data = pd.concat([cat_gender_data, dog_gender_data])

#         # Create the stacked bar chart
#         fig12 = px.bar(combined_data, x='animal_type', y='Count', color='gender', barmode='stack', text='Count')

#         # Update layout to set the title and axis labels
#         fig12.update_layout(title='Stacked Bar Chart of Dog and Cat Gender', xaxis_title='', yaxis_title='Count')
#         st.plotly_chart(fig12)
    
#     elif selected_tab == "Colour Analysis":
#         # Group the data by primary_colour and calculate the counts for cat_data
#         cat_colour_data = cat_data['primary_colour'].value_counts().reset_index(name='Count')
#         cat_colour_data = cat_colour_data.sort_values(['Count'], ascending=False)
#         cat_colour_data = cat_colour_data.head(10)
#         cat_colour_data.rename(columns={'index': 'primary_colour'}, inplace=True)
#         cat_colour_data['animal_type'] = 'cat'


#         # Group the data by primary_colour and calculate the counts for dog_data
#         dog_colour_data = dog_data['primary_colour'].value_counts().reset_index(name='Count')
#         dog_colour_data.rename(columns={'index': 'primary_colour'}, inplace=True)
#         dog_colour_data = dog_colour_data.sort_values(['Count'], ascending=False)
#         dog_colour_data = dog_colour_data.head(10)
#         dog_colour_data['animal_type'] = 'dog'

#         # Combine the data for both cat and dog
#         combined_data = pd.concat([cat_colour_data, dog_colour_data])

#         fig13 = px.bar(cat_colour_data, x='animal_type', y='Count', color='primary_colour', text='Count',
#                     color_discrete_sequence=px.colors.diverging.Picnic)
#         fig13.update_layout(title='Stacked Bar Chart of Cat Colour', xaxis_title = "", yaxis_title='Count')

#         fig13.update_traces(textposition='inside')

#         fig14 = px.bar(dog_colour_data, x='animal_type', y='Count', color='primary_colour', text='Count',
#                     color_discrete_sequence=px.colors.diverging.Picnic)

#         fig14.update_layout(title='Stacked Bar Chart of Dog Colour', xaxis_title = "", yaxis_title='Count')

#         fig14.update_traces(textposition='inside')

#         # Show the chart
#         st.plotly_chart(fig13)
#         st.plotly_chart(fig14)

#     time.sleep(1)

# def plot_graphs_cleaned_data(df):
#         adoption_data = df[df['outcome_type'] == 'adoption']
#         adoption_counts_year = adoption_data[['outcome_year', 'animal_type']].value_counts().reset_index(name='count')
#         adoption_counts_year = adoption_counts_year.sort_values(['animal_type', 'outcome_year'])

#         adoption_counts_month = adoption_data[['outcome_month', 'animal_type']].value_counts().reset_index(name='count')
#         adoption_counts_month = adoption_counts_month.sort_values(['animal_type', 'outcome_month'])

#         st.markdown("### Cats and Dogs Adoptions")
#         fig1 = px.line(adoption_counts_year, x='outcome_year', y = 'count', color='animal_type', markers=True)
#         fig1.update_layout(
#             xaxis_title="",
#             yaxis_title="Adoption Count"
#         )

#         fig2 = px.line(adoption_counts_month, x='outcome_month', y = 'count', color='animal_type', markers=True)
#         fig2.update_layout(
#             xaxis_title="",
#             yaxis_title="Adoption Count"
#         )


#         st.write('')
#         adoption_data['outcome_date_time'] = pd.to_datetime(adoption_data['outcome_date_time'])
#         counts = adoption_data['outcome_date_time'].dt.day_name().value_counts()
#         percentage = counts / counts.sum() *100
#         # Create a new DataFrame with 'Day' and 'Percentage' columns
#         adoption_day_df = pd.DataFrame({'Day': percentage.index, 'Percentage': percentage.values})

#         # Sort the DataFrame by 'Day' in chronological order
#         day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#         adoption_day_df['Day'] = pd.Categorical(adoption_day_df['Day'], categories=day_order, ordered=True)
#         adoption_day_df.sort_values(by='Day', inplace=True)

#         fig5 = px.bar(adoption_day_df, x='Day', y='Percentage', color='Day')
#         fig5.update_layout(xaxis_title="", yaxis_title="Percentage of Adoptions (%)")

#         tab1, tab2, tab3 = st.tabs(["Adoption By Year", "Adoption By Month", "Preferred Day for Adoption"])
#         with tab1:
#             st.plotly_chart(fig1)
#         with tab2:
#             st.plotly_chart(fig2)
#         with tab3:
#             st.plotly_chart(fig5)


#         # Calculate the average length of stay by year and animal type
#         avg_los_year = df.groupby(['outcome_year', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
#         avg_los_year = avg_los_year.sort_values(['animal_type', 'outcome_year'])

#         avg_los_month = df.groupby(['outcome_month', 'animal_type'])['days_in_shelter'].mean().reset_index(name='avg_los')
#         avg_los_month = avg_los_month.sort_values(['animal_type', 'outcome_month'])

#         st.markdown("### Average Length of Stay")
#         fig3 = px.line(avg_los_year, x='outcome_year', y='avg_los', color='animal_type', markers=True)
#         fig3.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

#         fig4 = px.line(avg_los_month, x='outcome_month', y='avg_los', color='animal_type', markers=True)
#         fig4.update_layout(xaxis_title="", yaxis_title="Average Length of Stay (Days)")

#         tab3, tab4 = st.tabs(["LOS By Year", "LOS By Month"])
#         with tab3:
#             st.plotly_chart(fig3)
#         with tab4:
#             st.plotly_chart(fig4)
        


#         st.markdown("### Intake Types")
#         intake_data = df['intake_type'].value_counts()
        
#         # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
#         x = intake_data.index.tolist()
#         y = intake_data.values.tolist()
        
#         fig6 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
#                                     marker_colors=px.colors.diverging.Portland,
#                                     textinfo='label+percent')])
#         st.plotly_chart(fig6)

#         st.markdown("### Outcome Types")
#         outcome_data = df['outcome_type'].value_counts()
        
#         # intake_data_df = pd.DataFrame({'Intake Type': intake_data['index'], 'Count': intake_data['Count']})
#         x = outcome_data.index.tolist()
#         y = outcome_data.values.tolist()
        
#         fig8 = go.Figure(data=[go.Pie(labels=x, values = y, hole=0.45,
#                                     marker_colors=px.colors.diverging.Temps,
#                                     textinfo='label+percent')])
#         st.plotly_chart(fig8)

        
#         st.markdown("### Animal Characteristics Analysis")
#         #### plot animal breed in LOS - which top 10 dog/cat breed has a longer LOS
#         dog_data = df[df['animal_type'] == 'dog']
#         cat_data = df[df['animal_type'] == 'cat']

#         selected_tab = st.selectbox("Analyse Animal Breed, Gender, Colour: ", ["Top 10 Dog Breed By LOS", 
#                                                 "Top 10 Cat Breed By LOS", 
#                                                 "Top 10 Adopted Dog Breed",
#                                                 "Top 10 Adopted Cat Breed",
#                                                 "Gender Analysis",
#                                                 "Colour Analysis"])

#         if selected_tab == "Top 10 Dog Breed By LOS":
#             # sort the dog breed by average length of stay
#             dog_breed_los = dog_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
#             dog_breed_los = dog_breed_los.sort_values(['avg_los'], ascending=False)

#             # only show top 10 dog breed
#             dog_breed_los = dog_breed_los.head(10)
#             fig7 = px.bar(dog_breed_los, x='breed', y='avg_los', color='breed')
#             fig7.update_layout(yaxis_title="Average Length of Stay (Days)")
#             st.plotly_chart(fig7)
        
#         elif selected_tab == "Top 10 Cat Breed By LOS":

#             # sort the cat breed by average length of stay
#             cat_breed_los = cat_data.groupby(['breed'])['days_in_shelter'].mean().reset_index(name='avg_los')
#             cat_breed_los = cat_breed_los.sort_values(['avg_los'], ascending=False)

#             # only show top 10 cat breed
#             cat_breed_los = cat_breed_los.head(10)

#             fig10 = px.bar(cat_breed_los, x='breed', y='avg_los', color='breed')
#             fig10.update_layout(yaxis_title="Average Length of Stay (Days)")
#             st.plotly_chart(fig10)
        
#         elif selected_tab == "Top 10 Adopted Dog Breed":
#             #### plot animal breed by adoption - which top 10 dog/cat breed has the highest adoption rate
#             dog_breed_adoption = dog_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
#             dog_breed_adoption = dog_breed_adoption[dog_breed_adoption['outcome_type'] == 'adoption']
#             dog_breed_adoption = dog_breed_adoption.sort_values(['count'], ascending=False)
#             dog_breed_adoption = dog_breed_adoption.head(10)
#             fig9 = px.bar(dog_breed_adoption, x='breed', y='count', color='breed')
#             fig9.update_layout(yaxis_title="Adoption Count")
#             st.plotly_chart(fig9)


#         elif selected_tab == "Top 10 Adopted Cat Breed":
#             cat_breed_adoption = cat_data.groupby(['breed'])['outcome_type'].value_counts().reset_index(name='count')
#             cat_breed_adoption = cat_breed_adoption[cat_breed_adoption['outcome_type'] == 'adoption']
#             cat_breed_adoption = cat_breed_adoption.sort_values(['count'], ascending=False)
#             cat_breed_adoption = cat_breed_adoption.head(10)
#             fig11 = px.bar(cat_breed_adoption, x='breed', y='count', color='breed')
#             fig11.update_layout(yaxis_title="Adoption Count")
#             st.plotly_chart(fig11)
        
#         elif selected_tab =="Gender Analysis":
#             # Group the data by gender and calculate the counts for cat_data
#             cat_gender_data = cat_data['gender'].value_counts().reset_index(name='Count')
#             cat_gender_data.rename(columns={'index': 'gender'}, inplace=True)
#             cat_gender_data['animal_type'] = 'cat'

#             # Group the data by gender and calculate the counts for dog_data
#             dog_gender_data = dog_data['gender'].value_counts().reset_index(name='Count')
#             dog_gender_data.rename(columns={'index': 'gender'}, inplace=True)
#             dog_gender_data['animal_type'] = 'dog'

#             # Combine the data for both cat and dog
#             combined_data = pd.concat([cat_gender_data, dog_gender_data])

#             # Create the stacked bar chart
#             fig12 = px.bar(combined_data, x='animal_type', y='Count', color='gender', barmode='stack', text='Count')

#             # Update layout to set the title and axis labels
#             fig12.update_layout(title='Stacked Bar Chart of Dog and Cat Gender', xaxis_title='', yaxis_title='Count')
#             st.plotly_chart(fig12)
        
#         elif selected_tab == "Colour Analysis":
#             # Group the data by primary_colour and calculate the counts for cat_data
#             cat_colour_data = cat_data['colour'].value_counts().reset_index(name='Count')
#             cat_colour_data = cat_colour_data.sort_values(['Count'], ascending=False)
#             cat_colour_data = cat_colour_data.head(10)
#             cat_colour_data.rename(columns={'index': 'colour'}, inplace=True)
#             cat_colour_data['animal_type'] = 'cat'


#             # Group the data by primary_colour and calculate the counts for dog_data
#             dog_colour_data = dog_data['colour'].value_counts().reset_index(name='Count')
#             dog_colour_data.rename(columns={'index': 'colour'}, inplace=True)
#             dog_colour_data = dog_colour_data.sort_values(['Count'], ascending=False)
#             dog_colour_data = dog_colour_data.head(10)
#             dog_colour_data['animal_type'] = 'dog'

#             # Combine the data for both cat and dog
#             combined_data = pd.concat([cat_colour_data, dog_colour_data])

#             fig13 = px.bar(cat_colour_data, x='animal_type', y='Count', color='colour', text='Count',
#                         color_discrete_sequence=px.colors.diverging.Picnic)
#             fig13.update_layout(title='Stacked Bar Chart of Cat Colour', xaxis_title = "", yaxis_title='Count')

#             fig13.update_traces(textposition='inside')

#             fig14 = px.bar(dog_colour_data, x='animal_type', y='Count', color='colour', text='Count',
#                         color_discrete_sequence=px.colors.diverging.Picnic)

#             fig14.update_layout(title='Stacked Bar Chart of Dog Colour', xaxis_title = "", yaxis_title='Count')

#             fig14.update_traces(textposition='inside')

#             # Show the chart
#             st.plotly_chart(fig13)
#             st.plotly_chart(fig14)

#         time.sleep(1)


# call functions
main_function()


