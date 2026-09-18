import pandas as pd
import numpy as np
import streamlit as st

def clean_data(df,feature,method):
    df1 = df.copy()
    if method == 'dropnulls_method':
        df1 = df1.dropna(subset=[feature])
    elif method == 'mean_method':
        df1[feature] = df1[feature].fillna(df1[feature].mean())
    elif method == 'median_method':
        df1[feature] = df1[feature].fillna(df1[feature].median())
    elif method == 'min_method':
        df1[feature] = df1[feature].fillna(df1[feature].min())
    elif method == 'max_method':
        df1[feature] = df1[feature].fillna(df1[feature].max())

    return df1

def Outliers(df,feature,methods1, submethods1, k):
    df2 = df.copy()
    if methods1 == 'Z-score':
        if submethods1 == 'Records Above +3σ and below -3σ':
            df2 = df2[((df2[feature] - df2[feature].mean()) / (df2[feature].std())).between(-3,3)]
        elif submethods1 == 'Records Above +2σ and below -2σ':
            df2 = df2[((df2[feature] - df2[feature].mean()) / (df2[feature].std())).between(-2, 2)]
        elif submethods1 == 'Records Above +1σ and below -1σ':
            df2 = df2[((df2[feature] - df2[feature].mean()) / (df2[feature].std())).between(-1, 1)]

    elif methods1 == 'IQR score':
        q1 = df2[feature].quantile(0.25)
        q3 = df2[feature].quantile(0.75)
        IQR = q3 - q1
        min_range = q1 - (k*IQR)
        max_range = q3 + (k*IQR)
        df2 = df2[df2[feature].between(min_range, max_range)]

    return df2

st.set_page_config(layout="wide")

st.title("DataLave")

if 'df' not in st.session_state:
    st.session_state.df = None

st.sidebar.subheader('Select Work to perform')
work = st.sidebar.radio('Select Work to perform', ["Main Menu", "1.Fill and Clean Nulls", "2.Outlier Management", "3.Encode & Scale"])

methods = ['dropnulls_method', 'mean_method', 'median_method', 'min_method', 'max_method']
methods1 = ['Z-score', 'IQR score']
submethods1 =['Records Above +3σ and below -3σ', 'Records Above +2σ and below -2σ', 'Records Above +1σ and below -1σ']

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

    st.caption('Current Dataset:')
    st.dataframe(st.session_state.df)
    st.caption(st.session_state.df.shape)

if work == '2.Outlier Management':

    if file and st.session_state.df is not None:
        feature = st.selectbox('Select your feature', st.session_state.df.columns)
        methods1= st.selectbox('Select your method', methods1)

        if 'show_prev' not in st.session_state:
            st.session_state.show_prev = False

        selected_submethod = None
        k = 1.5

        if methods1 == 'Z-score':
         selected_submethod = st.selectbox('Select your Z-score method: ', submethods1)

        elif methods1 == 'IQR score':
            k = st.slider('Select your IQR multiplier: ', 0.0, 5.0, step=0.01, format='%.2f')

        col1, col2, col3 = st.columns([1,1,2])

        with col1:
            if not st.session_state.show_prev:
                if st.button('Show Preview'):
                    st.session_state.show_prev = True
                    st.rerun()
            else:
                if st.button('Hide Preview'):
                   st.session_state.show_prev = False
                   st.rerun()

        preview_df = None

        if st.session_state.show_prev:
           preview_df = Outliers(st.session_state.df,feature,methods1,selected_submethod,k)

           orignal_rows = len(st.session_state.df)
           filtered_rows = len(preview_df)

           st.info(f'Keeping **{filtered_rows}** out of **{orignal_rows}**, hence removed **{orignal_rows - filtered_rows}** rows of Outliers')
           st.dataframe(preview_df)
           st.caption(preview_df.shape)
        else:
            st.caption('Current Dataset:')
            st.dataframe(st.session_state.df)
            st.caption(st.session_state.df.shape)

        with col2:
            if st.button('Apply Changes'):
                if preview_df is None:
                    preview_df = Outliers(st.session_state.df, feature, methods1, selected_submethod, k)
                else:
                    st.session_state.df = preview_df
                    st.session_state.show_prev = False
                    st.success('Your changes have been saved.')
                    st.rerun()


