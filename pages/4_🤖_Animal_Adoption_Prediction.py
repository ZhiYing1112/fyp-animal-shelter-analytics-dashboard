import streamlit as st
from joblib import load
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Animal Adoption Prediction",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Animal Adoption Prediction 🤖')