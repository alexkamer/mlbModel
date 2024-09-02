import streamlit as st

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

st.title('Injury Report')
@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

df = load_data('datasets/injuryReport.csv')

team_select = st.selectbox(
    options=sorted(list(df['Team'].unique())),
    label="Select A Team:"
)

team_df = df[df['Team'] == team_select]

st.dataframe(team_df[['Name', 'Position', 'status', 'injuryDate', 'shortComment']], hide_index = True)