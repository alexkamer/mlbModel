import streamlit as st
st.title('Stats Per Inning Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
from io import StringIO
import requests


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data


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



strikeouts_df = load_data('datasets/k_per_inning.csv')
hits_df = load_data('datasets/h_per_inning.csv')
batters_df = load_data('datasets/complex_batters.csv')
pitchers_df = load_data('datasets/complex_pitchers.csv')



url = 'http://192.168.1.200/data/daySlate.csv'


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
    daySlate = pd.read_csv(data_io)






#strikeouts_df_unique = strikeouts_df.drop_duplicates(subset='game_id', keep='first')
#strikeouts_df_unique = strikeouts_df.drop_duplicates(subset='game_id', keep='first')

expected_pitchers = daySlate['home_probable_pitcher'].to_list() + daySlate['away_probable_pitcher'].to_list()
expected_pitchers = [x for x in expected_pitchers if type(x) == str]

pitcher_name = st.selectbox(
    label="Select a pitcher",
    options=sorted(expected_pitchers)
)

stat_type = st.selectbox(
    label="Select a stat type:",
    options=['Strikeouts', 'Hits']
)

innings = st.multiselect(
    label="Select Which innings:",
    options=range(1,10)
)

pitcher_df = pitchers_df[(pitchers_df['Name'] == pitcher_name) & (pitchers_df['isStarter'])]

pitcher_df = pitcher_df.sort_values(by="date", ascending=False)



number_of_games = st.select_slider(
        'Select the number of games for the sample size',
        options=range(1,len(pitcher_df) + 1))

pitcher_df = pitcher_df.head(number_of_games)

game_id_df = pitcher_df[['game_id', 'date']]

if stat_type == 'Strikeouts':
    stat_df = strikeouts_df[(strikeouts_df['Name'] == pitcher_name) & (strikeouts_df['game_id'].isin(game_id_df['game_id'].to_list()))]
elif stat_type == 'Hits':
    stat_df = hits_df[(hits_df['Name'] == pitcher_name) & (hits_df['game_id'].isin(game_id_df['game_id'].to_list()))]

if innings != []:
    stat_df['Sum'] = sum([stat_df[str(inning)] for inning in innings])





stat_df = pd.merge(stat_df,game_id_df, on='game_id', how='right')
stat_df = stat_df.drop_duplicates(subset='date',keep='first')
stat_df = stat_df.round(1)


st.bar_chart(
    stat_df, x='date', y='Sum'
)

st.table(stat_df)
