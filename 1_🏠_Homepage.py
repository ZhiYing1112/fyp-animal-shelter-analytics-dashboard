import streamlit as st
import pandas as pd
import os
from joblib import load
import data_import_preprocessing as dip

st.set_page_config(
    page_title="FYP: Animal Shelter Adoption Prediction App",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create a title for the app
st.title('Animal Shelter Adoption Prediction 🐶😺🏠')
# st.markdown('---')

# Create a subheader for the app - App Info and User Guide
st.subheader('About this app: 📝')
st.write('This app is created as part of the Final Year Project (FYP)')
st.write('Features of this app:')
st.markdown('---')

st.subheader('How to use this app? 🤔')
st.write('This app is divided into 4 pages. You can navigate to each page using the sidebar on the left.')
st.markdown('---')


# # Create a sidebar for the app
# st.sidebar.title('Menu')
# st.sidebar.info('Select a page below.')
# st.sidebar.markdown('---')

# Create a function to read uploaded file and check relevant variables
uploaded_data = dip.upload_file_and_check_variables()

if uploaded_data is not None:
    st.write('Preview of the uploaded dataset:')
    st.dataframe(uploaded_data)