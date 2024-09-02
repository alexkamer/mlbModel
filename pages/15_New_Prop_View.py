import streamlit as st
st.title('Prize Picks Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data


from datetime import datetime
import requests
import pandas as pd
import csv

from io import StringIO


url = 'http://192.168.1.200/data/data.csv'
url = 'http://192.168.1.200/data/all_prop_data.csv'


response = requests.get(url)
# Check if the request was successful
if response.status_code == 200:
    data = response.content.decode('utf-8')
else:
    print(f"Failed to retrieve data: status code {response.status_code}")
    data = None
if data:
    # Convert string data to StringIO object
    data_io = StringIO(data)
    # Create DataFrame
    df = pd.read_csv(data_io)


df = df.drop_duplicates(['prop_id'], keep='last')

prop_lines = df.copy()
prop_lines = prop_lines[prop_lines['league'] == 'MLB']
pitcher_df = load_data('datasets/complex_pitchers.csv')
batter_df = load_data('datasets/complex_batters.csv')
prop_lines = prop_lines.drop_duplicates()


def implied_probability_to_american_odds(implied_prob):
    try:
        if implied_prob < 0.5:
            return f"+{int((100 / implied_prob) - 100)}"
        elif implied_prob == 0:
            return 0
        else:
            return f"-{int((100 / implied_prob))}"
    except:
        return "Adjust game slider"

current_date = datetime.now().strftime('%Y-%m-%d')
single_day_props = prop_lines[pd.to_datetime(prop_lines['start_time']) == pd.to_datetime(current_date)]



display_df = single_day_props.copy()

col1,col2,col3 = st.columns(3)

with col1:
    team_name = st.selectbox(label='Select a team:', options=['Any'] + sorted(single_day_props['Team'].unique()))
    if team_name != 'Any':
        display_df = display_df[display_df['Team'] == team_name]
    

with col2:
    prop_type = st.selectbox(label='Select a prop type:', options=['Any'] + sorted(display_df['stat_type'].unique()))

    if prop_type != 'Any':
        display_df = display_df[display_df['stat_type'] == prop_type]

with col3:
    odds_type = st.selectbox(label='Select the odds type:', options=['Any'] + sorted(display_df['odds_type'].unique()))
    if odds_type != 'Any':
        display_df = display_df[display_df['odds_type'] == odds_type]



st.dataframe(display_df)