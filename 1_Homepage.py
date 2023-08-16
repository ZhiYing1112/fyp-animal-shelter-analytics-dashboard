import streamlit as st

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
# st.subheader('About this app:')
st.write('''Welcome to the Animal Shelter Adoption Prediction App, 
         a powerful tool designed to assist animal shelter staff and administrators 
         in making informed decisions **"to improve animal adoption and streamline shelter operations"**. 
         Our app is built with the primary goal of finding loving forever homes for shelter animals, 
         ensuring they receive the care and attention they deserve.''')
st.info('Note: This app is currently open to the public for demonstration purposes only.')
# skip a line
st.write('')
st.write('')

st.subheader('App Features')
st.write('- **File Upload**: Upload your organization data to the app for analysis and prediction.')
st.write('- **Analytic Dashboard**: View and monitor the shelter performance and animal adoption trends.')
st.write('- **Adoption Prediction**: Predict cat and dog adoptions using pre-trained machine learning models for more accurate and efficient decision-making.')
st.write('')
st.write('')

# st.markdown('---')

st.subheader('User Guide')
st.write('''To use this app, simply navigate your way through the sidebar on the left. 
         By default, the analytics dashboard and animal adoption prediction will be shown with the sample dataset. 
         To use upload your own animal shelter dataset, please follow the steps below:''')
st.write('''
        1. Upload animal shelter dataset
            - Only accept .csv and .xlsx format.
            - The dataset columns need to be renamed and it must contain the relevant variables.
            - Once dataset is successfully uploaded, the data is automatically preprocessed and will be shown as an output table.
        
        2. Use the "Analytics Dashboard" page to visualize the data
            - Navigate to the page and view your shelter data in interactive plots. 
            - Now, you can gain insights from the plots and monitor shelter performance.
        
        3. View animal adoption prediction result
            - To view prediction results of animal adoption, navigate to "Animal Adoption Prediction" page.
            - This page shows all the factors influencing animal adoption and likelihood of adoption.
         
         ''')
st.write('')
# st.markdown('Head on to the sidebar to get started! 🐾')
st.markdown('<p style="color:#2FA4FF;font-size:20px;">Head on to the sidebar to get started! 🐾</p>', unsafe_allow_html=True)
st.markdown('---')
st.markdown('<p style = "font-size: 14px;">Created by 👩‍💻: YEE ZHI YING (TP055495), Data Analytics Final Year student at APU.</p>', unsafe_allow_html=True)
# create a link to my linkedin profile

st.markdown('<p style="font-size: 14px;"><a href="https://www.linkedin.com/in/zhi-ying-yee-13b586200/" target="_blank">🔗 LinkedIn</a></p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 14px;"><a href="https://github.com/ZhiYing1112" target="_blank">🔗 GitHub</a></p>', unsafe_allow_html=True)