import streamlit as st
from joblib import load
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import LabelEncoder

st.set_page_config(
    page_title="Animal Adoption Prediction",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Animal Adoption Prediction 🤖')

def main_function():
    if st.session_state.get('cleaned_data') is not None:
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
        st.write(X_norm_data) 

        # load the model and make prediction
        model = load('best_model_os_xgb_clf.joblib')
        prediction = model.predict(X_norm_data)

        shelter_data['outcome_type'] = prediction
        st.write(shelter_data.head(5))



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




main_function()