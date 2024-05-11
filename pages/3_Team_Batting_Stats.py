import streamlit as st
st.title('Team Hitting Analysis vs Starting Pitcher')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

df = pd.read_csv('datasets/complex_pitchers.csv')

team_list = sorted(df['Team'].unique())

team_name = st.selectbox(
    label='Select an Opposing Team:',
    options = team_list
)

if team_name:
    team_df = df[(df['Opponent'] == team_name) & (df['isStarter']) & (df['seasonNumber'] == 2024)]
    team_df = team_df.rename(columns={
        'isWinner' : 'Team Won Game',
        'pitcherIsWinner' : 'Pitcher Recorded Win',
        'ip' : 'Innings Pitched',
        'h' : 'Hits Allowed',
        'r' : 'Runs Allowed',
        'er' : 'Earned Runs',
        'bb' : 'Walks',
        'k' : 'Strikeouts',
        'hr' : 'Homeruns Allowed',
        'p' : 'Pitches Thrown',
        's' : 'Strikes Thrown',
        'pitching_outs' : 'Pitching Outs'
    })
    team_df = team_df.drop(['namefield','name', 'note', 'game_datetime', 'game_date', 'game_type','status','home_pitcher_note','away_pitcher_note','current_inning', 'inning_state', 'venue_id', 'venue_name', 'national_broadcasts', 'series_status','summary', 'losing_Team', 'doubleheader', 'game_num'], axis=1)

prop_type = st.selectbox(
    label='Select a Prop',
    options= sorted(['Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Walks', 'Strikeouts', 'Homeruns Allowed', 'Pitches Thrown', 'Pitching Outs', 'Team Won Game'])
)

minimum_pitches = st.select_slider(
    label='Select the minimum amount of pitches',
    options=range(0,111),
    value=0
)

minimum_outs_pitched = st.select_slider(
    label = 'Select the minimum amount of outs pitched',
    options=range(0,28),
    value = 0
)

#team_df = team_df[(team_df['Pitching Outs'] >= minimum_outs_pitched) & (team_df['Pitches Thrown'] >= minimum_pitches) & (team_df['Pitches Thrown'] <= (minimum_pitches + 20))]

team_df = team_df[(team_df['Pitches Thrown'] >= minimum_pitches)]


number_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,len(team_df) + 1))
team_df = team_df.tail(number_of_games)



st.bar_chart(
    team_df, x='date', y=[prop_type, 'Pitching Outs']
)
st.table(team_df)
