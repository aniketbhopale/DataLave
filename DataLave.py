import pandas as pd
import numpy as np
import streamlit as st

def clean_data(df,feature,method):
    df1 = df.copy()
    if method == 'dropnulls_method':
        df1 = df1.dropna(subset=[feature])
    if method == 'mean_method':
        df1[feature] = df1[feature].fillna(df1[feature].mean())
    if method == 'median_method':
        df1[feature] = df1[feature].fillna(df1[feature].median())
    if method == 'min_method':
        df1[feature] = df1[feature].fillna(df1[feature].min())
    if method == 'max_method':
        df1[feature] = df1[feature].fillna(df1[feature].max())

    return df1

st.set_page_config(layout="wide")

st.title("Data Studio")

if 'df' not in st.session_state:
    st.session_state.df = None

st.sidebar.subheader('Select Work to perform')
work = st.sidebar.radio('Select Work to perform', ["Main Menu", "1.Fill and Clean Nulls", "2.Outlier Management", "3.Encode & Scale"])

methods = ['dropnulls_method', 'mean_method', 'median_method', 'min_method', 'max_method']

file = st.file_uploader('Upload your csv file', type='csv')

if file and st.session_state.df is None:
    st.session_state.df = pd.read_csv(file)

if work == '1.Fill and Clean Nulls':
    if file and st.session_state.df is None:
        st.session_state.df = pd.read_csv(file)

    if file:
        feature = st.selectbox('Select your feature', st.session_state.df.columns)
        method = st.selectbox('Select your method', methods)

        if st.button('Apply Changes'):
          st.session_state.df = clean_data(st.session_state.df,feature,method)
          st.success('Your changes have been saved.')

st.dataframe(st.session_state.df)


if work == '2.Outlier Management':
