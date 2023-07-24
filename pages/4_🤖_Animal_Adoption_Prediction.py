import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import data_functions as dip

st.set_page_config(
    page_title="Animal Adoption Prediction",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Animal Adoption Prediction 🤖')


def main_function():
    if st.session_state.get('cleaned_data') is not None:
           
        st.info('''
        Note:         
        This page shows all the factors influencing animal adoption and likelihood of adoption.
        Your uploaded data is predicted and the results are shown below. 😀

        ''')
        shelter_data = st.session_state.get('cleaned_data')

        adoption_prediction_data = dip.adoption_prediction(shelter_data)

        # Populate the dashboard with metrices and graphs
        total_num_intakes = st.session_state.get('total_num_intakes')
        total_num_adoptions = st.session_state.get('total_num_adoptions')
        save_rate = st.session_state.get('save_rate')
        live_release_rate = st.session_state.get('live_release_rate')

        dip.card_metrics(total_num_intakes, total_num_adoptions, save_rate, live_release_rate)
        dip.plot_filtered_data(adoption_prediction_data)

        # # export the data to csv
        # adoption_prediction_data.to_csv('adoption_prediction_data.csv', index=False)
    else:
        st.info('Note: Go to "Getting Started" page to upload your dataset and try it out HERE ✨')
        


main_function()