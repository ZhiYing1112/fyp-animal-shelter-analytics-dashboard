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

        shelter_data = st.session_state.get('cleaned_data')

        total_num_intakes = st.session_state.get('total_num_intakes')
        total_num_adoptions = st.session_state.get('total_num_adoptions')
        save_rate = st.session_state.get('save_rate')
        live_release_rate = st.session_state.get('live_release_rate')
        

        dip.card_metrics(total_num_intakes, total_num_adoptions, save_rate, live_release_rate)
        dip.plot_graphs_cleaned_data(shelter_data)
        st.session_state['analytics_dashboard_shelter_data'] = shelter_data

    else:
        st.info('Note: The below shows the sample data for demonstration purposes only. Please upload your own dataset at "📝 Getting Started" Page.')
        st.write('')
        dip.card_metrics(37890, 30122, 0.9823, 0.9955)
        dip.plot_graphs_sample(pd.read_csv('austin_sample_data.csv'))


main_function()


